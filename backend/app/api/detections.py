"""Detection endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..services.database_service import get_db
from ..services.detection_service import DetectionService
from ..models.detection import Detection
from ..models.false_positive import FalsePositive
from ..schemas.detection import DetectionResponse, DetectionUpdate
from ..schemas.false_positive import FalsePositiveCreate, FalsePositiveResponse
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=List[DetectionResponse])
async def list_detections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repository_id: Optional[int] = None,
    secret_type: Optional[str] = None,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    exclude_false_positives: bool = True,
    db: Session = Depends(get_db)
):
    """List detections with optional filtering"""
    query = db.query(Detection)
    
    if repository_id:
        query = query.filter(Detection.repository_id == repository_id)
    
    if secret_type:
        query = query.filter(Detection.secret_type == secret_type)
    
    if exclude_false_positives:
        query = query.filter(Detection.is_false_positive == False)
    
    if min_confidence > 0:
        query = query.filter(Detection.confidence_score >= min_confidence)
    
    detections = query.offset(skip).limit(limit).all()
    return detections

@router.get("/{detection_id}", response_model=DetectionResponse)
async def get_detection(
    detection_id: int,
    db: Session = Depends(get_db)
):
    """Get detection details"""
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    return detection

@router.put("/{detection_id}", response_model=DetectionResponse)
async def update_detection(
    detection_id: int,
    detection_update: DetectionUpdate,
    db: Session = Depends(get_db)
):
    """Update detection status"""
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    try:
        update_data = detection_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(detection, field, value)
        
        db.commit()
        db.refresh(detection)
        
        logger.info(f"Updated detection {detection_id}")
        return detection
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{detection_id}", response_model=DetectionResponse)
async def patch_detection(
    detection_id: int,
    detection_update: DetectionUpdate,
    db: Session = Depends(get_db)
):
    """Patch detection status (partial update)"""
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    try:
        update_data = detection_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(detection, field, value)
        
        db.commit()
        db.refresh(detection)
        
        logger.info(f"Patched detection {detection_id}")
        return detection
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error patching detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repository/{repository_id}", response_model=List[DetectionResponse])
async def get_repository_detections(
    repository_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all detections for a repository"""
    detection_service = DetectionService()
    detections = detection_service.get_detections_by_repository(
        repository_id, db, skip=skip, limit=limit
    )
    
    if not detections and db.query(Detection).filter(
        Detection.repository_id == repository_id
    ).count() == 0:
        raise HTTPException(status_code=404, detail="No detections found for this repository")
    
    return detections

@router.get("/high-confidence", response_model=List[DetectionResponse])
async def get_high_confidence_detections(
    min_confidence: float = Query(0.8, ge=0.0, le=1.0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get high-confidence detections"""
    detection_service = DetectionService()
    detections = detection_service.get_high_confidence_detections(
        db, min_confidence=min_confidence, skip=skip, limit=limit
    )
    
    return detections

@router.post("/{detection_id}/false-positive", response_model=FalsePositiveResponse)
async def mark_as_false_positive(
    detection_id: int,
    false_positive_data: FalsePositiveCreate,
    db: Session = Depends(get_db)
):
    """Mark a detection as false positive"""
    try:
        detection = db.query(Detection).filter(Detection.id == detection_id).first()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        # Update detection
        detection.is_false_positive = True
        
        # Create false positive record
        false_positive = FalsePositive(
            detection_id=detection_id,
            reason_code=false_positive_data.reason_code,
            reason_description=false_positive_data.reason_description,
            marked_by=false_positive_data.marked_by
        )
        
        db.add(false_positive)
        db.commit()
        db.refresh(false_positive)
        
        logger.info(f"Marked detection {detection_id} as false positive")
        return false_positive
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking false positive: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{detection_id}/false-positive")
async def remove_false_positive_marking(
    detection_id: int,
    db: Session = Depends(get_db)
):
    """Remove false positive marking"""
    try:
        detection = db.query(Detection).filter(Detection.id == detection_id).first()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        # Update detection
        detection.is_false_positive = False
        
        # Delete false positive records
        db.query(FalsePositive).filter(FalsePositive.detection_id == detection_id).delete()
        
        db.commit()
        
        logger.info(f"Removed false positive marking from detection {detection_id}")
        return {"message": "False positive marking removed"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing false positive marking: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-type/{secret_type}", response_model=List[DetectionResponse])
async def get_detections_by_type(
    secret_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get detections by secret type"""
    detection_service = DetectionService()
    detections = detection_service.get_detections_by_type(
        secret_type, db, skip=skip, limit=limit
    )
    
    if not detections:
        raise HTTPException(status_code=404, detail=f"No detections found for type {secret_type}")
    
    return detections

@router.get("/stats/by-type")
async def get_detections_statistics(
    db: Session = Depends(get_db)
):
    """Get detection statistics by type"""
    detection_service = DetectionService()
    stats = detection_service.get_statistics(db)
    
    return stats
