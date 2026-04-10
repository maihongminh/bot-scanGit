from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Detection(Base):
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    commit_id = Column(Integer, ForeignKey("commits.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    secret_type = Column(String(100), nullable=False, index=True)  # aws_key, google_api, openai_key, etc
    secret_pattern = Column(String(50))  # Pattern name that matched
    matched_value = Column(String(255))  # First 100 chars of matched secret (masked)
    line_number = Column(Integer)
    confidence_score = Column(Float, default=0.0, index=True)  # 0.0 to 1.0
    is_false_positive = Column(Boolean, default=False)
    remediation_status = Column(String(50), default="pending")  # pending, notified, fixed, dismissed
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    commit = relationship("Commit", back_populates="detections")
    repository = relationship("Repository", back_populates="detections")
    false_positives = relationship("FalsePositive", back_populates="detection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Detection(type='{self.secret_type}', confidence={self.confidence_score:.2f}, file='{self.file_path}')>"
