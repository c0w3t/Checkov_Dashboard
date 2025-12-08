"""
Scan Schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class ScanBase(BaseModel):
    project_id: int
    scan_type: str = Field(default="full", pattern="^(full|incremental|manual|upload|github_actions|docker|dockerfile|kubernetes|terraform)$")
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    triggered_by: Optional[str] = None

class ScanCreate(ScanBase):
    pass

class ScanUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed)$")
    total_checks: Optional[int] = None
    passed_checks: Optional[int] = None
    failed_checks: Optional[int] = None
    skipped_checks: Optional[int] = None
    scan_duration: Optional[int] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class ScanStatistics(BaseModel):
    total_checks: int
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    pass_rate: float

class VulnerabilityBrief(BaseModel):
    """Brief vulnerability info for scan response"""
    id: int
    check_id: str
    check_name: str
    severity: str
    file_path: str
    line_start: Optional[int] = None

    class Config:
        from_attributes = True

class ScanResponse(ScanBase):
    id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    total_checks: int
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    scan_duration: Optional[int] = None
    scan_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    statistics: Optional[ScanStatistics] = None
    vulnerabilities: Optional[List[VulnerabilityBrief]] = None

    class Config:
        from_attributes = True
