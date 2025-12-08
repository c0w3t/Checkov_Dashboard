"""
Report Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportBase(BaseModel):
    project_id: int
    report_type: str  # compliance, vulnerability, trend
    title: str
    format: str  # pdf, json, csv


class ReportCreate(ReportBase):
    generated_by: Optional[str] = None


class ReportResponse(ReportBase):
    id: int
    file_path: Optional[str] = None
    generated_by: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True
