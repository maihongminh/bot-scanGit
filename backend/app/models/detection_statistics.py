from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from .base import Base

class DetectionStatistics(Base):
    __tablename__ = "detection_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=date.today)
    secret_type = Column(String(100), index=True)
    count = Column(Integer, default=0)
    repositories_affected = Column(Integer, default=0)
    avg_confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DetectionStatistics(date={self.date}, type='{self.secret_type}', count={self.count})>"
