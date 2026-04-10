from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl

class RepositoryBase(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    owner: Optional[str] = None
    language: Optional[str] = None
    is_public: bool = True

class RepositoryCreate(RepositoryBase):
    pass

class RepositoryUpdate(BaseModel):
    description: Optional[str] = None
    scan_status: Optional[str] = None
    is_active: Optional[bool] = None

class RepositoryResponse(RepositoryBase):
    id: int
    stars_count: int
    forks_count: int
    last_scanned_at: Optional[datetime] = None
    next_scan_at: Optional[datetime] = None
    scan_status: str
    total_commits: int
    secrets_found: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RepositoryDetailResponse(RepositoryResponse):
    """Detailed repository response with relationships"""
    pass
