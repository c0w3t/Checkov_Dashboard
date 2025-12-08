"""
Project Schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    repository_url: Optional[str] = None
    framework: str = Field(..., pattern="^(terraform|kubernetes|dockerfile)$")
    status: Optional[str] = Field(default="active", pattern="^(active|inactive|archived)$")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    repository_url: Optional[str] = None
    framework: Optional[str] = Field(None, pattern="^(terraform|kubernetes|dockerfile)$")
    status: Optional[str] = Field(None, pattern="^(active|inactive|archived)$")

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    total_scans: int = 0
    last_scan_date: Optional[datetime] = None

    class Config:
        from_attributes = True
