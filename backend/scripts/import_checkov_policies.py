"""
Import all Checkov policies by parsing checkov --list output
"""
import sys
import os
import subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.policy import Policy
from app.severity_mapping import get_severity_for_check


# Severity is determined via centralized mapping logic
def determine_severity(check_id, name):
    return get_severity_for_check(check_id)


def parse_checkov_list():
    """Parse checkov --list output"""
    print("🔍 Running checkov --list...")
    
    try:
        result = subprocess.run(
            ['checkov', '--list'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        policies = []
        lines = result.stdout.split('\n')
        
        for line in lines:
            if not line.strip() or not line.startswith('|'):
                continue
            
            if '---' in line or 'Type' in line:
                continue
            
            parts = [p.strip() for p in line.split('|')]
            
            if len(parts) < 8:
                continue
            
            try:
                check_id = parts[2]
                if not check_id or not check_id.startswith('CKV'):
                    continue
                
                name = parts[5]
                iac = parts[6]
                link = parts[7] if len(parts) > 7 else ''
                
                platform = map_iac(iac)
                if not platform:
                    continue
                
                # Prefer centralized severity mapping; category is unknown from --list, so omitted
                severity = get_severity_for_check(check_id)
                
                policies.append({
                    'check_id': check_id,
                    'name': name,
                    'platform': platform,
                    'severity': severity,
                    'category': None,
                    'description': name,
                    'guideline': None,
                    'guideline_url': link if link.startswith('http') else None,
                    'supported_resources': None,
                    'built_in': True
                })
            except:
                continue
        
        return policies
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def map_iac(iac):
    """Map IaC to platform"""
    m = {
        'Terraform': 'terraform',
        'CloudFormation': 'cloudformation',
        'Cloudformation': 'cloudformation',
        'Kubernetes': 'kubernetes',
        'Dockerfile': 'dockerfile',
        'dockerfile': 'dockerfile',
        'ARM': 'arm',
        'arm': 'arm',
        'Serverless': 'serverless',
        'Helm': 'helm',
        'Ansible': 'ansible',
        'Secrets': 'secrets',
        'secrets': 'secrets',
        'GitHub Actions': 'github_actions',
        'GitLab CI': 'gitlab_ci',
        'CircleCI': 'circleci_pipelines',
        'Azure Pipelines': 'azure_pipelines',
        'Argo Workflows': 'argo_workflows',
        'Bicep': 'bicep',
        'OpenAPI': 'openapi',
        'Kustomize': 'kustomize',
        'bitbucket_configuration': 'bitbucket_configuration',
        'bitbucket_pipelines': 'bitbucket_pipelines',
        'github_configuration': 'github_configuration',
        'gitlab_configuration': 'gitlab_configuration',
    }
    return m.get(iac, None)


def import_policies(db: Session):
    policies = parse_checkov_list()
    
    if not policies:
        print("❌ No policies!")
        return
    
    # Remove dups
    unique = {}
    for p in policies:
        if p['check_id'] not in unique:
            unique[p['check_id']] = p
    
    policies = list(unique.values())
    
    # Stats
    by_p = {}
    for p in policies:
        by_p[p['platform']] = by_p.get(p['platform'], 0) + 1
    
    print(f"\n📊 Total: {len(policies)}")
    print("\n📋 By platform:")
    for plat, cnt in sorted(by_p.items(), key=lambda x: x[1], reverse=True):
        print(f"  {plat:25s} {cnt:4d}")
    
    # Import
    print("\n💾 Importing...")
    imp = upd = err = 0
    
    for p in policies:
        try:
            ex = db.query(Policy).filter(
                Policy.check_id == p['check_id'],
                Policy.built_in == True
            ).first()
            
            if ex:
                for k, v in p.items():
                    if k != 'check_id' and v:
                        setattr(ex, k, v)
                upd += 1
            else:
                db.add(Policy(**p))
                imp += 1
            
            if (imp + upd) % 100 == 0:
                db.commit()
                print(f"  ... {imp + upd}/{len(policies)}")
        except Exception as e:
            err += 1
            if err <= 3:
                print(f"⚠️ {p['check_id']}: {e}")
    
    db.commit()
    print(f"\n✅ Imported: {imp}, Updated: {upd}, Errors: {err}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        import_policies(db)
    finally:
        db.close()
