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
        # Count repositories
        total_repos = db.query(Repository).count()
        scanning_repos = db.query(Repository).filter(
            Repository.scan_status == "scanning"
        ).count()
        
        # Count detections
        total_detections = db.query(Detection).count()
        legitimate_detections = db.query(Detection).filter(
            Detection.is_false_positive == False
        ).count()
        false_positives = total_detections - legitimate_detections
        
        # Get detection statistics
        detection_service = DetectionService()
        detection_stats = detection_service.get_statistics(db)
        
        # Get scan statistics
        recent_scans = db.query(ScanHistory).order_by(
            ScanHistory.completed_at.desc()
        ).limit(10).all()
        
        avg_execution_time = 0
        if recent_scans:
            times = [s.execution_time_seconds for s in recent_scans if s.execution_time_seconds]
            avg_execution_time = sum(times) / len(times) if times else 0
        
        return {
            "repositories": {
                "total": total_repos,
                "scanning": scanning_repos,
                "completed": total_repos - scanning_repos
            },
            "detections": {
                "total": total_detections,
                "legitimate": legitimate_detections,
                "false_positives": false_positives
            },
            "detection_stats": detection_stats,
            "recent_scans": {
                "count": len(recent_scans),
                "avg_execution_time_seconds": round(avg_execution_time, 2)
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting statistics overview: {str(e)}")
        raise

@router.get("/by-type")
async def get_statistics_by_secret_type(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
                    "count": 0,
                    "repositories": set(),
                    "avg_confidence": 0,
                    "confidences": []
                }
            
            stats_by_type[secret_type]["count"] += 1
            stats_by_type[secret_type]["repositories"].add(detection.repository_id)
            stats_by_type[secret_type]["confidences"].append(detection.confidence_score)
        
        # Calculate averages
        for secret_type, stats in stats_by_type.items():
            stats["repositories_affected"] = len(stats["repositories"])
            stats["avg_confidence"] = round(
                sum(stats["confidences"]) / len(stats["confidences"]), 3
            ) if stats["confidences"] else 0
            del stats["repositories"]
            del stats["confidences"]
        
        return stats_by_type
    
    except Exception as e:
        logger.error(f"Error getting statistics by type: {str(e)}")
        raise

@router.get("/by-repository")
async def get_statistics_by_repository(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get statistics by repository"""
    try:
        stats_by_repo = {}
        
        repos = db.query(Repository).all()
        
        for repo in repos:
            detections = db.query(Detection).filter(
                Detection.repository_id == repo.id,
                Detection.is_false_positive == False
            ).all()
            
            secret_types = {}
            for detection in detections:
                secret_type = detection.secret_type
                secret_types[secret_type] = secret_types.get(secret_type, 0) + 1
            
            stats_by_repo[repo.name] = {
                "repository_id": repo.id,
                "total_secrets": len(detections),
                "secret_types": secret_types,
                "last_scanned": repo.last_scanned_at.isoformat() if repo.last_scanned_at else None,
                "scan_status": repo.scan_status
            }
        
        return stats_by_repo
    
    except Exception as e:
        logger.error(f"Error getting statistics by repository: {str(e)}")
        raise

@router.get("/timeline")
async def get_statistics_timeline(
    days: int = 30,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
                    "count": 0,
                    "by_type": {}
                }
            
            timeline[date_key]["count"] += 1
            secret_type = detection.secret_type
            timeline[date_key]["by_type"][secret_type] = (
                timeline[date_key]["by_type"].get(secret_type, 0) + 1
            )
        
        return {
            "period_days": days,
            "timeline": timeline
        }
    
    except Exception as e:
        logger.error(f"Error getting timeline statistics: {str(e)}")
        raise

@router.get("/scan-history")
async def get_scan_history_statistics(
    limit: int = 30,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recent scan history statistics"""
    try:
        scans = db.query(ScanHistory).order_by(
            ScanHistory.completed_at.desc()
        ).limit(limit).all()
        
        total_scans = db.query(ScanHistory).count()
        completed_scans = db.query(ScanHistory).filter(
            ScanHistory.scan_status == "completed"
        ).count()
        error_scans = db.query(ScanHistory).filter(
            ScanHistory.scan_status == "error"
        ).count()
        
        total_time = 0
        total_secrets = 0
        total_commits = 0
        
        for scan in scans:
            if scan.execution_time_seconds:
                total_time += scan.execution_time_seconds
            total_secrets += scan.total_secrets_found
            total_commits += scan.total_commits_scanned
        
        return {
            "total_scans": total_scans,
            "completed": completed_scans,
            "errors": error_scans,
            "recent_scans": [
                {
                    "scan_id": scan.id,
                    "repository_id": scan.repository_id,
                    "started_at": scan.started_at.isoformat() if scan.started_at else None,
                    "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                    "commits_scanned": scan.total_commits_scanned,
                    "secrets_found": scan.total_secrets_found,
                    "execution_time": scan.execution_time_seconds,
                    "status": scan.scan_status
                }
                for scan in scans
            ],
            "aggregated": {
                "total_commits_scanned": total_commits,
                "total_secrets_found": total_secrets,
                "total_execution_time_seconds": total_time,
                "avg_secrets_per_scan": round(total_secrets / len(scans), 2) if scans else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting scan history: {str(e)}")
        raise
