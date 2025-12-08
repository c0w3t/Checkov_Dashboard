"""
File History Router - API endpoints for file version history and vulnerability tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.file_version import FileVersion
from app.models.vulnerability import Vulnerability
from app.models.scan import Scan
from app.models.project import Project
from pydantic import BaseModel
from pathlib import Path
import hashlib

router = APIRouter()

# Pydantic models for responses
class FileVersionResponse(BaseModel):
    id: int
    upload_id: str
    project_id: int
    file_path: str
    content: str
    content_hash: str
    version_number: int
    scan_id: Optional[int]
    change_summary: Optional[str]
    edited_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class VulnerabilityComparison(BaseModel):
    check_id: str
    check_name: str
    severity: str
    file_path: str
    line_number: int
    status: str  # 'new', 'existing', 'fixed'
    first_detected: datetime
    last_seen: Optional[datetime]
    resolved_at: Optional[datetime]

@router.get("/file-versions/{upload_id}/{file_path:path}")
async def get_file_version_history(
    upload_id: str,
    file_path: str,
    db: Session = Depends(get_db)
):
    """
    Get version history for a specific file

    Returns all versions of a file in chronological order
    """
    versions = db.query(FileVersion).filter(
        FileVersion.upload_id == upload_id,
        FileVersion.file_path == file_path
    ).order_by(desc(FileVersion.version_number)).all()

    if not versions:
        raise HTTPException(status_code=404, detail="No version history found for this file")

    return {
        "upload_id": upload_id,
        "file_path": file_path,
        "total_versions": len(versions),
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "content_hash": v.content_hash,
                "scan_id": v.scan_id,
                "change_summary": v.change_summary,
                "edited_by": v.edited_by,
                "created_at": v.created_at
            }
            for v in versions
        ]
    }

@router.get("/file-versions/{upload_id}")
async def list_all_file_versions(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    List all files that have version history for an upload
    """
    # Get distinct file paths for this upload
    versions = db.query(FileVersion).filter(
        FileVersion.upload_id == upload_id
    ).order_by(FileVersion.file_path, desc(FileVersion.version_number)).all()

    if not versions:
        raise HTTPException(status_code=404, detail="No version history found for this upload")

    # Group by file path
    files_dict = {}
    for v in versions:
        if v.file_path not in files_dict:
            files_dict[v.file_path] = {
                "file_path": v.file_path,
                "latest_version": v.version_number,
                "total_versions": 1,
                "last_edited": v.created_at
            }
        else:
            files_dict[v.file_path]["total_versions"] += 1

    return {
        "upload_id": upload_id,
        "files": list(files_dict.values())
    }

@router.get("/file-version/{version_id}")
async def get_file_version_content(
    version_id: int,
    db: Session = Depends(get_db)
):
    """
    Get full content of a specific file version
    """
    version = db.query(FileVersion).filter(FileVersion.id == version_id).first()

    if not version:
        raise HTTPException(status_code=404, detail="File version not found")

    return {
        "id": version.id,
        "upload_id": version.upload_id,
        "file_path": version.file_path,
        "version_number": version.version_number,
        "content": version.content,
        "content_hash": version.content_hash,
        "scan_id": version.scan_id,
        "change_summary": version.change_summary,
        "edited_by": version.edited_by,
        "created_at": version.created_at
    }

@router.get("/file-versions/by-file")
async def get_versions_by_file_path(
    file_path: str,
    db: Session = Depends(get_db)
):
    """
    List all versions for a given file_path across uploads.
    Useful when upload_id is unknown or not consistent.
    """
    # Support both exact relative path and basename search
    # e.g., 'Dockerfile.001' should match '/some/path/Dockerfile.001'
    like_pattern = f"%/{file_path}"
    versions = db.query(FileVersion).filter(
        or_(
            FileVersion.file_path == file_path,
            FileVersion.file_path.like(like_pattern),
            FileVersion.file_path.like(f"%{file_path}")
        )
    ).order_by(desc(FileVersion.created_at)).all()
    if not versions:
        raise HTTPException(status_code=404, detail="No version history found for this file path")

    return {
        "file_path": file_path,
        "total_versions": len(versions),
        "versions": [
            {
                "id": v.id,
                "upload_id": v.upload_id,
                "version_number": v.version_number,
                "content_hash": v.content_hash,
                "scan_id": v.scan_id,
                "change_summary": v.change_summary,
                "edited_by": v.edited_by,
                "created_at": v.created_at
            }
            for v in versions
        ]
    }

class RecordOriginalRequest(BaseModel):
    vulnerability_id: int

