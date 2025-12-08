"""
Policy Router - Using database for fast retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.database import get_db
from app.models.policy import Policy
from pydantic import BaseModel

router = APIRouter(prefix="/api/policies", tags=["Policies"])


# ============= Built-in Policies (from database) =============

@router.get("/built-in", response_model=List[Dict[str, Any]])
def get_builtin_policies(
    platform: Optional[str] = Query(None, description="Filter by platform: terraform, kubernetes, dockerfile"),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW, INFO"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in check_id or name"),
    db: Session = Depends(get_db)
):
    """
    Get all built-in Checkov policies from database.
    
    This is MUCH faster than parsing Checkov checks on every request.
    Policies are imported into database using scripts/import_policies.py
    """
    try:
        # Build query - only built-in policies
        query = db.query(Policy).filter(Policy.built_in == True)
        
        # Apply filters
        if platform:
            query = query.filter(Policy.platform == platform.lower())
        
        if severity:
            query = query.filter(Policy.severity == severity.upper())
        
        if category:
            query = query.filter(Policy.category.ilike(f"%{category}%"))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Policy.check_id.ilike(search_term)) | 
                (Policy.name.ilike(search_term))
            )
        
        # Order by platform, severity, check_id
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
                "built_in": True
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policies: {str(e)}")


@router.get("/stats")
def get_policy_stats(db: Session = Depends(get_db)):
    """Get statistics about policies in database"""
    try:
        from sqlalchemy import func
        
        # Total policies
        total = db.query(func.count(Policy.id)).filter(Policy.built_in == True).scalar()
        
        # By platform
        by_platform = db.query(
            Policy.platform,
            func.count(Policy.id).label('count')
        ).filter(Policy.built_in == True).group_by(Policy.platform).all()
        
        # By severity
        by_severity = db.query(
            Policy.severity,
            func.count(Policy.id).label('count')
        ).filter(Policy.built_in == True).group_by(Policy.severity).all()
        
        return {
            "total": total,
            "by_platform": {p: c for p, c in by_platform},
            "by_severity": {s: c for s, c in by_severity}
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/sync-from-checkov")
def sync_policies_from_checkov(db: Session = Depends(get_db)):
    """
    Sync built-in policies from Checkov into database.
    This should be run after Checkov updates or initially.
    """
    try:
        # Use direct import without instantiating registries
        from checkov.terraform.checks.resource.registry import resource_registry as tf_registry
        from checkov.kubernetes.checks.resource.registry import registry as k8s_registry
        
        synced_count = 0
        
        # Helper function to extract policy info
        def extract_check_info(check, platform):
            try:
                check_id = getattr(check, 'id', 'Unknown')
                name = getattr(check, 'name', 'Unknown')
                
                # Get category and map to severity
                categories = getattr(check, 'categories', [])
                category = categories[0].name if categories else 'GENERAL'
                
                # Map category to severity
                severity_map = {
                    'SECRETS': 'CRITICAL',
                    'IAM': 'HIGH',
                    'ENCRYPTION': 'HIGH',
                    'NETWORKING': 'MEDIUM',
                    'LOGGING': 'MEDIUM',
                    'BACKUP': 'MEDIUM',
                    'MONITORING': 'MEDIUM',
                    'CONVENTION': 'LOW',
                    'GENERAL': 'MEDIUM'
                }
                severity = severity_map.get(category, 'MEDIUM')
                
                # Get guideline
                guideline = getattr(check, 'guideline', None) or ''
                
                return {
                    'check_id': check_id,
                    'name': name,
                    'platform': platform,
                    'severity': severity,
                    'category': category,
                    'description': name,
                    'guideline': guideline
                }
            except Exception as e:
                print(f"Error extracting check info: {e}")
                return None
        
        # Sync Terraform policies
        for check in tf_registry.wildcard_checks:
            try:
                info = extract_check_info(check, 'terraform')
                if info and info['check_id'] != 'Unknown':
                    # Check if already exists
                    existing = db.query(Policy).filter(
                        Policy.check_id == info['check_id']
                    ).first()
                    
                    if not existing:
                        policy = Policy(
                            check_id=info['check_id'],
                            name=info['name'],
                            platform=info['platform'],
                            severity=info['severity'],
                            category=info['category'],
                            description=info['description'],
                            guideline=info['guideline'],
                            built_in=True
                        )
                        db.add(policy)
                        db.flush()  # Flush to catch duplicates early
                        synced_count += 1
            except Exception as e:
                db.rollback()
                print(f"Error syncing check {getattr(check, 'id', 'unknown')}: {e}")
                continue
        
        # Commit after wildcard checks
        db.commit()
        
        # Get resource-specific Terraform checks
        for resource_type, checks in tf_registry.checks.items():
            for check in checks:
                try:
                    info = extract_check_info(check, 'terraform')
                    if info and info['check_id'] != 'Unknown':
                        existing = db.query(Policy).filter(
                            Policy.check_id == info['check_id']
                        ).first()
                        
                        if not existing:
                            policy = Policy(
                                check_id=info['check_id'],
                                name=info['name'],
                                platform=info['platform'],
                                severity=info['severity'],
                                category=info['category'],
                                description=info['description'],
                                guideline=info['guideline'],
                                built_in=True
                            )
                            db.add(policy)
                            db.flush()  # Flush to catch duplicates early
                            synced_count += 1
                except Exception as e:
                    db.rollback()
                    print(f"Error syncing check {getattr(check, 'id', 'unknown')}: {e}")
                    continue
        
        # Commit after Terraform checks
        db.commit()
        
        # Sync Kubernetes policies
        for check in k8s_registry.wildcard_checks:
            try:
                info = extract_check_info(check, 'kubernetes')
                if info and info['check_id'] != 'Unknown':
                    existing = db.query(Policy).filter(
                        Policy.check_id == info['check_id']
                    ).first()
                    
                    if not existing:
                        policy = Policy(
                            check_id=info['check_id'],
                            name=info['name'],
                            platform=info['platform'],
                            severity=info['severity'],
                            category=info['category'],
                            description=info['description'],
                            guideline=info['guideline'],
                            built_in=True
                        )
                        db.add(policy)
                        db.flush()
                        synced_count += 1
            except Exception as e:
                db.rollback()
                print(f"Error syncing check {getattr(check, 'id', 'unknown')}: {e}")
                continue
        
        # Commit after wildcard checks
        db.commit()
        
        for resource_type, checks in k8s_registry.checks.items():
            for check in checks:
                try:
                    info = extract_check_info(check, 'kubernetes')
                    if info and info['check_id'] != 'Unknown':
                        existing = db.query(Policy).filter(
                            Policy.check_id == info['check_id']
                        ).first()
                        
                        if not existing:
                            policy = Policy(
                                check_id=info['check_id'],
                                name=info['name'],
                                platform=info['platform'],
                                severity=info['severity'],
                                category=info['category'],
                                description=info['description'],
                                guideline=info['guideline'],
                                built_in=True
                            )
                            db.add(policy)
                            db.flush()
                            synced_count += 1
                except Exception as e:
                    db.rollback()
                    print(f"Error syncing check {getattr(check, 'id', 'unknown')}: {e}")
                    continue
        
        # Final commit
        db.commit()
        
        # Final commit
        db.commit()
        
        return {
            "message": "Policies synced successfully",
            "synced_count": synced_count
        }
    
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to sync policies: {str(e)}")


# ============= Custom Policies =============

@router.get("/custom", response_model=List[Dict[str, Any]])
def get_custom_policies(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: Session = Depends(get_db)
):
    """Get all custom policies from database"""
    try:
        query = db.query(Policy).filter(Policy.built_in == False)
        
        if platform:
            query = query.filter(Policy.platform == platform.lower())
        
        policies = query.order_by(Policy.platform, Policy.check_id).all()
        
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


class CreateCustomPolicyRequest(BaseModel):
    platform: str
    check_id: str
    name: str
    severity: str
    format: str  # 'python' or 'yaml'
    code: str


@router.post("/custom/create")
def create_custom_policy(request: CreateCustomPolicyRequest, db: Session = Depends(get_db)):
    """Create a new custom policy"""
    try:
        # Validate platform - All Checkov supported frameworks
        SUPPORTED_PLATFORMS = [
            'terraform', 'terraform_json', 'terraform_plan',
            'kubernetes', 'kustomize', 'helm',
            'dockerfile',
            'cloudformation', 'arm', 'bicep',
            'ansible',
            'serverless',
            'openapi',
            'github_actions', 'github_configuration',
            'gitlab_ci', 'gitlab_configuration',
            'azure_pipelines', 'circleci_pipelines', 'bitbucket_pipelines', 'argo_workflows',
            'bitbucket_configuration',
            'cdk',
            'json', 'yaml'
        ]
        if request.platform not in SUPPORTED_PLATFORMS:
            raise HTTPException(status_code=400, detail=f"Invalid platform. Supported: {', '.join(SUPPORTED_PLATFORMS)}")
        
        # Validate format
        if request.format not in ['python', 'yaml']:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        # Check if already exists in database
        existing = db.query(Policy).filter(
            Policy.check_id == request.check_id,
            Policy.built_in == False
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail=f"Policy {request.check_id} already exists")
        
        # Create file - Use Dashboard's custom_policies folder (respect CUSTOM_POLICIES_DIR env)
        import os
        default_path = Path(__file__).parent.parent.parent / "custom_policies"
        base_path = Path(os.getenv("CUSTOM_POLICIES_DIR", str(default_path)))
        platform_path = base_path / request.platform
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
            platform=request.platform.lower(),
            severity=request.severity.upper(),
            category='CUSTOM',
            description=request.name,
            file_path=str(file_path),
            built_in=False
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        return {
            "message": "Custom policy created successfully",
            "file_path": str(file_path),
            "check_id": request.check_id,
            "policy": {
                "check_id": policy.check_id,
                "name": policy.name,
                "platform": policy.platform,
                "severity": policy.severity,
                "built_in": False
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating custom policy: {str(e)}")


@router.delete("/custom/{check_id}")
def delete_custom_policy(check_id: str, platform: str, db: Session = Depends(get_db)):
    """Delete a custom policy"""
    try:
        # Find policy in database
        policy = db.query(Policy).filter(
            Policy.check_id == check_id,
            Policy.platform == platform.lower(),
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
