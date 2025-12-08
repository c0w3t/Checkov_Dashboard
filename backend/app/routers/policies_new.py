"""
Policy Configs Router - Using Database for fast retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel

from app.database import get_db
from app.models.policy_config import PolicyConfig
from app.models.policy import Policy
from app.schemas.policy_config import PolicyConfigCreate, PolicyConfigUpdate, PolicyConfigResponse

router = APIRouter(prefix="/api/policies", tags=["Policy Configurations"])


# ==================== Policy Retrieval (from Database) ====================

@router.get("/built-in", response_model=List[Dict[str, Any]])
def get_builtin_policies(
    platform: Optional[str] = Query(None, description="Filter by platform: terraform, kubernetes, dockerfile"),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW, INFO"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    Get all built-in Checkov policies from database
    
    This endpoint reads from database which is much faster than parsing Checkov on every request.
    Run 'python scripts/import_policies.py' to populate the database with policies.
    """
    try:
        # Build query
        query = db.query(Policy).filter(Policy.built_in == True)
        
        # Apply filters
        if platform:
            query = query.filter(Policy.platform == platform)
        
        if severity:
            query = query.filter(Policy.severity == severity.upper())
        
        if category:
            query = query.filter(Policy.category == category.upper())
        
        # Order by platform, then severity, then check_id
        policies = query.order_by(
            Policy.platform,
            Policy.severity,
            Policy.check_id
        ).all()
        
        # Convert to dict
        result = []
        for policy in policies:
            result.append({
                "check_id": policy.check_id,
                "name": policy.name,
                "platform": policy.platform,
                "severity": policy.severity,
                "category": policy.category,
                "description": policy.description,
                "guideline": policy.guideline,
                "guideline_url": policy.guideline_url,
                "built_in": True
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policies: {str(e)}")


@router.get("/custom", response_model=List[Dict[str, Any]])
def get_custom_policies(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: Session = Depends(get_db)
):
    """
    Get all custom policies from database
    """
    try:
        # Build query
        query = db.query(Policy).filter(Policy.built_in == False)
        
        if platform:
            query = query.filter(Policy.platform == platform)
        
        policies = query.order_by(Policy.platform, Policy.check_id).all()
        
        # Convert to dict
        result = []
        for policy in policies:
            result.append({
                "check_id": policy.check_id,
                "name": policy.name,
                "platform": policy.platform,
                "severity": policy.severity,
                "category": policy.category,
                "description": policy.description,
                "file_path": policy.file_path,
                "built_in": False
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load custom policies: {str(e)}")


# ==================== Custom Policy Management ====================

class CreateCustomPolicyRequest(BaseModel):
    platform: str
    check_id: str
    name: str
    severity: str
    format: str  # 'python' or 'yaml'
    code: str


@router.post("/custom/create")
def create_custom_policy(request: CreateCustomPolicyRequest, db: Session = Depends(get_db)):
    """Create a new custom policy file and store in database"""
    try:
        # Validate platform
        if request.platform not in ['terraform', 'kubernetes', 'dockerfile']:
            raise HTTPException(status_code=400, detail="Invalid platform")
        
        # Validate format
        if request.format not in ['python', 'yaml']:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        # Check if policy already exists in database
        existing = db.query(Policy).filter(Policy.check_id == request.check_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Policy {request.check_id} already exists")
        
        # Save to filesystem (respect CUSTOM_POLICIES_DIR env)
        import os
        default_path = Path(__file__).parent.parent.parent.parent / "custom_policies"
        base_path = Path(os.getenv("CUSTOM_POLICIES_DIR", str(default_path)))
        platform_path = base_path / request.platform
        
        # Create directory if not exists
        platform_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py if not exists
        init_file = platform_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
        
        # Determine file extension
        ext = '.py' if request.format == 'python' else '.yaml'
        file_path = platform_path / f"{request.check_id}{ext}"
        
        # Write the code to file
        file_path.write_text(request.code)
        
        # Save to database
        policy = Policy(
            check_id=request.check_id,
            name=request.name,
            platform=request.platform,
            severity=request.severity.upper(),
            category='CUSTOM',
            file_path=str(file_path),
            code=request.code,
            built_in=False
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        return {
            "message": "Custom policy created successfully",
            "file_path": str(file_path),
            "check_id": request.check_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating custom policy: {str(e)}")


@router.delete("/custom/{check_id}")
def delete_custom_policy(check_id: str, platform: str, db: Session = Depends(get_db)):
    """Delete a custom policy file and from database"""
    try:
        # Find policy in database
        policy = db.query(Policy).filter(
            Policy.check_id == check_id,
            Policy.platform == platform,
            Policy.built_in == False
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Delete file if exists
        if policy.file_path:
            file_path = Path(policy.file_path)
            if file_path.exists():
                file_path.unlink()
        
        # Delete from database
        db.delete(policy)
        db.commit()
        
        return {"message": "Custom policy deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting custom policy: {str(e)}")


# ==================== Policy Sync/Refresh ====================

@router.post("/sync")
def sync_policies_from_checkov(db: Session = Depends(get_db)):
    """
    Sync policies from Checkov into database
    This is useful to refresh built-in policies when Checkov is updated
    """
    try:
        import sys
        from pathlib import Path
        
        # Import the sync script
        script_path = Path(__file__).parent.parent.parent / "scripts" / "import_policies.py"
        
        # Run sync
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Sync failed: {result.stderr}")
        
        # Count policies
        total = db.query(Policy).count()
        builtin = db.query(Policy).filter(Policy.built_in == True).count()
        custom = db.query(Policy).filter(Policy.built_in == False).count()
        
        return {
            "message": "Policies synced successfully",
            "total": total,
            "built_in": builtin,
            "custom": custom
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing policies: {str(e)}")


@router.get("/stats")
def get_policy_stats(db: Session = Depends(get_db)):
    """Get statistics about policies in database"""
    try:
        stats = {
            "total": db.query(Policy).count(),
            "built_in": db.query(Policy).filter(Policy.built_in == True).count(),
            "custom": db.query(Policy).filter(Policy.built_in == False).count(),
            "by_platform": {},
            "by_severity": {}
        }
        
        # Count by platform
        from sqlalchemy import func
        platforms = db.query(
            Policy.platform,
            func.count(Policy.id)
        ).group_by(Policy.platform).all()
        
        for platform, count in platforms:
            stats["by_platform"][platform] = count
        
        # Count by severity
        severities = db.query(
            Policy.severity,
            func.count(Policy.id)
        ).group_by(Policy.severity).all()
        
        for severity, count in severities:
            stats["by_severity"][severity] = count
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


# ==================== Policy Configurations (per project) ====================

@router.get("/", response_model=List[PolicyConfigResponse])
def get_policy_configs(
    project_id: int = None,
    policy_type: str = None,
    enabled: bool = None,
    db: Session = Depends(get_db)
):
    """Get all policy configurations with optional filters"""
    query = db.query(PolicyConfig)
    
    if project_id:
        query = query.filter(PolicyConfig.project_id == project_id)
    if policy_type:
        query = query.filter(PolicyConfig.policy_type == policy_type)
    if enabled is not None:
        query = query.filter(PolicyConfig.enabled == enabled)
    
    return query.all()


@router.get("/config/{policy_id}", response_model=PolicyConfigResponse)
def get_policy_config(policy_id: int, db: Session = Depends(get_db)):
    """Get a specific policy configuration"""
    policy = db.query(PolicyConfig).filter(PolicyConfig.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy configuration not found")
    return policy


@router.post("/config", response_model=PolicyConfigResponse)
def create_policy_config(policy: PolicyConfigCreate, db: Session = Depends(get_db)):
    """Create a new policy configuration"""
    db_policy = PolicyConfig(**policy.dict())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy


@router.put("/config/{policy_id}", response_model=PolicyConfigResponse)
def update_policy_config(
    policy_id: int,
    policy_update: PolicyConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update a policy configuration"""
    db_policy = db.query(PolicyConfig).filter(PolicyConfig.id == policy_id).first()
    if not db_policy:
        raise HTTPException(status_code=404, detail="Policy configuration not found")
    
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_policy, field, value)
    
    db.commit()
    db.refresh(db_policy)
    return db_policy


@router.delete("/config/{policy_id}")
def delete_policy_config(policy_id: int, db: Session = Depends(get_db)):
    """Delete a policy configuration"""
    db_policy = db.query(PolicyConfig).filter(PolicyConfig.id == policy_id).first()
    if not db_policy:
        raise HTTPException(status_code=404, detail="Policy configuration not found")
    
    db.delete(db_policy)
    db.commit()
    return {"message": "Policy configuration deleted successfully"}


@router.post("/bulk-toggle")
def bulk_toggle_policies(
    project_id: int,
    policy_type: str,
    enabled: bool,
    db: Session = Depends(get_db)
):
    """Enable or disable all policies for a project and type"""
    policies = db.query(PolicyConfig).filter(
        PolicyConfig.project_id == project_id,
        PolicyConfig.policy_type == policy_type
    ).all()
    
    for policy in policies:
        policy.enabled = enabled
    
    db.commit()
    return {"message": f"Updated {len(policies)} policies", "count": len(policies)}
