from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class FalsePositive(Base):
    __tablename__ = "false_positives"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="CASCADE"), nullable=False, index=True)
    reason_code = Column(String(100))  # whitelist, test_data, example_code, etc
    reason_description = Column(Text)
    marked_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    detection = relationship("Detection", back_populates="false_positives")
    
    def __repr__(self):
        return f"<FalsePositive(detection_id={self.detection_id}, reason='{self.reason_code}')>"
