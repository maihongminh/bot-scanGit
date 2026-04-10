from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class FalsePositiveBase(BaseModel):
    reason_code: Optional[str] = None
    reason_description: Optional[str] = None

class FalsePositiveCreate(FalsePositiveBase):
    detection_id: int
    marked_by: Optional[str] = None

class FalsePositiveResponse(FalsePositiveBase):
    id: int
    detection_id: int
    marked_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
