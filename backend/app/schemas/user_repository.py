from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserRepositoryBase(BaseModel):
    user_added_by: Optional[str] = None
    is_monitored: bool = True
    monitor_frequency: str = "hourly"  # hourly, daily, weekly

class UserRepositoryCreate(UserRepositoryBase):
    repository_id: int

class UserRepositoryResponse(UserRepositoryBase):
    id: int
    repository_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
