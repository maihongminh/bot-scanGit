"""Service for database operations"""
import logging
from typing import Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from ..config import settings
from ..models.repository import Repository
from ..models.base import Base

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database management"""
    
    _engine = None
    _SessionLocal = None
    
    @classmethod
    def initialize(cls):
        """Initialize database connection and create tables"""
        try:
            # Create engine with connection pooling
            cls._engine = create_engine(
                settings.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Test connections before using them
                echo=settings.DEBUG
            )
            
            # Create session factory
            cls._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=cls._engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=cls._engine)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    @classmethod
    def get_session(cls) -> Session:
        """Get a database session"""
        if cls._SessionLocal is None:
            cls.initialize()
        
        return cls._SessionLocal()
    
    @classmethod
    def close_session(cls, session: Session):
        """Close a database session"""
        if session:
            session.close()
    
    @staticmethod
    def get_or_create_repository(repo_name: str, db: Session) -> Repository:
        """Get existing repository or create a new one"""
        repo = db.query(Repository).filter(
            Repository.name == repo_name
        ).first()
        
        if not repo:
            repo = Repository(
                name=repo_name,
                url="",
                scan_status="pending"
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)
        
        return repo
    
    @staticmethod
    def cleanup_old_records(db: Session, days: int = 90):
        """
        Clean up old scan history and detections
        
        Args:
            db: Database session
            days: Delete records older than this many days
        """
        from datetime import datetime, timedelta
        from ..models.scan_history import ScanHistory
        from ..models.detection import Detection
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old detections
            deleted_detections = db.query(Detection).filter(
                Detection.created_at < cutoff_date
            ).delete()
            
            # Delete old scan histories
            deleted_scans = db.query(ScanHistory).filter(
                ScanHistory.created_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(
                f"Cleaned up {deleted_detections} detections and "
                f"{deleted_scans} scan history records older than {days} days"
            )
        except Exception as e:
            logger.error(f"Error cleaning up old records: {str(e)}")
            db.rollback()

# Dependency for FastAPI
def get_db() -> Session:
    """FastAPI dependency for database session"""
    db = DatabaseService.get_session()
    try:
        yield db
    finally:
        db.close()
