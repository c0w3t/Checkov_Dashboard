from fastapi import BackgroundTasks
from fastapi import UploadFile
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
# Ensure APIRouter is imported
from fastapi import APIRouter
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
import zipfile
import time
from pathlib import Path
from datetime import datetime
from app.database import get_db
from app.models.scan import Scan
from app.models.project import Project
from app.models.vulnerability import Vulnerability
from app.models.file_version import FileVersion
from app.schemas.scan import ScanResponse
from app.services.scan_service import ScanService
import logging
import hashlib
from app.models.notification_settings import NotificationHistory

router = APIRouter()
scan_service = ScanService()

# Upload directory (use absolute path relative to repository backend folder)
BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_files(
    project_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload files only (without scanning)
    
    Accepts:
    - Single file (e.g., main.tf, deployment.yaml, Dockerfile)
    - Multiple files
    - Zip file (will be extracted)
    
    Returns upload_id that can be used later for scanning
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create upload directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_id = f"{project_id}_{timestamp}"
    scan_dir = UPLOAD_DIR / f"project_{project_id}" / timestamp
    scan_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        uploaded_files = []
        # Save uploaded files
        for file in files:
            # Handle folder structure from webkitRelativePath
            # filename might be "folder/subfolder/file.txt"
            file_path = scan_dir / file.filename

            # Create parent directories if needed (for folder uploads)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append(file.filename)

            # If zip file, extract it
            if file.filename.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(scan_dir)
                # Remove zip file after extraction
                os.remove(file_path)
                uploaded_files.append("(extracted)")
        
        # Count total files in directory
        total_files = sum(1 for _ in scan_dir.rglob('*') if _.is_file())

        # Log notification: files uploaded
        try:
            db.add(NotificationHistory(
                project_id=project_id,
                scan_id=None,
                notification_type="files_uploaded",
                subject=f"Files uploaded ({total_files})",
                recipients=[],
                sent_at=datetime.utcnow(),
                status="sent",
            ))
            db.commit()
        except Exception:
            pass

        return {
            "message": "Files uploaded successfully",
            "upload_id": upload_id,
            "project_id": project_id,
            "upload_path": str(scan_dir),
            "uploaded_files": uploaded_files,
            "total_files": total_files,
            "timestamp": timestamp
        }
        
    except Exception as e:
        # Cleanup on error
        if scan_dir.exists():
            shutil.rmtree(scan_dir)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


from fastapi import Body

@router.post("/upload/{upload_id}/file/scan")
async def update_file_and_scan(
    upload_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    data: dict = Body(...)
):
    """
    Start scan on previously uploaded files
    
    Args:
        upload_id: Format "project_id_timestamp" from upload endpoint
    """
    try:
        # Parse upload_id
        parts = upload_id.split('_')
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid upload_id format")

        project_id = int(parts[0])
        timestamp = '_'.join(parts[1:])

        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if upload directory exists
        scan_dir = UPLOAD_DIR / f"project_{project_id}" / timestamp
        logging.getLogger(__name__).warning(f"Checking scan_dir: {scan_dir} resolved={scan_dir.resolve()} exists={scan_dir.exists()} cwd={Path.cwd()}")
        if not scan_dir.exists():
            raise HTTPException(status_code=404, detail="Upload not found. Please upload files first.")

        # Only update file if file_path and content are provided (edit & scan)
        file_path = data.get("file_path") if data else None
        content = data.get("content") if data else None
        if file_path and content is not None:
            abs_file_path = (scan_dir / file_path).resolve()
            if not str(abs_file_path).startswith(str(scan_dir.resolve())):
                raise HTTPException(status_code=400, detail="Invalid file_path (outside upload directory)")
            try:
                abs_file_path.parent.mkdir(parents=True, exist_ok=True)
                # Write file with proper flushing
                with open(abs_file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())  # Force OS to write to disk immediately

                # Verify file was written
                with open(abs_file_path, "r", encoding="utf-8") as f:
                    written_content = f.read()
                    if written_content != content:
                        raise Exception("File verification failed - content mismatch")

                logging.getLogger(__name__).info(f"File updated and verified: {abs_file_path}")
                # Log notification: file changed
                try:
                    db.add(NotificationHistory(
                        project_id=project_id,
                        scan_id=None,
                        notification_type="file_changed",
                        subject=f"File changed: {file_path}",
                        recipients=[],
                        sent_at=datetime.utcnow(),
                        status="sent",
                    ))
                    db.commit()
                except Exception:
                    pass

                # Save file version to database for history tracking
                content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

                # Get current version number for this file
                last_version = db.query(FileVersion).filter(
                    FileVersion.upload_id == upload_id,
                    FileVersion.file_path == file_path
                ).order_by(FileVersion.version_number.desc()).first()

                version_number = (last_version.version_number + 1) if last_version else 1

                # Only save if content has changed (avoid duplicate versions)
                saved_file_version = None
                if not last_version or last_version.content_hash != content_hash:
                    saved_file_version = FileVersion(
                        upload_id=upload_id,
                        project_id=project_id,
                        file_path=file_path,
                        content=content,
                        content_hash=content_hash,
                        version_number=version_number,
                        change_summary=data.get("change_summary"),  # Optional from frontend
                        edited_by=data.get("edited_by")  # Optional from frontend
                    )
                    db.add(saved_file_version)
                    db.commit()
                    db.refresh(saved_file_version)
                    logging.getLogger(__name__).info(f"Saved file version {version_number} for {file_path}")

                # Small delay to ensure filesystem sync (especially on network drives)
                time.sleep(0.1)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")

        # Create scan record
        db_scan = Scan(
            project_id=project_id,
            scan_type="upload",
            status="pending",
            started_at=datetime.now()
        )
        db.add(db_scan)
        db.commit()
        db.refresh(db_scan)

        # Execute scan synchronously when file is edited (for immediate feedback)
        # Use background task only for regular scans without file editing
        if file_path and content is not None:
            # Link the file version to this scan
            if 'saved_file_version' in locals() and saved_file_version:
                saved_file_version.scan_id = db_scan.id
                db.commit()

            # Synchronous scan for edit & scan
            await scan_service.execute_scan_on_upload(
                db_scan.id,
                str(scan_dir),
                project.framework,
                db
            )
            # Refresh to get updated scan results and vulnerabilities
            db.refresh(db_scan)
            # Explicitly load vulnerabilities for response
            db_scan.vulnerabilities = db.query(Vulnerability).filter(
                Vulnerability.scan_id == db_scan.id
            ).all()
        else:
            # Background scan for regular upload scan
            background_tasks.add_task(
                scan_service.execute_scan_on_upload,
                db_scan.id,
                str(scan_dir),
                project.framework,
                db
            )

        return db_scan

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload_id format")
    except HTTPException:
        # Re-raise HTTP errors meant for the client
        raise
    except Exception as e:
        logging.getLogger(__name__).exception("Scan failed")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@router.get("/uploads/{project_id}")
async def list_uploads(
    project_id: int,
    db: Session = Depends(get_db)
):
    """List all uploaded files for a project (ready to scan)"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    upload_base_dir = UPLOAD_DIR / f"project_{project_id}"
    if not upload_base_dir.exists():
        return {"uploads": []}
    
    uploads = []
    for timestamp_dir in upload_base_dir.iterdir():
        if timestamp_dir.is_dir():
            timestamp = timestamp_dir.name
            upload_id = f"{project_id}_{timestamp}"
            
            # Count files
            total_files = sum(1 for _ in timestamp_dir.rglob('*') if _.is_file())
            
            # Check if already scanned
            existing_scan = db.query(Scan).filter(
                Scan.project_id == project_id,
                Scan.scan_type == "upload"
            ).order_by(Scan.created_at.desc()).first()
            
            uploads.append({
                "upload_id": upload_id,
                "timestamp": timestamp,
                "total_files": total_files,
                "path": str(timestamp_dir),
                "scanned": existing_scan is not None if existing_scan else False
            })
    
    return {"uploads": sorted(uploads, key=lambda x: x['timestamp'], reverse=True)}


@router.get("/upload/{upload_id}/files")
async def list_upload_files(upload_id: str):
    """List all files in an upload directory"""
    try:
        # Parse upload_id
        parts = upload_id.split('_')
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid upload_id format")

        project_id = int(parts[0])
        timestamp = '_'.join(parts[1:])

        # Get upload directory
        scan_dir = UPLOAD_DIR / f"project_{project_id}" / timestamp
        if not scan_dir.exists():
            raise HTTPException(status_code=404, detail="Upload not found")

        # List all files recursively
        files = []
        for file_path in scan_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(scan_dir)
                files.append({
                    "path": str(relative_path),
                    "name": file_path.name,
                    "size": file_path.stat().st_size
                })

        return {"files": files}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/upload/{upload_id}/file")
async def get_file_content(upload_id: str, file_path: str):
    """Get content of a specific file in upload directory"""
    try:
        # Parse upload_id
        parts = upload_id.split('_')
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid upload_id format")

        project_id = int(parts[0])
        timestamp = '_'.join(parts[1:])

        # Get upload directory
        scan_dir = UPLOAD_DIR / f"project_{project_id}" / timestamp
        if not scan_dir.exists():
            raise HTTPException(status_code=404, detail="Upload not found")

        # Get file path (prevent directory traversal)
        abs_file_path = (scan_dir / file_path).resolve()
        if not str(abs_file_path).startswith(str(scan_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file_path (outside upload directory)")

        if not abs_file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Read file content
        with open(abs_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "file_path": file_path,
            "content": content
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload_id format")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not text-based or uses unsupported encoding")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.delete("/upload/{project_id}/{timestamp}")
async def delete_uploaded_files(
    project_id: int,
    timestamp: str
):
    """Delete uploaded files after scan"""
    scan_dir = UPLOAD_DIR / f"project_{project_id}" / timestamp

    if scan_dir.exists():
        shutil.rmtree(scan_dir)
        return {"message": "Files deleted successfully"}

    raise HTTPException(status_code=404, detail="Upload directory not found")


@router.get("/diagnostics/uploads")
async def diagnostics_uploads():
    """Temporary diagnostics endpoint: returns server-side upload path info and listing"""
    try:
        resolved = UPLOAD_DIR.resolve()
    except Exception:
        resolved = UPLOAD_DIR

    cwd = Path.cwd()
    projects = []
    if UPLOAD_DIR.exists():
        for p in sorted(UPLOAD_DIR.iterdir()):
            try:
                if p.is_dir():
                    subdirs = [d.name for d in sorted(p.iterdir()) if d.is_dir()]
                    projects.append({"project_dir": p.name, "subdirs": subdirs})
                else:
                    projects.append({"file": p.name})
            except Exception:
                projects.append({"error_reading": p.name})

    return {
        "upload_dir": str(UPLOAD_DIR),
        "resolved": str(resolved),
        "cwd": str(cwd),
        "projects": projects
    }
