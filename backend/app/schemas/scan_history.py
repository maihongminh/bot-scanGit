from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ScanHistoryBase(BaseModel):
    scan_type: str = "full"  # full, incremental, manual
    total_commits_scanned: int = 0
    total_secrets_found: int = 0
    errors_count: int = 0

class ScanHistoryCreate(ScanHistoryBase):
    repository_id: int

class ScanHistoryResponse(ScanHistoryBase):
    id: int
    repository_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    scan_status: str  # running, completed, error
    execution_time_seconds: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
