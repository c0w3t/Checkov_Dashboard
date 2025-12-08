"""
AI Router - API endpoints for AI-powered features
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.database import get_db
from app.services.ai_service import AIService
from app.models.vulnerability import Vulnerability
from app.models.project import Project
from app.models.file_version import FileVersion
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class GeneratePolicyRequest(BaseModel):
    policy_name: str
    description: str
    framework: str  # terraform, kubernetes, dockerfile
    example_code: Optional[str] = None

class GeneratePolicyResponse(BaseModel):
    success: bool
    policy_code: Optional[str]
    explanation: Optional[str]
    error: Optional[str] = None
    model_used: Optional[str] = None
    model_config = ConfigDict(protected_namespaces=())

class SuggestFixRequest(BaseModel):
    vulnerability_id: int

class SuggestFixResponse(BaseModel):
    success: bool
    explanation: Optional[str]
    fixed_code: Optional[str]
    original_code: Optional[str]
    error: Optional[str] = None
    model_used: Optional[str] = None
    model_config = ConfigDict(protected_namespaces=())

class EditFileRequest(BaseModel):
    project_id: int
    file_path: str
    instruction: str

class EditFileResponse(BaseModel):
    success: bool
    changes: Optional[str]
    edited_content: Optional[str]
    original_content: Optional[str]
    error: Optional[str] = None
    model_used: Optional[str] = None
    model_config = ConfigDict(protected_namespaces=())

class AnalyzeVulnerabilityRequest(BaseModel):
    vulnerability_id: int

class AnalyzeVulnerabilityResponse(BaseModel):
    success: bool
    analysis: Optional[str]
    error: Optional[str] = None
    model_used: Optional[str] = None
    model_config = ConfigDict(protected_namespaces=())

class ApplyFixRequest(BaseModel):
    vulnerability_id: int
    fixed_code: Optional[str] = None

class ApplyFixResponse(BaseModel):
    success: bool
    file_path: Optional[str]
    error: Optional[str] = None

@router.post("/ai/generate-policy", response_model=GeneratePolicyResponse)
async def generate_custom_policy(
    request: GeneratePolicyRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a custom Checkov policy using AI

    **Example request:**
    ```json
    {
      "policy_name": "No hardcoded secrets in environment variables",
      "description": "Check that environment variables don't contain hardcoded secrets like API keys or passwords",
      "framework": "dockerfile",
      "example_code": "ENV API_KEY=sk-1234567890abcdef"
    }
    ```
    """
    ai_service = AIService()

    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Please configure OPENAI_API_KEY in backend .env"
        )

    try:
        result = ai_service.generate_custom_policy(
            policy_name=request.policy_name,
            description=request.description,
            framework=request.framework,
            example_code=request.example_code
        )

        return GeneratePolicyResponse(**result)

    except Exception as e:
        logger.error(f"Failed to generate policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/suggest-fix", response_model=SuggestFixResponse)
