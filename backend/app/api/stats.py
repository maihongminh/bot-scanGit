"""Statistics endpoints"""
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from ..services.database_service import get_db
from ..services.detection_service import DetectionService
from ..models.repository import Repository
from ..models.detection import Detection
from ..models.scan_history import ScanHistory
from ..utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/overview")
async def get_statistics_overview(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get overall statistics"""
    try:
        # Count detections
        total_detections = db.query(Detection).count()
        legitimate_detections = db.query(Detection).filter(
            Detection.is_false_positive == False
        ).count()
        false_positives = total_detections - legitimate_detections
        
        # High confidence detections
        high_confidence = db.query(Detection).filter(
            Detection.is_false_positive == False,
            Detection.confidence_score >= 0.8
        ).count()
        
        # Average confidence
        avg_confidence = db.query(func.avg(Detection.confidence_score)).filter(
            Detection.is_false_positive == False
        ).scalar() or 0
        
        # Repositories count
        total_repos = db.query(Repository).count()
        
        return {
            "total_detections": total_detections,
            "legitimate_detections": legitimate_detections,
            "false_positives": false_positives,
            "high_confidence_count": high_confidence,
            "avg_confidence_score": round(float(avg_confidence), 2),
            "repositories_count": total_repos
        }
    
    except Exception as e:
        logger.error(f"Error getting statistics overview: {str(e)}")
        raise

@router.get("/by-type")
async def get_statistics_by_secret_type(
    db: Session = Depends(get_db)
) -> list:
    """Get statistics by secret type"""
    try:
        stats_by_type = {}
        
        detections = db.query(Detection).filter(
            Detection.is_false_positive == False
        ).all()
        
        for detection in detections:
            secret_type = detection.secret_type
            if secret_type not in stats_by_type:
                stats_by_type[secret_type] = {
                    "secret_type": secret_type,
                    "count": 0,
                    "repositories": set(),
                    "confidences": []
                }
            
            stats_by_type[secret_type]["count"] += 1
            stats_by_type[secret_type]["repositories"].add(detection.repository_id)
            stats_by_type[secret_type]["confidences"].append(detection.confidence_score)
        
        # Convert to list
        result = []
        for secret_type, stats in stats_by_type.items():
            avg_conf = round(
                sum(stats["confidences"]) / len(stats["confidences"]), 2
            ) if stats["confidences"] else 0
            result.append({
                "secret_type": secret_type,
                "count": stats["count"],
                "repositories_affected": len(stats["repositories"]),
                "avg_confidence": avg_conf
            })
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
    
    except Exception as e:
        logger.error(f"Error getting statistics by type: {str(e)}")
        raise

@router.get("/by-repository")
async def get_statistics_by_repository(
    db: Session = Depends(get_db)
) -> list:
    """Get statistics by repository"""
    try:
        result = []
        
        repos = db.query(Repository).all()
        
        for repo in repos:
            detections = db.query(Detection).filter(
                Detection.repository_id == repo.id,
                Detection.is_false_positive == False
            ).all()
            
            high_confidence = len([d for d in detections if d.confidence_score >= 0.8])
            
            types_breakdown = {}
            for detection in detections:
                secret_type = detection.secret_type
                types_breakdown[secret_type] = types_breakdown.get(secret_type, 0) + 1
            
            result.append({
                "repository_id": repo.id,
                "repository_name": repo.name,
                "total_secrets": len(detections),
                "high_confidence_count": high_confidence,
                "types_breakdown": types_breakdown,
                "last_scanned_at": repo.last_scanned_at.isoformat() if repo.last_scanned_at else None,
                "scan_status": repo.scan_status
            })
        
        return sorted(result, key=lambda x: x["total_secrets"], reverse=True)
    
    except Exception as e:
        logger.error(f"Error getting statistics by repository: {str(e)}")
        raise

@router.get("/timeline")
async def get_statistics_timeline(
    days: int = 30,
    db: Session = Depends(get_db)
) -> list:
    """Get detection statistics over time"""
    try:
        timeline = {}
        
        # Get detections from the past N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        detections = db.query(Detection).filter(
            Detection.detected_at >= cutoff_date,
            Detection.is_false_positive == False
        ).all()
        
        # Group by date
        for detection in detections:
            date_key = detection.detected_at.date().isoformat()
            if date_key not in timeline:
                timeline[date_key] = {
                    "date": date_key,
                    "count": 0,
                    "by_type": {}
                }
            
            timeline[date_key]["count"] += 1
            secret_type = detection.secret_type
            timeline[date_key]["by_type"][secret_type] = (
                timeline[date_key]["by_type"].get(secret_type, 0) + 1
            )
        
        # Return sorted by date
        return sorted(timeline.values(), key=lambda x: x["date"])
    
    except Exception as e:
        logger.error(f"Error getting timeline statistics: {str(e)}")
        raise

@router.get("/scan-history")
async def get_scan_history_statistics(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recent scan history statistics with pagination"""
    try:
        # Get paginated scans
        scans = db.query(ScanHistory).order_by(
            ScanHistory.completed_at.desc()
        ).offset(offset).limit(limit).all()
        
        total_scans = db.query(ScanHistory).count()
        
        # Calculate aggregates from ALL scans for summary
        all_scans = db.query(ScanHistory).all()
        total_time = sum([s.execution_time_seconds or 0 for s in all_scans])
        total_secrets = sum([s.total_secrets_found or 0 for s in all_scans])
        total_commits = sum([s.total_commits_scanned or 0 for s in all_scans])
        
        # Get repository names from detections
        scan_items = []
        for scan in scans:
            repo = db.query(Repository).filter(
                Repository.id == scan.repository_id
            ).first()
            
            scan_items.append({
                "id": scan.id,
                "repository_name": repo.name if repo else f"Repo #{scan.repository_id}",
                "scan_date": scan.completed_at.isoformat() if scan.completed_at else scan.started_at.isoformat() if scan.started_at else None,
                "commits_scanned": scan.total_commits_scanned or 0,
                "secrets_found": scan.total_secrets_found or 0,
                "execution_time_seconds": scan.execution_time_seconds or 0,
                "status": scan.scan_status
            })
        
        return {
            "items": scan_items,
            "total": total_scans,
            "total_commits_scanned": total_commits,
            "total_secrets_found": total_secrets,
            "total_scan_time_seconds": total_time
        }
    
    except Exception as e:
        logger.error(f"Error getting scan history: {str(e)}")
        raise
