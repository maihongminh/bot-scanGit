from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class ScanHistory(Base):
    __tablename__ = "scan_history"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_type = Column(String(50), default="full")  # full, incremental, manual
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_commits_scanned = Column(Integer, default=0)
    total_secrets_found = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_message = Column(Text)
    scan_status = Column(String(50), default="running")  # running, completed, error
    execution_time_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="scan_history")
    
    def __repr__(self):
        return f"<ScanHistory(repo_id={self.repository_id}, status='{self.scan_status}', secrets={self.total_secrets_found})>"
