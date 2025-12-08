"""
API Token Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApiTokenBase(BaseModel):
    name: str
    permissions: Optional[str] = None
    expires_at: Optional[datetime] = None


class ApiTokenCreate(ApiTokenBase):
    pass


class ApiTokenResponse(ApiTokenBase):
    id: int
    token: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True