@router.post("/file-versions/record-original")
async def record_original_version(
    request: RecordOriginalRequest,
    db: Session = Depends(get_db)
):
    """
    Record the current original content of a vulnerability's file as version 1.
    Use a stable upload_id per project when scan timestamp isn't consistent.
    """
    vuln = db.query(Vulnerability).filter(Vulnerability.id == request.vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    from pathlib import Path
    file_abs = Path(vuln.file_path)
    if not file_abs.exists():
        base_dir = Path(__file__).resolve().parents[2]
        candidate = base_dir / "uploads" / vuln.file_path
        file_abs = candidate if candidate.exists() else file_abs
    if not file_abs.exists():
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_abs, 'r') as f:
        content = f.read()

    import hashlib
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    # Normalize to project-level upload id and basename path for robust lookups
    upload_id = f"project_{vuln.scan.project_id}"
    rel_path = Path(vuln.file_path).name

    # If exists, don't duplicate v1
    existing = (
        db.query(FileVersion)
        .filter(FileVersion.upload_id == upload_id, FileVersion.file_path == rel_path)
        .order_by(FileVersion.version_number.asc())
        .first()
    )
    if existing:
        return {"message": "Original already recorded", "upload_id": upload_id, "file_path": rel_path}

    db.add(FileVersion(
        upload_id=upload_id,
        project_id=vuln.scan.project_id,
        file_path=rel_path,
        content=content,
        content_hash=content_hash,
        version_number=1,
        scan_id=vuln.scan_id,
        change_summary="Initial original content",
        edited_by=None,
    ))
    db.commit()

    return {"message": "Original recorded", "upload_id": upload_id, "file_path": rel_path}


class RestoreRequest(BaseModel):
    version_id: int

class RestoreResponse(BaseModel):
    success: bool
    file_path: Optional[str]
    error: Optional[str] = None

@router.post("/file-versions/restore", response_model=RestoreResponse)
async def restore_file_version(
    request: RestoreRequest,
    db: Session = Depends(get_db)
):
    """
    Restore a specific file version by writing its content back to disk
    and recording a new version entry.
    """
    version = db.query(FileVersion).filter(FileVersion.id == request.version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="File version not found")

    # Resolve absolute path under backend/uploads if possible
    try:
        base_dir = Path(__file__).resolve().parents[2]
        uploads_dir = base_dir / "uploads"

        # upload_id format may be "project_XX/timestamp" or similar
        upload_parts = version.upload_id.split("/") if version.upload_id else []
        file_abs = None
        if upload_parts:
            candidate = uploads_dir / upload_parts[0]
            if len(upload_parts) > 1:
                candidate = candidate / upload_parts[1]
            file_abs = candidate / version.file_path

        # Fallback: if we cannot build the absolute path, try using file_path as absolute
        if not file_abs:
            file_abs = Path(version.file_path)

        # Ensure parent exists
        if not file_abs.parent.exists():
            raise HTTPException(status_code=404, detail="File directory not found for restore")

        # Write restored content
        with open(file_abs, 'w') as f:
            f.write(version.content)

        # Record a new version noting the restore
        new_version_number = (db.query(FileVersion)
                              .filter(FileVersion.upload_id == version.upload_id,
                                      FileVersion.file_path == version.file_path)
                              .order_by(desc(FileVersion.version_number))
                              .first())
        next_v = (new_version_number.version_number + 1) if new_version_number else 1
        restored_hash = hashlib.sha256(version.content.encode('utf-8')).hexdigest()
        db.add(FileVersion(
            upload_id=version.upload_id,
            project_id=version.project_id,
            file_path=version.file_path,
            content=version.content,
            content_hash=restored_hash,
            version_number=next_v,
            scan_id=None,
            change_summary=f"Restore to v{version.version_number}",
            edited_by="restore",
        ))
        db.commit()

        return RestoreResponse(success=True, file_path=str(file_abs))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore version: {e}")

