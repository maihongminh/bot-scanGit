"""Celery tasks for repository scanning"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from celery import shared_task, group
from celery.exceptions import SoftTimeLimitExceeded

from ..config import settings
from ..services.github_service import GitHubService
from ..services.detection_service import DetectionService
from ..services.database_service import DatabaseService
from ..models.repository import Repository
from ..models.commit import Commit
from ..models.scan_history import ScanHistory
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ScanException(Exception):
    """Custom exception for scan-related errors"""
    pass

def perform_repository_scan(repository_id: int, max_commits: int = None) -> dict:
    """
    Core scan logic (can be called synchronously or from Celery task)
    
    Args:
        repository_id: ID of the repository to scan
        max_commits: Maximum commits to scan (uses config if None)
        
    Returns:
        Dict with scan results
    """
    max_commits = max_commits or 10  # Default to 10 commits for faster testing
    db = None
    
    try:
        db = DatabaseService.get_session()
        
        # Get repository
        repo = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repo:
            logger.error(f"Repository with ID {repository_id} not found")
            return {"status": "error", "message": "Repository not found"}
        
        # Update repository status
        repo.scan_status = "scanning"
        db.commit()
        
        # Create scan history record
        scan_history = ScanHistory(
            repository_id=repository_id,
            scan_type="full",
            scan_status="running"
        )
        db.add(scan_history)
        db.commit()
        
        logger.info(f"Starting scan for repository: {repo.name}")
        
        # Initialize services
        gh_service = GitHubService()
        detection_service = DetectionService()
        
        # Get commits from GitHub
        # If last_scanned_at exists, only scan new commits since then
        commits_since = None
        if repo.last_scanned_at:
            commits_since = repo.last_scanned_at
            logger.info(f"Scanning commits since {commits_since} for {repo.name}")
        
        commits_info = gh_service.get_commits(
            repo.name, 
            max_commits=max_commits,
            since=commits_since
        )
        
        if not commits_info:
            logger.warning(f"No commits found for repository {repo.name}")
            repo.scan_status = "completed"
            scan_history.scan_status = "completed"
            scan_history.completed_at = datetime.utcnow()
            db.commit()
            return {"status": "completed", "commits_scanned": 0, "secrets_found": 0}
        
        # Save commits and scan them
        total_secrets = 0
        errors = 0
        
        for commit_info in commits_info:
            try:
                # Check if commit already exists
                existing_commit = db.query(Commit).filter(
                    Commit.repository_id == repository_id,
                    Commit.commit_hash == commit_info['commit_hash']
                ).first()
                
                if existing_commit and existing_commit.scan_status == "completed":
                    logger.debug(f"Commit {commit_info['commit_hash'][:8]} already scanned")
                    continue
                
                # Create or update commit
                if existing_commit:
                    commit = existing_commit
                else:
                    commit = Commit(
                        repository_id=repository_id,
                        commit_hash=commit_info['commit_hash'],
                        author_name=commit_info.get('author_name'),
                        author_email=commit_info.get('author_email'),
                        message=commit_info.get('message'),
                        commit_url=commit_info.get('commit_url')
                    )
                    db.add(commit)
                    db.commit()
                    db.refresh(commit)
                
                # Get changed files
                changed_files = gh_service.get_changed_files(
                    repo.name,
                    commit_info['commit_hash']
                )
                
                # Scan files
                for file_path in changed_files:
                    # Skip binary files and common non-code files
                    if should_skip_file(file_path):
                        continue
                    
                    try:
                        content = gh_service.get_file_content(
                            repo.name,
                            file_path,
                            ref=commit_info['commit_hash']
                        )
                        
                        if content:
                            detections = detection_service.scan_content(
                                content,
                                file_path,
                                commit.id,
                                repository_id,
                                db
                            )
                            
                            if detections:
                                total_secrets += len(detections)
                                commit.has_secrets = True
                                db.commit()
                                
                                logger.info(
                                    f"Found {len(detections)} secrets in "
                                    f"{repo.name}/{file_path}"
                                )
                    except Exception as e:
                        logger.error(f"Error scanning file {file_path}: {str(e)}")
                        errors += 1
                        continue
                
                # Mark commit as scanned
                commit.scan_status = "completed"
                commit.scanned_at = datetime.utcnow()
                db.commit()
                
            except SoftTimeLimitExceeded:
                logger.warning(f"Soft time limit exceeded for repository {repo.name}")
                commit.scan_status = "error"
                db.commit()
                raise
            except Exception as e:
                logger.error(f"Error processing commit {commit_info['commit_hash']}: {str(e)}")
                errors += 1
                commit.scan_status = "error"
                db.commit()
                continue
        
        # Update repository and scan history
        repo.scan_status = "completed"
        repo.last_scanned_at = datetime.utcnow()
        repo.next_scan_at = repo.last_scanned_at + timedelta(hours=24)
        repo.total_commits = len(commits_info)
        repo.secrets_found = total_secrets
        
        scan_history.scan_status = "completed"
        scan_history.completed_at = datetime.utcnow()
        scan_history.total_commits_scanned = len(commits_info)
        scan_history.total_secrets_found = total_secrets
        scan_history.errors_count = errors
        scan_history.execution_time_seconds = int(
            (scan_history.completed_at - scan_history.started_at).total_seconds()
        )
        
        db.commit()
        
        logger.info(
            f"Scan completed for {repo.name}: {len(commits_info)} commits, "
            f"{total_secrets} secrets found, {errors} errors"
        )
        
        return {
            "status": "completed",
            "commits_scanned": len(commits_info),
            "secrets_found": total_secrets,
            "errors": errors
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout for repository {repository_id}")
        if db:
            repo = db.query(Repository).filter(Repository.id == repository_id).first()
            if repo:
                repo.scan_status = "error"
            db.commit()
        return {"status": "error", "message": "Task timeout"}
    except Exception as e:
        import traceback
        error_msg = str(e) if str(e) else repr(e)
        logger.error(f"Error scanning repository {repository_id}: {error_msg}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if db:
            repo = db.query(Repository).filter(Repository.id == repository_id).first()
            if repo:
                repo.scan_status = "error"
            db.commit()
        return {"status": "error", "message": error_msg or "Unknown error"}
    finally:
        if db:
            DatabaseService.close_session(db)

@shared_task(bind=True, max_retries=3)
def scan_repository(self, repository_id: int, max_commits: int = None):
    """
    Celery task wrapper for scanning repository
    """
    try:
        return perform_repository_scan(repository_id, max_commits)
    except SoftTimeLimitExceeded:
        logger.warning(f"Soft time limit exceeded for repository {repository_id}")
        raise self.retry(exc=ScanException("Task timeout"), countdown=60)
    except Exception as e:
        logger.error(f"Error in scan task: {str(e)}")
        raise self.retry(exc=e, countdown=60)

@shared_task
def scan_trending_repositories(language: str = "", limit: int = None):
    """
    Scan trending repositories from GitHub
    
    Args:
        language: Programming language to scan
        limit: Number of repositories to scan
    """
    limit = limit or settings.TRENDING_REPO_COUNT
    db = None
    
    try:
        db = DatabaseService.get_session()
        
        logger.info(f"Starting scan of trending repositories (language={language})")
        
        # Get trending repos
        gh_service = GitHubService()
        repos_info = gh_service.get_trending_repos(language=language, limit=limit)
        
        if not repos_info:
            logger.warning("No trending repositories found")
            return {"status": "no_repos"}
        
        # Save repositories to database
        task_ids = []
        for repo_info in repos_info:
            try:
                repo = gh_service.save_repository(repo_info, db)
                if repo:
                    # Queue scan task
                    task = scan_repository.delay(repo.id)
                    task_ids.append(task.id)
                    logger.info(f"Queued scan for {repo.name}")
            except Exception as e:
                logger.error(f"Error processing repo {repo_info.get('name')}: {str(e)}")
                continue
        
        logger.info(f"Queued {len(task_ids)} repositories for scanning")
        
        return {
            "status": "queued",
            "repositories": len(repos_info),
            "tasks": task_ids
        }
        
    except Exception as e:
        logger.error(f"Error scanning trending repositories: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        if db:
            DatabaseService.close_session(db)

@shared_task
def cleanup_old_scans(days: int = 90):
    """
    Clean up old scan records
    
    Args:
        days: Delete records older than this many days
    """
    db = None
    
    try:
        db = DatabaseService.get_session()
        DatabaseService.cleanup_old_records(db, days=days)
        return {"status": "completed"}
    except Exception as e:
        logger.error(f"Error cleaning up old scans: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        if db:
            DatabaseService.close_session(db)

def should_skip_file(file_path: str) -> bool:
    """
    Check if a file should be skipped during scanning
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file should be skipped
    """
    # Binary file extensions
    binary_extensions = {
        '.pyc', '.pyo', '.pyd', '.so', '.o', '.obj',
        '.exe', '.dll', '.lib', '.a',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        '.mp3', '.mp4', '.mov', '.avi'
    }
    
    # Directories to skip
    skip_dirs = {
        '.git', '.svn', '.hg', 'node_modules', '__pycache__',
        'venv', '.venv', 'env', '.env',
        'build', 'dist', '.tox', '.eggs'
    }
    
    # Check extension
    for ext in binary_extensions:
        if file_path.lower().endswith(ext):
            return True
    
    # Check directory
    for dir_name in skip_dirs:
        if f'/{dir_name}/' in file_path or file_path.startswith(dir_name + '/'):
            return True
    
    return False
