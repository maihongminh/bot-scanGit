"""Service for interacting with GitHub API"""
import logging
from typing import List, Optional, Dict, Any
from github import Github, GithubException, Repository
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..config import settings
from ..models.repository import Repository as RepositoryModel
from ..models.commit import Commit
from ..schemas.repository import RepositoryCreate
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GitHubService:
    """Service for GitHub API operations"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub service
        
        Args:
            token: GitHub API token (uses settings.GITHUB_TOKEN if not provided)
        """
        self.token = token or settings.GITHUB_TOKEN
        if not self.token:
            logger.warning("GitHub token not provided - API access will be limited")
            self.github = Github()
        else:
            self.github = Github(self.token)
        self.logger = logger
    
    def get_trending_repos(self, language: str = "", 
                          stars_min: int = 100,
                          limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get trending repositories from GitHub
        
        Args:
            language: Programming language filter (empty for all languages)
            stars_min: Minimum number of stars
            limit: Maximum number of repos to return
            
        Returns:
            List of repository information dictionaries
        """
        try:
            query = f"stars:>{stars_min}"
            if language:
                query += f" language:{language}"
            
            # Sort by stars, descending
            query += " sort:stars"
            
            repos = self.github.search_repositories(query=query, per_page=limit)
            
            result = []
            for repo in repos[:limit]:
                try:
                    result.append({
                        "name": repo.full_name,
                        "url": repo.html_url,
                        "description": repo.description,
                        "owner": repo.owner.login,
                        "stars_count": repo.stargazers_count,
                        "forks_count": repo.forks_count,
                        "language": repo.language,
                        "is_public": not repo.private
                    })
                except Exception as e:
                    self.logger.warning(f"Error processing repo {repo.full_name}: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(result)} trending repositories")
            return result
        
        except GithubException as e:
            self.logger.error(f"GitHub API error: {str(e)}")
            return []
    
    def get_repository(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific repository information
        
        Args:
            repo_name: Repository name in format "owner/repo"
            
        Returns:
            Repository information dictionary or None
        """
        try:
            # Require format "owner/repo"
            if "/" not in repo_name:
                self.logger.error(f"Invalid repo format: {repo_name}. Use format: owner/repo")
                return None
            
            repo = self.github.get_repo(repo_name)
            
            return {
                "name": repo.full_name,
                "url": repo.html_url,
                "description": repo.description,
                "owner": repo.owner.login,
                "stars_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "language": repo.language,
                "is_public": not repo.private
            }
        except GithubException as e:
            self.logger.error(f"Error fetching repository {repo_name}: {str(e)}")
            return None
    
    def get_commits(self, repo_name: str, max_commits: int = 100,
                   since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get commits from a repository
        
        Args:
            repo_name: Repository name in format "owner/repo"
            max_commits: Maximum number of commits to return
            since: Get commits after this date
            
        Returns:
            List of commit information dictionaries
        """
        try:
            repo = self.github.get_repo(repo_name)
            # Only pass since if it's not None
            if since:
                commits = repo.get_commits(since=since)
            else:
                commits = repo.get_commits()
            
            result = []
            for i, commit in enumerate(commits):
                if i >= max_commits:
                    break
                
                try:
                    result.append({
                        "commit_hash": commit.sha,
                        "author_name": commit.commit.author.name if commit.commit.author else "Unknown",
                        "author_email": commit.commit.author.email if commit.commit.author else "",
                        "message": commit.commit.message,
                        "commit_url": commit.html_url
                    })
                except Exception as e:
                    self.logger.warning(f"Error processing commit {commit.sha}: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(result)} commits in {repo_name}")
            return result
        
        except GithubException as e:
            self.logger.error(f"Error fetching commits from {repo_name}: {str(e)}")
            return []
    
    def get_file_content(self, repo_name: str, file_path: str, 
                        ref: str = "main") -> Optional[str]:
        """
        Get content of a specific file
        
        Args:
            repo_name: Repository name in format "owner/repo"
            file_path: Path to the file
            ref: Git reference (branch, tag, or commit)
            
        Returns:
            File content or None
        """
        try:
            repo = self.github.get_repo(repo_name)
            
            # Try the specified ref first
            try:
                content = repo.get_contents(file_path, ref=ref)
            except GithubException:
                # Fall back to main/master
                try:
                    content = repo.get_contents(file_path, ref="main")
                except GithubException:
                    content = repo.get_contents(file_path, ref="master")
            
            if content.size > 1024 * 1024:  # Skip files larger than 1MB
                self.logger.warning(f"File {file_path} is too large, skipping")
                return None
            
            return content.decoded_content.decode('utf-8', errors='ignore')
        
        except GithubException as e:
            self.logger.debug(f"Error fetching file {repo_name}/{file_path}: {str(e)}")
            return None
    
    def get_changed_files(self, repo_name: str, commit_sha: str) -> List[str]:
        """
        Get list of files changed in a commit
        
        Args:
            repo_name: Repository name in format "owner/repo"
            commit_sha: Commit SHA
            
        Returns:
            List of file paths
        """
        try:
            repo = self.github.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            return [file.filename for file in commit.files]
        
        except GithubException as e:
            self.logger.error(f"Error fetching changed files for {commit_sha}: {str(e)}")
            return []
    
    def save_repository(self, repo_info: Dict[str, Any], db: Session) -> Optional[RepositoryModel]:
        """
        Save repository to database
        
        Args:
            repo_info: Repository information dictionary
            db: Database session
            
        Returns:
            Repository model instance or None
        """
        try:
            # Check if repository already exists
            existing = db.query(RepositoryModel).filter(
                RepositoryModel.name == repo_info['name']
            ).first()
            
            if existing:
                # Update existing repository
                existing.stars_count = repo_info.get('stars_count', 0)
                existing.forks_count = repo_info.get('forks_count', 0)
                existing.updated_at = datetime.utcnow()
                db.commit()
                return existing
            
            # Create new repository
            repo_obj = RepositoryModel(
                name=repo_info['name'],
                url=repo_info['url'],
                description=repo_info.get('description'),
                owner=repo_info.get('owner'),
                stars_count=repo_info.get('stars_count', 0),
                forks_count=repo_info.get('forks_count', 0),
                language=repo_info.get('language'),
                is_public=repo_info.get('is_public', True),
                scan_status='pending'
            )
            
            db.add(repo_obj)
            db.commit()
            db.refresh(repo_obj)
            
            self.logger.info(f"Saved repository {repo_info['name']} to database")
            return repo_obj
        
        except Exception as e:
            self.logger.error(f"Error saving repository: {str(e)}")
            db.rollback()
            return None
    
    def is_rate_limited(self) -> bool:
        """Check if GitHub API rate limit is exceeded"""
        try:
            rate_limit = self.github.get_rate_limit()
            remaining = rate_limit.core.remaining
            
            if remaining < 100:
                reset_time = datetime.fromtimestamp(rate_limit.core.reset)
                self.logger.warning(
                    f"GitHub API rate limit low: {remaining} remaining. "
                    f"Reset at {reset_time}"
                )
                return remaining == 0
            
            return False
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {str(e)}")
            return False
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        try:
            rate_limit = self.github.get_rate_limit()
            
            return {
                "limit": rate_limit.core.limit,
                "remaining": rate_limit.core.remaining,
                "reset": datetime.fromtimestamp(rate_limit.core.reset).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting rate limit info: {str(e)}")
            return {}
