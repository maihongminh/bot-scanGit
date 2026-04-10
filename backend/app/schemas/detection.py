from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DetectionBase(BaseModel):
    file_path: str
    secret_type: str
    secret_pattern: Optional[str] = None
    line_number: Optional[int] = None
    confidence_score: float = 0.0

class DetectionCreate(DetectionBase):
    commit_id: int
    repository_id: int
    matched_value: Optional[str] = None

class DetectionUpdate(BaseModel):
    is_false_positive: Optional[bool] = None
    remediation_status: Optional[str] = None

class DetectionResponse(DetectionBase):
    id: int
    commit_id: int
    repository_id: int
    matched_value: Optional[str] = None
    is_false_positive: bool
    remediation_status: str
    detected_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
