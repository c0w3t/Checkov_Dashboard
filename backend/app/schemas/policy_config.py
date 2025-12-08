"""
Policy Config Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PolicyConfigBase(BaseModel):
    project_id: Optional[int] = None
    policy_type: str  # docker, kubernetes, terraform
    check_id: str
    enabled: bool = True
    severity_override: Optional[str] = None
    custom_message: Optional[str] = None


class PolicyConfigCreate(PolicyConfigBase):
    pass


class PolicyConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    severity_override: Optional[str] = None
    custom_message: Optional[str] = None


class PolicyConfigResponse(PolicyConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
