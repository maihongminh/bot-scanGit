"""Repository endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..services.database_service import get_db
from ..services.github_service import GitHubService
from ..models.repository import Repository
from ..schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryUpdate
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    scan_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all repositories"""
    query = db.query(Repository)
    
    if scan_status:
        query = query.filter(Repository.scan_status == scan_status)
    
    total = query.count()
    repos = query.offset(skip).limit(limit).all()
    
    return repos

@router.post("/", response_model=RepositoryResponse)
async def create_repository(
    repo: RepositoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new repository"""
    try:
        # Check if repository already exists
        existing = db.query(Repository).filter(
            Repository.name == repo.name
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Repository already exists")
        
        # Create new repository
        db_repo = Repository(**repo.dict())
        db.add(db_repo)
        db.commit()
        db.refresh(db_repo)
        
        logger.info(f"Created repository: {repo.name}")
        return db_repo
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    """Get repository details"""
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return repo

@router.put("/{repository_id}", response_model=RepositoryResponse)
async def update_repository(
    repository_id: int,
    repo_update: RepositoryUpdate,
    db: Session = Depends(get_db)
):
    """Update repository"""
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    try:
        update_data = repo_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(repo, field, value)
        
        db.commit()
        db.refresh(repo)
        
        logger.info(f"Updated repository: {repo.name}")
        return repo
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    """Delete repository and all related data"""
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    try:
        # Delete related data first (cascade will handle this, but explicit is better)
        db.delete(repo)
        db.commit()
        
        logger.info(f"Deleted repository: {repo.name}")
        return {"message": f"Repository '{repo.name}' deleted successfully", "repository_id": repository_id}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{repo_name}/from-github", response_model=RepositoryResponse)
async def add_repository_from_github(
    repo_name: str,
    db: Session = Depends(get_db)
):
    """Add a repository from GitHub"""
    try:
        gh_service = GitHubService()
        
        # Get repository info from GitHub
        repo_info = gh_service.get_repository(repo_name)
        
        if not repo_info:
            raise HTTPException(status_code=404, detail="Repository not found on GitHub")
        
        # Save to database
        db_repo = gh_service.save_repository(repo_info, db)
        
        if not db_repo:
            raise HTTPException(status_code=500, detail="Failed to save repository")
        
        logger.info(f"Added repository from GitHub: {repo_name}")
        return db_repo
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding repository from GitHub: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{repository_id}/stats")
async def get_repository_stats(
    repository_id: int,
    db: Session = Depends(get_db)
):
    """Get repository statistics"""
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    from ..models.detection import Detection
    
    detections = db.query(Detection).filter(
        Detection.repository_id == repository_id,
        Detection.is_false_positive == False
    ).all()
    
    secret_types = {}
    for detection in detections:
        secret_types[detection.secret_type] = secret_types.get(detection.secret_type, 0) + 1
    
    return {
        "repository_id": repository_id,
        "repository_name": repo.name,
        "total_secrets": len(detections),
        "secret_types": secret_types,
        "average_confidence": sum(d.confidence_score for d in detections) / len(detections) if detections else 0
    }
