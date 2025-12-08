"""
Vulnerabilities Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.vulnerability import Vulnerability, SeverityLevel, VulnerabilityStatus

router = APIRouter()

@router.get("/")
async def list_vulnerabilities(
    scan_id: Optional[int] = None,
    severity: Optional[SeverityLevel] = None,
    status_filter: Optional[VulnerabilityStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get vulnerabilities with optional filters"""
    query = db.query(Vulnerability)
    
    if scan_id:
        query = query.filter(Vulnerability.scan_id == scan_id)
    if severity:
        query = query.filter(Vulnerability.severity == severity)
    if status_filter:
        query = query.filter(Vulnerability.status == status_filter)
    
    vulnerabilities = query.offset(skip).limit(limit).all()
    return vulnerabilities

@router.get("/{vulnerability_id}")
async def get_vulnerability(
    vulnerability_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific vulnerability"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )
    return vuln

@router.patch("/{vulnerability_id}/status")
async def update_vulnerability_status(
    vulnerability_id: int,
    new_status: VulnerabilityStatus,
    db: Session = Depends(get_db)
):
    """Update vulnerability status"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )
    
    vuln.status = new_status
    if new_status == VulnerabilityStatus.RESOLVED:
        from datetime import datetime
        vuln.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(vuln)
    return vuln

@router.get("/statistics/summary")
async def get_vulnerability_summary(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get vulnerability statistics summary"""
    query = db.query(Vulnerability)
    
    if project_id:
        from app.models.scan import Scan
        query = query.join(Scan).filter(Scan.project_id == project_id)
    
    total = query.count()
    by_severity = {
        "critical": query.filter(Vulnerability.severity == SeverityLevel.CRITICAL).count(),
        "high": query.filter(Vulnerability.severity == SeverityLevel.HIGH).count(),
        "medium": query.filter(Vulnerability.severity == SeverityLevel.MEDIUM).count(),
        "low": query.filter(Vulnerability.severity == SeverityLevel.LOW).count(),
        "info": query.filter(Vulnerability.severity == SeverityLevel.INFO).count(),
    }
    by_status = {
        "open": query.filter(Vulnerability.status == VulnerabilityStatus.OPEN).count(),
        "in_progress": query.filter(Vulnerability.status == VulnerabilityStatus.IN_PROGRESS).count(),
        "resolved": query.filter(Vulnerability.status == VulnerabilityStatus.RESOLVED).count(),
        "ignored": query.filter(Vulnerability.status == VulnerabilityStatus.IGNORED).count(),
    }
    
    return {
        "total": total,
        "by_severity": by_severity,
        "by_status": by_status
    }
