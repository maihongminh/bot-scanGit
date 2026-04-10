from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from .base import Base

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    url = Column(String(500), nullable=False)
    description = Column(Text)
    owner = Column(String(255))
    stars_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    language = Column(String(50))
    is_public = Column(Boolean, default=True)
    last_scanned_at = Column(DateTime, nullable=True, index=True)
    next_scan_at = Column(DateTime, nullable=True)
    scan_status = Column(String(50), default="pending", index=True)  # pending, scanning, completed, error
    total_commits = Column(Integer, default=0)
    secrets_found = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    detections = relationship("Detection", back_populates="repository", cascade="all, delete-orphan")
    scan_history = relationship("ScanHistory", back_populates="repository", cascade="all, delete-orphan")
    user_repositories = relationship("UserRepository", back_populates="repository", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Repository(name='{self.name}', url='{self.url}', secrets_found={self.secrets_found})>"
