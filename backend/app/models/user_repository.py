from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class UserRepository(Base):
    __tablename__ = "user_repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_added_by = Column(String(255))
    is_monitored = Column(Boolean, default=True)
    monitor_frequency = Column(String(50), default="hourly")  # hourly, daily, weekly
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="user_repositories")
    
    def __repr__(self):
        return f"<UserRepository(repo_id={self.repository_id}, monitored={self.is_monitored}, freq='{self.monitor_frequency}')>"
