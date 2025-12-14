"""
Projects Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from pathlib import Path
import logging
from datetime import datetime
from app.models.notification_settings import NotificationHistory

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all projects"""
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    # Check if project name already exists
    existing_project = db.query(Project).filter(Project.name == project.name).first()
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists"
        )
    
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    # Log notification: project created
    try:
        db.add(NotificationHistory(
            project_id=db_project.id,
            scan_id=None,
            notification_type="project_created",
            subject=f"Project '{db_project.name}' created",
            recipients=[],
            sent_at=datetime.utcnow(),
            status="sent",
        ))
        db.commit()
    except Exception:
        pass
    return db_project

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Delete a project and all associated data including uploaded files"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Delete uploaded files (use absolute uploads path)
    base_dir = Path(__file__).resolve().parents[2]
    upload_dir = base_dir / f"uploads/project_{project_id}"
    try:
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            logging.getLogger(__name__).info(f"Deleted upload directory: {upload_dir}")
    except Exception as e:
        logging.getLogger(__name__).exception(f"Failed to delete upload directory {upload_dir}: {e}")
    
    # Delete from database (cascade will delete scans, vulnerabilities, etc.)
    db.delete(project)
    db.commit()
    # Log notification: project deleted
    try:
        db.add(NotificationHistory(
            project_id=project_id,
            scan_id=None,
            notification_type="project_deleted",
            subject=f"Project '{project.name}' deleted",
            recipients=[],
            sent_at=datetime.utcnow(),
            status="sent",
        ))
        db.commit()
    except Exception:
        pass
    return None
