from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CommitBase(BaseModel):
    commit_hash: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    message: Optional[str] = None
    commit_url: Optional[str] = None

class CommitCreate(CommitBase):
    repository_id: int
    scan_status: str = "pending"

class CommitResponse(CommitBase):
    id: int
    repository_id: int
    scanned_at: Optional[datetime] = None
    has_secrets: bool
    scan_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
