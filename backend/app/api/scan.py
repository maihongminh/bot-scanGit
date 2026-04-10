"""Scanning endpoints"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from ..services.database_service import get_db
from ..services.github_service import GitHubService
from ..workers.scan_tasks import scan_repository, scan_trending_repositories, perform_repository_scan
from ..models.repository import Repository
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/repository/{repository_id}")
async def start_scan(
    repository_id: int,
    max_commits: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Start scanning a repository"""
    try:
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        if repo.scan_status == "scanning":
            raise HTTPException(status_code=400, detail="Repository is already being scanned")
        
        # Run scan synchronously
        try:
            result = perform_repository_scan(repository_id, max_commits=max_commits)
            logger.info(f"Scan result: {result}")
            logger.info(f"Scan completed for repository {repo.name}")
            
            # Ensure result is valid
            if result is None:
                logger.warning("Result is None, returning default")
                result = {"status": "completed", "repository_id": repository_id, "repository_name": repo.name}
            
            logger.info(f"Returning result: {result}")
            return result
        except Exception as e:
            import traceback
            logger.error(f"Scan error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "repository_id": repository_id,
                "repository_name": repo.name,
                "message": str(e)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trending")
def scan_trending(
    language: str = "",
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Scan trending repositories in background"""
    try:
        import threading
        from ..services.database_service import DatabaseService
        
        limit = limit or 10  # Default to 10 trending repos
        
        # Start background thread to scan trending repos
        def scan_trending_bg():
            db = DatabaseService.get_session()
            try:
                logger.info(f"Starting background scan for trending repositories (language={language}, limit={limit})")
                
                # Get trending repos
                gh_service = GitHubService()
                repos_info = gh_service.get_trending_repos(language=language, limit=limit)
                
                if not repos_info:
                    logger.warning("No trending repositories found")
                    return
                
                scanned_count = 0
                for repo_info in repos_info:
                    try:
                        # Check if already exists
                        existing = db.query(Repository).filter(Repository.name == repo_info['name']).first()
                        if existing:
                            logger.info(f"Repository {repo_info['name']} already exists")
                            continue
                        
                        # Save repo
                        repo = gh_service.save_repository(repo_info, db)
                        if not repo:
                            continue
                        
                        # Scan it
                        result = perform_repository_scan(repo.id, max_commits=10)
                        scanned_count += 1
                        logger.info(f"Scanned {repo_info['name']}: {result.get('secrets_found', 0)} secrets found")
                        
                    except Exception as e:
                        logger.error(f"Error processing trending repo {repo_info.get('name')}: {str(e)}")
                        continue
                
                logger.info(f"Trending scan completed: {scanned_count} repositories scanned")
                
            except Exception as e:
                logger.error(f"Error in background trending scan: {str(e)}")
            finally:
                DatabaseService.close_session(db)
        
        # Start background thread (daemon so it won't block shutdown)
        thread = threading.Thread(target=scan_trending_bg, daemon=True)
        thread.start()
        
        return {
            "status": "started",
            "message": f"Scanning trending repositories in background (limit={limit})",
            "language": language
        }
    
    except Exception as e:
        logger.error(f"Error starting trending scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repository/{repository_id}/status")
async def get_scan_status(
    repository_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get scan status for a repository"""
    try:
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        return {
            "repository_id": repository_id,
            "repository_name": repo.name,
            "scan_status": repo.scan_status,
            "last_scanned_at": repo.last_scanned_at.isoformat() if repo.last_scanned_at else None,
            "next_scan_at": repo.next_scan_at.isoformat() if repo.next_scan_at else None,
            "total_commits": repo.total_commits,
            "secrets_found": repo.secrets_found
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scan status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/task/{task_id}/status")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a scan task"""
    try:
        from celery_app import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.status == "SUCCESS" else None,
            "error": str(task.info) if task.status == "FAILURE" else None
        }
    
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/repository-from-github")
def scan_repository_from_github(
    repo_name: str = Query(...)
) -> Dict[str, Any]:
    """Add a repository from GitHub and start scanning"""
    try:
        from ..services.database_service import DatabaseService
        
        # Fetch repository from GitHub
        gh_service = GitHubService()
        repo_info = gh_service.get_repository(repo_name)
        
        if not repo_info:
            raise HTTPException(status_code=400, detail="Repository not found. Please use format: owner/repo_name (e.g., maihongminh/SFU_Server)")
        
        # Get database session
        db = DatabaseService.get_session()
        try:
            # Check if repository already exists
            existing = db.query(Repository).filter(Repository.name == repo_info['name']).first()
            
            if existing:
                logger.info(f"Repository {repo_name} already exists, repository_id={existing.id}")
                return {
                    "status": "already_exists",
                    "repository_id": existing.id,
                    "repository_name": repo_info['name'],
                    "message": "Repository already exists in database"
                }
            
            # Save repository
            repo = gh_service.save_repository(repo_info, db)
            
            if not repo:
                raise HTTPException(status_code=500, detail="Failed to save repository")
            
            logger.info(f"Added repository {repo_info['name']} to database, starting scan...")
            
            # Start scan synchronously
            result = perform_repository_scan(repo.id)
            
            logger.info(f"Scan completed for {repo_info['name']}")
            
            return {
                "status": "completed",
                "repository_id": repo.id,
                "repository_name": repo_info['name'],
                "message": "Repository added and scan completed",
                "scan_result": result
            }
        finally:
            DatabaseService.close_session(db)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning repository from GitHub: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def start_batch_scan(
    repository_ids: list[int],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Start scanning multiple repositories"""
    try:
        task_ids = []
        failed_repos = []
        
        for repo_id in repository_ids:
            try:
                repo = db.query(Repository).filter(Repository.id == repo_id).first()
                
                if not repo:
                    failed_repos.append(repo_id)
                    continue
                
                if repo.scan_status == "scanning":
                    failed_repos.append(repo_id)
                    continue
                
                # Queue scan
                task = scan_repository.delay(repo_id)
                task_ids.append({
                    "repository_id": repo_id,
                    "repository_name": repo.name,
                    "task_id": task.id
                })
                
            except Exception as e:
                logger.error(f"Error queuing scan for repository {repo_id}: {str(e)}")
                failed_repos.append(repo_id)
                continue
        
        logger.info(f"Queued batch scan for {len(task_ids)} repositories")
        
        return {
            "status": "queued",
            "total_queued": len(task_ids),
            "total_failed": len(failed_repos),
            "tasks": task_ids,
            "failed_repository_ids": failed_repos
        }
    
    except Exception as e:
        logger.error(f"Error starting batch scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rate-limit")
async def get_github_rate_limit() -> Dict[str, Any]:
    """Get GitHub API rate limit information"""
    try:
        gh_service = GitHubService()
        rate_limit_info = gh_service.get_rate_limit_info()
        
        return {
            "github_rate_limit": rate_limit_info
        }
    
    except Exception as e:
        logger.error(f"Error getting rate limit info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
