"""
Dashboard Schemas
"""
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class VulnerabilitySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

class ProjectSummary(BaseModel):
    total_projects: int
    active_projects: int
    frameworks: Dict[str, int]

class ScanSummary(BaseModel):
    total_scans: int
    completed_scans: int
    failed_scans: int
    average_pass_rate: float

class TrendDataPoint(BaseModel):
    date: str
    value: float  # Changed from int to float to support pass_rate

class TrendData(BaseModel):
    scans: List[TrendDataPoint]
    vulnerabilities: List[TrendDataPoint]
    pass_rate: List[TrendDataPoint]  # Changed from Dict to TrendDataPoint

class TopVulnerability(BaseModel):
    check_id: str
    check_name: str
    count: int
    severity: str

class VulnerabilityByProject(BaseModel):
    project_name: str
    failed_checks: int

class DashboardStats(BaseModel):
    projects: ProjectSummary
    scans: ScanSummary
    vulnerabilities: VulnerabilitySummary
    trends: TrendData
    top_vulnerabilities: List[TopVulnerability]
    recent_scans: List[Dict]
    vulnerabilities_by_project: List[VulnerabilityByProject]
