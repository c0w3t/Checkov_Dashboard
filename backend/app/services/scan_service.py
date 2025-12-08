"""
Scan Service - Handles Checkov scan execution
"""
import subprocess
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.models.vulnerability import Vulnerability, SeverityLevel
from app.models.project import Project
from app.severity_mapping import get_severity_for_check
from app.services.email_service import EmailService

class ScanService:
    def __init__(self):
        self.checkov_path = "checkov"  # Assumes checkov is in PATH
        # Use Dashboard's custom_policies folder
        default_path = str(Path(__file__).parent.parent.parent / "custom_policies")
        self.custom_policies_dir = os.getenv("CUSTOM_POLICIES_DIR", default_path)
        # Email service for notifications
        self.email_service = EmailService()
    
    async def execute_scan(self, scan_id: int, db: Session):
        """Execute Checkov scan"""
        try:
            # Get scan and project
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                return
            
            project = db.query(Project).filter(Project.id == scan.project_id).first()
            if not project:
                scan.status = "failed"
                scan.error_message = "Project not found"
                db.commit()
                return
            
            # Update scan status
            scan.status = "running"
            db.commit()
            
            # Prepare checkov command
            framework_map = {
                "terraform": "terraform",
                "kubernetes": "kubernetes",
                "dockerfile": "dockerfile"
            }
            
            framework = framework_map.get(project.framework, "terraform")
            
            # Build command
            cmd = [
                self.checkov_path,
                "-d", project.repository_url or "/tmp",
                "--framework", framework,
                "--external-checks-dir", f"{self.custom_policies_dir}/{project.framework}",
                "-o", "json",
                "--quiet"
            ]
            
            # Execute checkov
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            # Parse results
            output_data = json.loads(result.stdout) if result.stdout else {}
            
            # Update scan with results
            scan.total_checks = output_data.get("summary", {}).get("passed", 0) + \
                              output_data.get("summary", {}).get("failed", 0) + \
                              output_data.get("summary", {}).get("skipped", 0)
            scan.passed_checks = output_data.get("summary", {}).get("passed", 0)
            scan.failed_checks = output_data.get("summary", {}).get("failed", 0)
            scan.skipped_checks = output_data.get("summary", {}).get("skipped", 0)
            scan.status = "completed"
            scan.completed_at = datetime.utcnow()
            scan.scan_metadata = output_data.get("summary", {})
            
            # Store vulnerabilities
            self._store_vulnerabilities(scan_id, output_data, db)
            
            db.commit()
            
        except subprocess.TimeoutExpired:
            scan.status = "failed"
            scan.error_message = "Scan timed out after 10 minutes"
            scan.completed_at = datetime.utcnow()
            db.commit()
            # Send failure notification
            try:
                self.email_service.send_scan_failed_alert(db, scan_id)
            except Exception as email_error:
                print(f"⚠️ Failed to send failure notification: {email_error}")
        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            db.commit()
            # Send failure notification
            try:
                self.email_service.send_scan_failed_alert(db, scan_id)
            except Exception as email_error:
                print(f"⚠️ Failed to send failure notification: {email_error}")
    
    def _detect_file_framework(self, filepath: str) -> str:
        """Detect framework based on file extension and content"""
        filename = os.path.basename(filepath).lower()
        fullpath = filepath.lower()
        
        # Dockerfile detection
        if filename == 'dockerfile' or filename.startswith('dockerfile.'):
            return 'dockerfile'
        
        # Terraform detection
        if filename.endswith('.tf') or filename.endswith('.tfvars'):
            return 'terraform'
        if filename.endswith('.tf.json'):
            return 'terraform_json'
        
        # Bicep
        if filename.endswith('.bicep'):
            return 'bicep'
        
        # ARM Templates
        if filename.endswith('.json') and 'template' in filename:
            return 'arm'
        
        # GitHub Actions
        if '.github/workflows' in fullpath:
            return 'github_actions'
        
        # GitLab CI
        if '.gitlab-ci' in filename:
            return 'gitlab_ci'
        
        # Azure Pipelines
        if 'azure-pipelines' in filename:
            return 'azure_pipelines'
        
        # CircleCI
        if '.circleci' in fullpath:
            return 'circleci_pipelines'
        
        # Bitbucket Pipelines
        if 'bitbucket-pipelines' in filename:
            return 'bitbucket_pipelines'
        
        # Argo Workflows
        if 'argo' in filename and (filename.endswith('.yaml') or filename.endswith('.yml')):
            return 'argo_workflows'
        
        # YAML/Kubernetes detection
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(200)  # Read first 200 chars
                    # Kubernetes
                    if 'apiVersion' in content and 'kind' in content:
                        return 'kubernetes'
                    # Helm
                    if 'chart.yaml' in filename or 'values.yaml' in filename:
                        return 'helm'
                    # Kustomize
                    if 'kustomization.yaml' in filename:
                        return 'kustomize'
                    # Ansible
                    if 'ansible' in filename or 'playbook' in filename:
                        return 'ansible'
                    # CloudFormation
                    if 'AWSTemplateFormatVersion' in content or 'Resources:' in content:
                        return 'cloudformation'
                    # Serverless
                    if 'serverless' in filename:
                        return 'serverless'
                    # OpenAPI
                    if 'openapi' in content.lower() or 'swagger' in content.lower():
                        return 'openapi'
            except:
                pass
            return 'kubernetes'  # Default for YAML
        
        # CloudFormation JSON
        if filename.endswith('.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(500)
                    if 'AWSTemplateFormatVersion' in content or 'AWS::CloudFormation' in content:
                        return 'cloudformation'
            except:
                pass
            return 'json'
        
        return 'terraform'  # Default
    
    def _get_files_to_scan(self, upload_path: str) -> dict:
        """Get list of files grouped by framework"""
        files_by_framework = {}
        
        if os.path.isfile(upload_path):
            # Single file
            framework = self._detect_file_framework(upload_path)
            if framework not in files_by_framework:
                files_by_framework[framework] = []
            files_by_framework[framework].append(upload_path)
        else:
            # Directory - scan all files
            for root, dirs, files in os.walk(upload_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    framework = self._detect_file_framework(filepath)
                    if framework not in files_by_framework:
                        files_by_framework[framework] = []
                    files_by_framework[framework].append(filepath)
        
        # Remove empty frameworks
        return {k: v for k, v in files_by_framework.items() if v}
    
    async def execute_scan_on_upload(self, scan_id: int, upload_path: str, framework: str, db: Session):
        """Execute Checkov scan on uploaded files with auto-detection"""
        try:
            # Get scan
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                return
            
            # Update scan status
            scan.status = "running"
            scan.started_at = datetime.utcnow()
            db.commit()
            
            # Get files grouped by framework
            files_by_framework = self._get_files_to_scan(upload_path)
            
            if not files_by_framework:
                scan.status = "failed"
                scan.error_message = "No scannable files found"
                scan.completed_at = datetime.utcnow()
                db.commit()
                return
            
            # Aggregate results from all frameworks
            all_results = {
                "summary": {"passed": 0, "failed": 0, "skipped": 0},
                "results": {"failed_checks": []}
            }
            
            # Scan each framework separately
            for fw, files in files_by_framework.items():
                print(f"Scanning {len(files)} {fw} files...")
                
                for file_path in files:
                    # Verify file exists and get size
                    if not os.path.exists(file_path):
                        print(f"⚠️  File not found: {file_path}")
                        continue

                    file_size = os.path.getsize(file_path)
                    file_mtime = os.path.getmtime(file_path)
                    print(f"📄 Scanning: {file_path} (size: {file_size} bytes, modified: {file_mtime})")

                    # Debug: Show first 100 chars of file content
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            preview = f.read(100).replace('\n', ' ')
                            print(f"   Preview: {preview}...")
                    except:
                        pass

                    # Build checkov command for each file
                    cmd = [
                        self.checkov_path,
                        "-f", file_path,
                        "--framework", fw,
                        "-o", "json",
                        "--quiet",
                        "--compact"
                    ]

                    # Add custom policies if available
                    custom_policy_path = f"{self.custom_policies_dir}/{fw}"
                    if os.path.exists(custom_policy_path):
                        cmd.extend(["--external-checks-dir", custom_policy_path])

                    print(f"🔧 Checkov command: {' '.join(cmd)}")

                    try:
                        # Execute checkov
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minutes per file
                        )

                        # Log stderr if any
                        if result.stderr:
                            print(f"⚠️  Checkov stderr: {result.stderr[:200]}")
                        
                        # Parse results
                        if result.stdout:
                            try:
                                output_data = json.loads(result.stdout)
                                
                                # Debug logging
                                print(f"✅ Parsed JSON for {file_path}")
                                print(f"   Summary: {output_data.get('summary', {})}")
                                
                                # Aggregate summary
                                summary = output_data.get("summary", {})
                                all_results["summary"]["passed"] += summary.get("passed", 0)
                                all_results["summary"]["failed"] += summary.get("failed", 0)
                                all_results["summary"]["skipped"] += summary.get("skipped", 0)
                                
                                # Collect failed checks
                                failed = output_data.get("results", {}).get("failed_checks", [])
                                print(f"   Failed checks: {len(failed)}")
                                all_results["results"]["failed_checks"].extend(failed)
                                
                            except json.JSONDecodeError as e:
                                print(f"❌ Failed to parse JSON for {file_path}: {e}")
                    
                    except subprocess.TimeoutExpired:
                        print(f"Timeout scanning {file_path}")
                        continue
                    except Exception as e:
                        print(f"Error scanning {file_path}: {e}")
                        continue
            
            # Update scan with aggregated results
            summary = all_results["summary"]
            scan.total_checks = summary["passed"] + summary["failed"] + summary["skipped"]
            scan.passed_checks = summary["passed"]
            scan.failed_checks = summary["failed"]
            scan.skipped_checks = summary["skipped"]
            scan.status = "completed"
            scan.completed_at = datetime.utcnow()
            scan.scan_metadata = {
                "upload_path": upload_path,
                "summary": summary,
                "frameworks_scanned": list(files_by_framework.keys()),
                "total_files": sum(len(f) for f in files_by_framework.values())
            }
            
            # Store vulnerabilities
            self._store_vulnerabilities(scan_id, all_results, db)
            
            db.commit()
            print(f"✅ Scan completed: {scan.passed_checks} passed, {scan.failed_checks} failed")
            
        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            db.commit()
            print(f"❌ Scan failed: {e}")
            # Send failure notification
            try:
                self.email_service.send_scan_failed_alert(db, scan_id)
            except Exception as email_error:
                print(f"⚠️ Failed to send failure notification: {email_error}")
    
    def _generate_vulnerability_hash(self, check_id: str, file_path: str, line_number: int, resource_name: str) -> str:
        """Generate unique hash for vulnerability tracking across scans"""
        hash_input = f"{check_id}|{file_path}|{line_number}|{resource_name}"
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()

    def _store_vulnerabilities(self, scan_id: int, output_data: dict, db: Session):
        """Store vulnerabilities from scan results with fix tracking"""
        failed_checks = output_data.get("results", {}).get("failed_checks", [])

        print(f"📝 Storing {len(failed_checks)} vulnerabilities for scan {scan_id}")

        # Get current scan details for project tracking
        current_scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not current_scan:
            return

        # Get all current vulnerabilities detected in this scan (for tracking fixes)
        current_vuln_hashes = set()
        
        severity_map = {
            "CRITICAL": SeverityLevel.CRITICAL,
            "HIGH": SeverityLevel.HIGH,
            "MEDIUM": SeverityLevel.MEDIUM,
            "LOW": SeverityLevel.LOW,
            "INFO": SeverityLevel.INFO
        }
        
        for idx, check in enumerate(failed_checks):
            try:
                if idx == 0:  # Debug first vulnerability
                    print(f"🔍 First check keys: {list(check.keys())}")
                    print(f"🔍 Guideline: {check.get('guideline')}")
                    print(f"🔍 Code block type: {type(check.get('code_block'))}")
                    print(f"🔍 Details type: {type(check.get('details'))}")
                    print(f"🔍 File line range: {check.get('file_line_range')}")
                
                # Get severity using our mapping (Checkov returns null without API key)
                check_id = check.get("check_id", "UNKNOWN")

                # Try to get category from check result
                category = None
                check_class = check.get("check_class", "")
                if "categories" in check_class.lower():
                    # Try to extract category from class name
                    # e.g., checkov.terraform.checks.resource.aws.IAMPolicyDocument
                    parts = check_class.split(".")
                    if len(parts) > 0:
                        category = parts[-1] if parts[-1] else None

                # Use our severity mapping instead of Checkov's null severity
                severity_str = get_severity_for_check(check_id, category)

                severity = severity_map.get(
                    severity_str.upper(),
                    SeverityLevel.MEDIUM
                )
                
                # Get line range safely
                line_range = check.get("file_line_range")
                if not line_range or not isinstance(line_range, list) or len(line_range) < 2:
                    line_range = [0, 0]
                
                # Build detailed description from available fields
                check_name = check.get("check_name", "Unknown Check")
                description_parts = [check_name]
                
                # Add code block if available from Checkov output
                code_block = check.get("code_block")
                if code_block and isinstance(code_block, list) and len(code_block) > 0:
                    description_parts.append("\n\nCode:")
                    for line_num, line_content in code_block[:10]:
                        description_parts.append(f"{line_num}: {line_content.rstrip()}")
                else:
                    # If no code_block from Checkov, try to read from file
                    file_abs_path = check.get("file_abs_path", "")
                    if file_abs_path and os.path.exists(file_abs_path) and line_range[0] > 0:
                        try:
                            with open(file_abs_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                start = max(0, line_range[0] - 1)  # 0-indexed
                                end = min(len(lines), line_range[1])
                                if start < len(lines):
                                    description_parts.append("\n\nCode:")
                                    for i in range(start, end):
                                        description_parts.append(f"{i+1}: {lines[i].rstrip()}")
                        except Exception as read_err:
                            print(f"Could not read file {file_abs_path}: {read_err}")
                
                # Add details if available
                details = check.get("details")
                if details and isinstance(details, list) and len(details) > 0:
                    description_parts.append("\n\nDetails:")
                    for detail in details[:3]:
                        description_parts.append(f"- {detail}")
                
                description = "\n".join(description_parts)
                
                # Get remediation info
                remediation_parts = []
                if check.get("fixed_definition"):
                    remediation_parts.append("Fixed definition available")
                guideline = check.get("guideline")
                if guideline:
                    remediation_parts.append(f"See: {guideline}")
                remediation = "\n".join(remediation_parts) if remediation_parts else ""

                # Generate vulnerability hash for tracking
                vuln_hash = self._generate_vulnerability_hash(
                    check.get("check_id", "UNKNOWN"),
                    check.get("file_path", ""),
                    line_range[0],
                    check.get("resource", "")
                )
                current_vuln_hashes.add(vuln_hash)

                # Check if this vulnerability was seen before in previous scans
                previous_vuln = db.query(Vulnerability).filter(
                    Vulnerability.vulnerability_hash == vuln_hash,
                    Vulnerability.scan_id != scan_id  # From different scan
                ).order_by(Vulnerability.detected_at.asc()).first()

                if previous_vuln:
                    # This is a recurring vulnerability - update last_seen_at
                    print(f"♻️  Recurring vulnerability: {check_id} in {check.get('file_path', '')}")
                    detected_at = previous_vuln.detected_at  # Keep original detection time
                else:
                    # This is a new vulnerability
                    detected_at = datetime.utcnow()
                    print(f"🆕 New vulnerability: {check_id} in {check.get('file_path', '')}")

                vulnerability = Vulnerability(
                    scan_id=scan_id,
                    check_id=check.get("check_id", "UNKNOWN"),
                    check_name=check_name,
                    severity=severity,
                    file_path=check.get("file_path", ""),
                    resource_type=check.get("resource_type", ""),
                    resource_name=check.get("resource", ""),
                    line_start=line_range[0],
                    line_end=line_range[1] if len(line_range) > 1 else line_range[0],
                    line_number=line_range[0],
                    description=description,
                    remediation=remediation,
                    guideline_url=guideline if guideline else "",
                    vulnerability_hash=vuln_hash,
                    detected_at=detected_at,
                    last_seen_at=datetime.utcnow()
                )
                db.add(vulnerability)
                
            except Exception as e:
                print(f"⚠️  Error storing vulnerability {check.get('check_id', 'UNKNOWN')}: {e}")
                import traceback
                traceback.print_exc()
                continue

        # Mark previously detected vulnerabilities as fixed if they don't appear in current scan
        # Get all previous vulnerabilities for this project that are still OPEN
        previous_scans = db.query(Scan).filter(
            Scan.project_id == current_scan.project_id,
            Scan.id != scan_id,
            Scan.status == "completed"
        ).all()

        previous_scan_ids = [s.id for s in previous_scans]

        if previous_scan_ids:
            # Get all OPEN vulnerabilities from previous scans
            previous_vulns = db.query(Vulnerability).filter(
                Vulnerability.scan_id.in_(previous_scan_ids),
                Vulnerability.resolved_at.is_(None)
            ).all()

            fixed_count = 0
            for prev_vuln in previous_vulns:
                # If this vulnerability hash doesn't appear in current scan, it's fixed!
                if prev_vuln.vulnerability_hash and prev_vuln.vulnerability_hash not in current_vuln_hashes:
                    prev_vuln.resolved_at = datetime.utcnow()
                    prev_vuln.resolution_scan_id = scan_id
                    fixed_count += 1
                    print(f"✅ Fixed: {prev_vuln.check_id} in {prev_vuln.file_path}")

            if fixed_count > 0:
                print(f"🎉 Total vulnerabilities fixed in this scan: {fixed_count}")

        db.commit()

        # Send email notifications after storing vulnerabilities
        try:
            # Check for critical vulnerabilities
            self.email_service.send_critical_alert(db, scan_id)

            # Send scan summary
            self.email_service.send_scan_summary(db, scan_id)
        except Exception as e:
            print(f"⚠️ Email notification failed: {e}")
