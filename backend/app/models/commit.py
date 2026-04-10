from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

class Commit(Base):
    __tablename__ = "commits"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_hash = Column(String(40), nullable=False)
    author_name = Column(String(255))
    author_email = Column(String(255))
    message = Column(Text)
    commit_url = Column(String(500))
    scanned_at = Column(DateTime, nullable=True)
    has_secrets = Column(Boolean, default=False)
    scan_status = Column(String(50), default="pending")  # pending, scanning, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on repository_id + commit_hash
    __table_args__ = (
        UniqueConstraint('repository_id', 'commit_hash', name='uq_repo_commit'),
    )
    
    # Relationships
    repository = relationship("Repository", back_populates="commits")
    detections = relationship("Detection", back_populates="commit", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Commit(hash='{self.commit_hash[:8]}', repo_id={self.repository_id}, has_secrets={self.has_secrets})>"