@router.get("/vulnerabilities/compare/{project_id}")
async def compare_vulnerabilities(
    project_id: int,
    scan_id_1: Optional[int] = None,
    scan_id_2: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Compare vulnerabilities between two scans or show fixed/unfixed for latest scan

    If scan_id_1 and scan_id_2 provided: compare those two scans
    If only scan_id_1 provided: compare with previous scan
    If none provided: show fixed/unfixed for latest scan
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get scans to compare
    if not scan_id_1:
        # Use latest two scans
        latest_scans = db.query(Scan).filter(
            Scan.project_id == project_id,
            Scan.status == "completed"
        ).order_by(desc(Scan.completed_at)).limit(2).all()

        if len(latest_scans) < 2:
            raise HTTPException(
                status_code=400,
                detail="Not enough scans to compare. Need at least 2 completed scans."
            )

        scan_id_1 = latest_scans[0].id  # Latest
        scan_id_2 = latest_scans[1].id  # Previous

    elif not scan_id_2:
        # Find previous scan before scan_id_1
        scan_1 = db.query(Scan).filter(Scan.id == scan_id_1).first()
        if not scan_1:
            raise HTTPException(status_code=404, detail="Scan not found")

        previous_scan = db.query(Scan).filter(
            Scan.project_id == project_id,
            Scan.completed_at < scan_1.completed_at,
            Scan.status == "completed"
        ).order_by(desc(Scan.completed_at)).first()

        if not previous_scan:
            raise HTTPException(
                status_code=400,
                detail="No previous scan found for comparison"
            )

        scan_id_2 = previous_scan.id

    # Get vulnerabilities from both scans
    scan_1 = db.query(Scan).filter(Scan.id == scan_id_1).first()
    scan_2 = db.query(Scan).filter(Scan.id == scan_id_2).first()

    if not scan_1 or not scan_2:
        raise HTTPException(status_code=404, detail="One or both scans not found")

    vulns_1 = db.query(Vulnerability).filter(Vulnerability.scan_id == scan_id_1).all()
    vulns_2 = db.query(Vulnerability).filter(Vulnerability.scan_id == scan_id_2).all()

    # Create hash maps
    vulns_1_map = {v.vulnerability_hash: v for v in vulns_1 if v.vulnerability_hash}
    vulns_2_map = {v.vulnerability_hash: v for v in vulns_2 if v.vulnerability_hash}

    # Categorize vulnerabilities
    new_vulnerabilities = []
    existing_vulnerabilities = []
    fixed_vulnerabilities = []

    # New vulnerabilities (in scan_1 but not in scan_2)
    for hash_val, vuln in vulns_1_map.items():
        if hash_val not in vulns_2_map:
            new_vulnerabilities.append({
                "check_id": vuln.check_id,
                "check_name": vuln.check_name,
                "severity": vuln.severity.value,
                "file_path": vuln.file_path,
                "line_number": vuln.line_number,
                "status": "new",
                "first_detected": vuln.detected_at,
                "last_seen": vuln.last_seen_at
            })
        else:
            # Existing (in both scans)
            existing_vulnerabilities.append({
                "check_id": vuln.check_id,
                "check_name": vuln.check_name,
                "severity": vuln.severity.value,
                "file_path": vuln.file_path,
                "line_number": vuln.line_number,
                "status": "existing",
                "first_detected": vuln.detected_at,
                "last_seen": vuln.last_seen_at
            })

    # Fixed vulnerabilities (in scan_2 but not in scan_1)
    for hash_val, vuln in vulns_2_map.items():
        if hash_val not in vulns_1_map:
            fixed_vulnerabilities.append({
                "check_id": vuln.check_id,
                "check_name": vuln.check_name,
                "severity": vuln.severity.value,
                "file_path": vuln.file_path,
                "line_number": vuln.line_number,
                "status": "fixed",
                "first_detected": vuln.detected_at,
                "resolved_at": vuln.resolved_at or scan_1.completed_at
            })

    return {
        "project_id": project_id,
        "scan_1": {
            "id": scan_1.id,
            "completed_at": scan_1.completed_at,
            "total_vulnerabilities": len(vulns_1)
        },
        "scan_2": {
            "id": scan_2.id,
            "completed_at": scan_2.completed_at,
            "total_vulnerabilities": len(vulns_2)
        },
        "summary": {
            "new": len(new_vulnerabilities),
            "existing": len(existing_vulnerabilities),
            "fixed": len(fixed_vulnerabilities)
        },
        "new_vulnerabilities": new_vulnerabilities,
        "existing_vulnerabilities": existing_vulnerabilities,
        "fixed_vulnerabilities": fixed_vulnerabilities
    }

@router.get("/vulnerabilities/status/{project_id}")
async def get_vulnerability_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current vulnerability status for a project
    Shows: Open, Fixed, Total vulnerabilities
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest scan
    latest_scan = db.query(Scan).filter(
        Scan.project_id == project_id,
        Scan.status == "completed"
    ).order_by(desc(Scan.completed_at)).first()

    if not latest_scan:
        raise HTTPException(status_code=404, detail="No completed scans found for this project")

    # Get all vulnerabilities from latest scan
    latest_vulns = db.query(Vulnerability).filter(
        Vulnerability.scan_id == latest_scan.id
    ).all()

    # Get all historical vulnerabilities for this project that were fixed
    all_scans = db.query(Scan).filter(
        Scan.project_id == project_id,
        Scan.status == "completed"
    ).all()

    scan_ids = [s.id for s in all_scans]

    fixed_vulns = db.query(Vulnerability).filter(
        Vulnerability.scan_id.in_(scan_ids),
        Vulnerability.resolved_at.isnot(None)
    ).all()

    # Categorize by severity
    open_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    fixed_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

    for vuln in latest_vulns:
        severity = vuln.severity.value.upper()
        if severity in open_by_severity:
            open_by_severity[severity] += 1

    for vuln in fixed_vulns:
        severity = vuln.severity.value.upper()
        if severity in fixed_by_severity:
            fixed_by_severity[severity] += 1

    return {
        "project_id": project_id,
        "latest_scan": {
            "id": latest_scan.id,
            "completed_at": latest_scan.completed_at
        },
        "summary": {
            "total_open": len(latest_vulns),
            "total_fixed": len(fixed_vulns),
            "total_all_time": len(latest_vulns) + len(fixed_vulns)
        },
        "open_by_severity": open_by_severity,
        "fixed_by_severity": fixed_by_severity
    }
