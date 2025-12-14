"""
Scans Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.scan import Scan
from app.models.project import Project
from app.schemas.scan import ScanCreate, ScanUpdate, ScanResponse
from app.services.scan_service import ScanService

router = APIRouter()
scan_service = ScanService()

@router.get("/", response_model=List[ScanResponse])
async def list_scans(
    project_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all scans, optionally filtered by project"""
    query = db.query(Scan)
    if project_id:
        query = query.filter(Scan.project_id == project_id)
    
    scans = query.order_by(Scan.started_at.desc()).offset(skip).limit(limit).all()
    return scans

@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan: ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create and start a new scan"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == scan.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Create scan
    db_scan = Scan(**scan.dict(exclude={"skip_checks"}), status="pending")
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    
    # Persist skip_checks in scan_metadata for ScanService to consume
    if scan.skip_checks:
        db_scan.scan_metadata = (db_scan.scan_metadata or {})
        db_scan.scan_metadata.update({"skip_checks": scan.skip_checks})
        db.commit()

    # Start scan in background
    background_tasks.add_task(scan_service.execute_scan, db_scan.id, db)
    
    return db_scan

@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific scan"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    return scan

@router.put("/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: int,
    scan_update: ScanUpdate,
    db: Session = Depends(get_db)
):
    """Update a scan"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    update_data = scan_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scan, field, value)
    
    db.commit()
    db.refresh(scan)
    return scan

@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db)
):
    """Delete a scan"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    db.delete(scan)
    db.commit()
    return None
