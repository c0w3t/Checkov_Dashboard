"""
Import Checkov Built-in Policies into Database

This script loads all built-in policies from Checkov and stores them in the database
for faster retrieval.

Usage:
    python scripts/import_policies.py
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.policy import Policy
from app.severity_mapping import get_severity_for_check
import logging
import json


# Import Checkov registries
# For Terraform, the package exposes a pre-instantiated registry object (`resource_registry`),
# so import that instead of the Registry class (which requires a report_type argument).
from checkov.terraform.checks.resource.registry import resource_registry as terraform_registry
from checkov.kubernetes.checks.resource.registry import registry as k8s_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Map custom policies to their actual categories
CUSTOM_POLICY_CATEGORIES = {
    # Dockerfile policies
    'CKV_CUSTOM_11': 'SUPPLY_CHAIN',
    'CKV_CUSTOM_12': 'SUPPLY_CHAIN',
    'CKV_CUSTOM_13': 'NETWORKING',
    'CKV_CUSTOM_14': 'SUPPLY_CHAIN',
    'CKV_CUSTOM_15': 'CONVENTION',
    'CKV_CUSTOM_16': 'CONVENTION',
    'CKV_CUSTOM_17': 'SECRETS',
    'CKV_CUSTOM_18': 'IAM',
    'CKV_CUSTOM_19': 'IAM',
    'CKV_CUSTOM_20': 'GENERAL_SECURITY',

    # Kubernetes policies
    'CKV_K8S_CUSTOM_10': 'KUBERNETES',
    'CKV_K8S_CUSTOM_11': 'KUBERNETES',
    'CKV_K8S_CUSTOM_12': 'KUBERNETES',
    'CKV_K8S_CUSTOM_13': 'KUBERNETES',
    'CKV_K8S_CUSTOM_14': 'GENERAL_SECURITY',
    'CKV_K8S_CUSTOM_15': 'KUBERNETES',
    'CKV_K8S_CUSTOM_16': 'KUBERNETES',
    'CKV_K8S_CUSTOM_17': 'KUBERNETES',
    'CKV_K8S_CUSTOM_18': 'KUBERNETES',
    'CKV_K8S_CUSTOM_19': 'KUBERNETES',

    # Terraform policies
    'CKV_TF_CUSTOM_10': 'ENCRYPTION',
    'CKV_TF_CUSTOM_11': 'BACKUP_AND_RECOVERY',
    'CKV_TF_CUSTOM_12': 'LOGGING',
    'CKV_TF_CUSTOM_13': 'ENCRYPTION',
    'CKV_TF_CUSTOM_14': 'IAM',
    'CKV_TF_CUSTOM_15': 'NETWORKING',
    'CKV_TF_CUSTOM_16': 'ENCRYPTION',
    'CKV_TF_CUSTOM_17': 'BACKUP_AND_RECOVERY',
    'CKV_TF_CUSTOM_18': 'LOGGING',
    'CKV_TF_CUSTOM_19': 'NETWORKING',
}

def update_custom_policy_severities(db: Session) -> int:
    """Update severity for all custom policies using mapping"""
    logger.info("Updating custom policy severities...")
    updated_count = 0

    # Get all custom policies
    custom_policies = db.query(Policy).filter(Policy.built_in == False).all()

    logger.info(f"Found {len(custom_policies)} custom policies in database")

    for policy in custom_policies:
        check_id = policy.check_id

        # Get the correct category for this policy
        category = CUSTOM_POLICY_CATEGORIES.get(check_id, policy.category)

        # Calculate new severity using severity_mapping.py
        new_severity = get_severity_for_check(check_id, category)

        # Update if different
        if policy.severity != new_severity or policy.category != category:
            old_severity = policy.severity
            old_category = policy.category
            policy.severity = new_severity
            policy.category = category
            logger.info(f"  {check_id:25} | {old_category:20} -> {category:20} | {old_severity:8} → {new_severity:8}")
            updated_count += 1
        else:
            logger.info(f"  {check_id:25} | {category:20} | {policy.severity:8} (no change)")

    db.commit()
    logger.info(f"Updated {updated_count} custom policies")
    return updated_count

def import_terraform_policies(db: Session) -> int:
    """Import Terraform policies from Checkov"""
    logger.info("Importing Terraform policies...")
    count = 0
    
    try:
        # Use the pre-instantiated terraform_registry provided by Checkov
        tf_reg = terraform_registry
        
        # Get wildcard checks
        for check in tf_reg.wildcard_checks:
            try:
                check_id = check.id
                name = check.name
                categories = getattr(check, 'categories', [])
                category = categories[0].name if categories else 'GENERAL'
                # Use new severity mapping
                severity = get_severity_for_check(check_id, category)
                
                # Check if policy already exists
                existing = db.query(Policy).filter(Policy.check_id == check_id).first()
                if existing:
                    # Update existing policy
                    existing.name = name
                    existing.platform = 'terraform'
                    existing.severity = severity
                    existing.category = category
                    existing.built_in = True
                else:
                    # Create new policy
                    policy = Policy(
                        check_id=check_id,
                        name=name,
                        platform='terraform',
                        severity=severity,
                        category=category,
                        description=getattr(check, 'guideline', name),
                        guideline=getattr(check, 'guideline', ''),
                        built_in=True
                    )
                    db.add(policy)
                
                count += 1
            except Exception as e:
                logger.warning(f"Error importing Terraform check {getattr(check, 'id', 'unknown')}: {str(e)}")
                continue
        
        # Get resource-specific checks
        for resource_type, checks in tf_reg.checks.items():
            for check in checks:
                try:
                    check_id = check.id
                    name = check.name
                    categories = getattr(check, 'categories', [])
                    category = categories[0].name if categories else 'GENERAL'
                    severity = get_severity_for_check(check_id, category)
                    
                    # Check if policy already exists (avoid duplicates from wildcard)
                    existing = db.query(Policy).filter(Policy.check_id == check_id).first()
                    if existing:
                        continue  # Skip if already added
                    
                    # Create new policy
                    policy = Policy(
                        check_id=check_id,
                        name=name,
                        platform='terraform',
                        severity=severity,
                        category=category,
                        description=getattr(check, 'guideline', name),
                        guideline=getattr(check, 'guideline', ''),
                        built_in=True
                    )
                    db.add(policy)
                    count += 1
                except Exception as e:
                    logger.warning(f"Error importing Terraform check {getattr(check, 'id', 'unknown')}: {str(e)}")
                    continue
        
        db.commit()
        logger.info(f"Imported {count} Terraform policies")
        return count
    
    except Exception as e:
        logger.error(f"Error importing Terraform policies: {str(e)}")
        db.rollback()
        return 0


def import_kubernetes_policies(db: Session) -> int:
    """Import Kubernetes policies from Checkov"""
    logger.info("Importing Kubernetes policies...")
    count = 0
    
    try:
        # Get wildcard checks
        for check in k8s_registry.wildcard_checks:
            try:
                check_id = check.id
                name = check.name
                categories = getattr(check, 'categories', [])
                category = categories[0].name if categories else 'GENERAL'
                # Use new severity mapping
                severity = get_severity_for_check(check_id, category)
                
                # Check if policy already exists
                existing = db.query(Policy).filter(Policy.check_id == check_id).first()
                if existing:
                    continue  # Skip if already added
                
                # Create new policy
                policy = Policy(
                    check_id=check_id,
                    name=name,
                    platform='kubernetes',
                    severity=severity,
                    category=category,
                    description=getattr(check, 'guideline', name),
                    guideline=getattr(check, 'guideline', ''),
                    built_in=True
                )
                db.add(policy)
                count += 1
            except Exception as e:
                logger.warning(f"Error importing Kubernetes check {getattr(check, 'id', 'unknown')}: {str(e)}")
                continue
        
        # Get resource-specific checks
        for resource_type, checks in k8s_registry.checks.items():
            for check in checks:
                try:
                    check_id = check.id
                    name = check.name
                    categories = getattr(check, 'categories', [])
                    category = categories[0].name if categories else 'GENERAL'
                    severity = get_severity_for_check(check_id, category)
                    
                    # Check if policy already exists (avoid duplicates)
                    existing = db.query(Policy).filter(Policy.check_id == check_id).first()
                    if existing:
                        continue  # Skip if already added
                    
                    # Create new policy
                    policy = Policy(
                        check_id=check_id,
                        name=name,
                        platform='kubernetes',
                        severity=severity,
                        category=category,
                        description=getattr(check, 'guideline', name),
                        guideline=getattr(check, 'guideline', ''),
                        built_in=True
                    )
                    db.add(policy)
                    count += 1
                except Exception as e:
                    logger.warning(f"Error importing Kubernetes check {getattr(check, 'id', 'unknown')}: {str(e)}")
                    continue
        
        db.commit()
        logger.info(f"Imported {count} Kubernetes policies")
        return count
    
    except Exception as e:
        logger.error(f"Error importing Kubernetes policies: {str(e)}")
        db.rollback()
        return 0


def import_custom_policies(db: Session) -> int:
    """Import custom policies from filesystem"""
    logger.info("Importing custom policies...")
    count = 0

    # Prefer CUSTOM_POLICIES_DIR environment variable if set (allows different envs)
    env_dir = os.getenv('CUSTOM_POLICIES_DIR')
    if env_dir:
        custom_policies_dir = Path(env_dir)
        logger.info(f"Using CUSTOM_POLICIES_DIR from env: {custom_policies_dir}")
    else:
        # Fallback to repository relative path
        custom_policies_dir = Path(__file__).parent.parent.parent.parent / "custom_policies"
        logger.info(f"No CUSTOM_POLICIES_DIR env var; using repo path: {custom_policies_dir}")

    # Normalize path
    custom_policies_dir = custom_policies_dir.expanduser().resolve() if custom_policies_dir.exists() else custom_policies_dir.expanduser()

    if not custom_policies_dir.exists():
        logger.info(f"No custom_policies directory found at: {custom_policies_dir}")
        return 0
    
    for platform_dir in custom_policies_dir.iterdir():
        if not platform_dir.is_dir() or platform_dir.name == '__pycache__':
            continue
        
        platform = platform_dir.name
        if platform == 'kubernets':  # Handle typo in directory name
            platform = 'kubernetes'
        
        for policy_file in platform_dir.glob("*.py"):
            if policy_file.name.startswith('__'):
                continue
            
            try:
                # Read file content
                code = policy_file.read_text()
                
                # Extract check_id from filename
                check_id = policy_file.stem
                
                # Try to extract name from code
                name = check_id  # Default to check_id
                for line in code.split('\n'):
                    if 'name = ' in line and '"' in line:
                        name = line.split('"')[1]
                        break
                
                # Check if policy already exists
                existing = db.query(Policy).filter(Policy.check_id == check_id).first()
                if existing:
                    # Update existing custom policy
                    existing.name = name
                    existing.platform = platform
                    existing.file_path = str(policy_file)
                    existing.code = code
                    existing.built_in = False
                else:
                    # Create new custom policy
                    policy = Policy(
                        check_id=check_id,
                        name=name,
                        platform=platform,
                        severity='MEDIUM',  # Default severity for custom
                        category='CUSTOM',
                        file_path=str(policy_file),
                        code=code,
                        built_in=False
                    )
                    db.add(policy)
                
                count += 1
            except Exception as e:
                logger.warning(f"Error importing custom policy {policy_file}: {str(e)}")
                continue
    
    db.commit()
    logger.info(f"Imported {count} custom policies")
    return count


def main():
    """Main function to import all policies"""
    logger.info("Starting policy import...")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Import policies
        tf_count = import_terraform_policies(db)
        k8s_count = import_kubernetes_policies(db)
        custom_count = import_custom_policies(db)

        # Sync severities/categories for custom policies using mapping
        updated_custom = update_custom_policy_severities(db)
        
        total = tf_count + k8s_count + custom_count
        
        logger.info("=" * 50)
        logger.info(f"Policy import completed!")
        logger.info(f"Terraform policies: {tf_count}")
        logger.info(f"Kubernetes policies: {k8s_count}")
        logger.info(f"Custom policies: {custom_count}")
        logger.info(f"Custom policies updated: {updated_custom}")
        logger.info(f"Total policies: {total}")
        logger.info("=" * 50)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
