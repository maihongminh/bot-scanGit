"""Service for detecting secrets in code"""
import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from ..utils.patterns import PatternMatcher
from ..models.detection import Detection
from ..models.commit import Commit
from ..schemas.detection import DetectionCreate

logger = logging.getLogger(__name__)

class DetectionService:
    """Service for scanning and detecting secrets in code"""
    
    def __init__(self):
        self.matcher = PatternMatcher()
        self.logger = logger
    
    def scan_content(self, content: str, file_path: str, commit_id: int, 
                    repository_id: int, db: Session) -> List[Detection]:
        """
        Scan content for secrets and save detections to database
        
        Args:
            content: File content to scan
            file_path: Path of the file
            commit_id: ID of the commit
            repository_id: ID of the repository
            db: Database session
            
        Returns:
            List of Detection objects created
        """
        detections = []
        secrets = self.matcher.find_secrets(content)
        
        for secret_type, matched_value, confidence, line_num, pattern_name in secrets:
            try:
                detection_data = DetectionCreate(
                    commit_id=commit_id,
                    repository_id=repository_id,
                    file_path=file_path,
                    secret_type=secret_type,
                    secret_pattern=pattern_name,
                    matched_value=self._mask_secret(matched_value),
                    line_number=line_num,
                    confidence_score=confidence
                )
                
                detection = Detection(**detection_data.dict())
                db.add(detection)
                detections.append(detection)
                
                self.logger.info(
                    f"Detected {secret_type} in {file_path}:{line_num} "
                    f"with confidence {confidence:.2f}"
                )
            except Exception as e:
                self.logger.error(f"Error creating detection: {str(e)}")
                continue
        
        db.commit()
        return detections
    
    @staticmethod
    def _mask_secret(value: str, show_first: int = 4, show_last: int = 4) -> str:
        """
        Mask sensitive part of secret value
        
        Args:
            value: The secret value to mask
            show_first: Number of characters to show at the beginning
            show_last: Number of characters to show at the end
            
        Returns:
            Masked secret value
        """
        if len(value) <= show_first + show_last:
            return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}" if len(value) > 2 else value
        
        return f"{value[:show_first]}{'*' * (len(value) - show_first - show_last)}{value[-show_last:]}"
    
    def get_detections_by_repository(self, repository_id: int, db: Session,
                                     skip: int = 0, limit: int = 100,
                                     exclude_false_positives: bool = True) -> List[Detection]:
        """Get detections for a specific repository"""
        query = db.query(Detection).filter(Detection.repository_id == repository_id)
        
        if exclude_false_positives:
            query = query.filter(Detection.is_false_positive == False)
        
        return query.offset(skip).limit(limit).all()
    
    def get_detections_by_commit(self, commit_id: int, db: Session,
                                exclude_false_positives: bool = True) -> List[Detection]:
        """Get detections for a specific commit"""
        query = db.query(Detection).filter(Detection.commit_id == commit_id)
        
        if exclude_false_positives:
            query = query.filter(Detection.is_false_positive == False)
        
        return query.all()
    
    def get_high_confidence_detections(self, db: Session, 
                                      min_confidence: float = 0.8,
                                      skip: int = 0, limit: int = 100) -> List[Detection]:
        """Get detections with high confidence scores"""
        return db.query(Detection).filter(
            Detection.confidence_score >= min_confidence,
            Detection.is_false_positive == False
        ).offset(skip).limit(limit).all()
    
    def get_detections_by_type(self, secret_type: str, db: Session,
                              skip: int = 0, limit: int = 100) -> List[Detection]:
        """Get detections of a specific secret type"""
        return db.query(Detection).filter(
            Detection.secret_type == secret_type,
            Detection.is_false_positive == False
        ).offset(skip).limit(limit).all()
    
    def count_detections(self, repository_id: Optional[int] = None, 
                        db: Session = None,
                        exclude_false_positives: bool = True) -> int:
        """Count total detections"""
        query = db.query(Detection)
        
        if repository_id:
            query = query.filter(Detection.repository_id == repository_id)
        
        if exclude_false_positives:
            query = query.filter(Detection.is_false_positive == False)
        
        return query.count()
    
    def mark_as_false_positive(self, detection_id: int, reason: str,
                              marked_by: str, db: Session) -> Optional[Detection]:
        """Mark a detection as false positive"""
        detection = db.query(Detection).filter(Detection.id == detection_id).first()
        
        if detection:
            detection.is_false_positive = True
            db.commit()
            self.logger.info(f"Marked detection {detection_id} as false positive. Reason: {reason}")
            return detection
        
        return None
    
    def get_statistics(self, db: Session) -> dict:
        """Get overall detection statistics"""
        total_detections = db.query(Detection).count()
        total_legitimate = db.query(Detection).filter(
            Detection.is_false_positive == False
        ).count()
        
        # Get distribution by secret type
        type_distribution = {}
        detections = db.query(Detection).filter(
            Detection.is_false_positive == False
        ).all()
        
        for detection in detections:
            secret_type = detection.secret_type
            type_distribution[secret_type] = type_distribution.get(secret_type, 0) + 1
        
        # Get average confidence
        avg_confidence = 0.0
        if detections:
            avg_confidence = sum(d.confidence_score for d in detections) / len(detections)
        
        return {
            "total_detections": total_detections,
            "legitimate_detections": total_legitimate,
            "false_positives": total_detections - total_legitimate,
            "type_distribution": type_distribution,
            "average_confidence": round(avg_confidence, 3)
        }