async def suggest_fix(
    request: SuggestFixRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI-suggested fix for a vulnerability

    **Example request:**
    ```json
    {
      "vulnerability_id": 123
    }
    ```
    """
    ai_service = AIService()

    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Please configure OPENAI_API_KEY"
        )

    # Get vulnerability details
    vuln = db.query(Vulnerability).filter(Vulnerability.id == request.vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    # Get file content from stored file path
    from pathlib import Path
    project = db.query(Project).filter(Project.id == vuln.scan.project_id).first()

    # Try to read file content
    try:
        # In our storage, vulnerabilities already store absolute or workspace-relative file paths
        # Example: /home/user/Desktop/Dashboard/backend/uploads/project_21/20251207_164420/Dockerfile.001
        upload_path = Path(vuln.file_path)

        # Fallback: if the stored path is relative, resolve under backend/uploads
        if not upload_path.exists():
            base_dir = Path(__file__).resolve().parents[2]
            candidate = base_dir / "uploads" / vuln.file_path
            upload_path = candidate if candidate.exists() else upload_path

        if not upload_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        with open(upload_path, 'r') as f:
            file_content = f.read()

    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    try:
        vulnerability_data = {
            "check_id": vuln.check_id,
            "check_name": vuln.check_name,
            "description": vuln.description,
            "line_number": vuln.line_number
        }

        result = ai_service.suggest_fix_for_vulnerability(
            vulnerability=vulnerability_data,
            file_content=file_content,
            file_path=vuln.file_path
        )

        return SuggestFixResponse(**result)

    except Exception as e:
        logger.error(f"Failed to suggest fix: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/edit-file", response_model=EditFileResponse)
async def edit_file_with_ai(
    request: EditFileRequest,
    db: Session = Depends(get_db)
):
    """
    Edit a file using AI based on natural language instruction

    **Example request:**
    ```json
    {
      "project_id": 1,
      "file_path": "terraform/main.tf",
      "instruction": "Add encryption to the S3 bucket and enable versioning"
    }
    ```
    """
    ai_service = AIService()

    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Please configure OPENAI_API_KEY"
        )

    # Get project
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest upload_id for this project
    from app.models.scan import Scan
    latest_scan = db.query(Scan).filter(
        Scan.project_id == request.project_id
    ).order_by(Scan.id.desc()).first()

    if not latest_scan:
        raise HTTPException(status_code=404, detail="No scans found for project")

    # Read file content
    try:
        from pathlib import Path
        base_dir = Path(__file__).resolve().parents[2]
        upload_path = base_dir / "uploads" / latest_scan.upload_id / request.file_path

        if not upload_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

        with open(upload_path, 'r') as f:
            file_content = f.read()

    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    try:
        result = ai_service.edit_file_with_ai(
            file_content=file_content,
            file_path=request.file_path,
            user_instruction=request.instruction
        )

        return EditFileResponse(**result)

    except Exception as e:
        logger.error(f"Failed to edit file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/apply-fix", response_model=ApplyFixResponse)
async def apply_fix(
    request: ApplyFixRequest,
    db: Session = Depends(get_db)
):
    """
    Apply an AI-suggested fix into the original file.

    If fixed_code is not provided, generate it via suggest-fix first.
    """
    ai_service = AIService()

    # Fetch vulnerability
    vuln = db.query(Vulnerability).filter(Vulnerability.id == request.vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    from pathlib import Path
    try:
        # Resolve file path similarly to suggest-fix
        file_path = Path(vuln.file_path)
        if not file_path.exists():
            base_dir = Path(__file__).resolve().parents[2]
            candidate = base_dir / "uploads" / vuln.file_path
            file_path = candidate if candidate.exists() else file_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Read original content
        with open(file_path, 'r') as f:
            original_content = f.read()

        fixed_code = request.fixed_code
        if not fixed_code:
            if not ai_service.is_available():
                raise HTTPException(status_code=503, detail="AI service not available")

            vulnerability_data = {
                "check_id": vuln.check_id,
                "check_name": vuln.check_name,
                "description": vuln.description,
                "line_number": vuln.line_number
            }

            result = ai_service.suggest_fix_for_vulnerability(
                vulnerability=vulnerability_data,
                file_content=original_content,
                file_path=vuln.file_path
            )

            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate fix"))

            fixed_code = result.get("fixed_code", original_content)

        # Derive upload_id and relative file path for versioning
        # Normalize to project-level upload_id and basename path to keep history consistent
        upload_id = f"project_{vuln.scan.project_id}"
        rel_path = Path(vuln.file_path).name

        # Record file versions: ensure original is stored, then store fixed
        import hashlib
        project_id = vuln.scan.project_id

        def get_next_version(db_session, up_id, path):
            if not up_id:
                return 1
            latest = (
                db_session.query(FileVersion)
                .filter(FileVersion.upload_id == up_id, FileVersion.file_path == path)
                .order_by(FileVersion.version_number.desc())
                .first()
            )
            return (latest.version_number + 1) if latest else 1

        # If no previous versions, store original as v1
        vnum = get_next_version(db, upload_id, rel_path)
        if vnum == 1:
            orig_hash = hashlib.sha256(original_content.encode('utf-8')).hexdigest()
            db.add(FileVersion(
                upload_id=upload_id,
                project_id=project_id,
                file_path=rel_path,
                content=original_content,
                content_hash=orig_hash,
                version_number=1,
                scan_id=vuln.scan_id,
                change_summary="Initial upload",
                edited_by=None,
            ))
            db.commit()

        # Store fixed version as next version
        fixed_hash = hashlib.sha256(fixed_code.encode('utf-8')).hexdigest()
        db.add(FileVersion(
            upload_id=upload_id,
            project_id=project_id,
            file_path=rel_path,
            content=fixed_code,
            content_hash=fixed_hash,
            version_number=get_next_version(db, upload_id, rel_path),
            scan_id=None,
            change_summary=f"AI apply-fix for {vuln.check_id}",
            edited_by="ai",
        ))
        db.commit()

        # Write back to file on disk
        with open(file_path, 'w') as f:
            f.write(fixed_code)

        return ApplyFixResponse(success=True, file_path=str(file_path))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply fix: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply fix: {e}")

@router.post("/ai/analyze-vulnerability", response_model=AnalyzeVulnerabilityResponse)
async def analyze_vulnerability(
    request: AnalyzeVulnerabilityRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI analysis of vulnerability severity and impact

    **Example request:**
    ```json
    {
      "vulnerability_id": 123
    }
    ```
    """
    ai_service = AIService()

    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Please configure OPENAI_API_KEY"
        )

    # Get vulnerability
    vuln = db.query(Vulnerability).filter(Vulnerability.id == request.vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    try:
        result = ai_service.analyze_vulnerability_severity(
            check_id=vuln.check_id,
            check_name=vuln.check_name,
            resource_type=vuln.resource_type,
            description=vuln.description
        )

        return AnalyzeVulnerabilityResponse(**result)

    except Exception as e:
        logger.error(f"Failed to analyze vulnerability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/status")
async def get_ai_status():
    """Check if AI service is available"""
    ai_service = AIService()
    return {
        "available": ai_service.is_available(),
        "model": ai_service.model if ai_service.is_available() else None
    }
