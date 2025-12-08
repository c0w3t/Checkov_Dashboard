"""
Email Notification Service
Handles sending email notifications for security scan results
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.notification_settings import NotificationSettings, NotificationHistory
from app.models.scan import Scan
from app.models.vulnerability import Vulnerability
from app.models.project import Project
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # SMTP Configuration from environment variables
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_username)
        self.smtp_from_name = os.getenv("SMTP_FROM_NAME", "Security Dashboard")
        self.dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:5173")

        # Enable/disable email sending
        self.enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"

    def send_email(self, to_emails: List[str], subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email via SMTP"""
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send to {to_emails}: {subject}")
            return False

        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            msg['To'] = ', '.join(to_emails)

            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)

            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_emails}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def send_critical_alert(self, db: Session, scan_id: int):
        """Send immediate alert for critical vulnerabilities"""
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return

        project = db.query(Project).filter(Project.id == scan.project_id).first()
        if not project:
            return

        # Get notification settings
        settings = db.query(NotificationSettings).filter(
            NotificationSettings.project_id == project.id
        ).first()

        if not settings or not settings.critical_immediate_enabled:
            return

        # Get critical vulnerabilities from this scan
        critical_vulns = db.query(Vulnerability).filter(
            Vulnerability.scan_id == scan_id,
            Vulnerability.severity == 'critical'
        ).all()

        if len(critical_vulns) < settings.critical_threshold:
            return

        # Prepare email
        subject = f"🔴 CRITICAL ALERT: Project \"{project.name}\" - {len(critical_vulns)} Critical Security Issues"

        html_content = self._render_critical_alert_html(project, scan, critical_vulns)
        text_content = self._render_critical_alert_text(project, scan, critical_vulns)

        # Send email
        recipients = settings.critical_recipients or []
        if recipients:
            success = self.send_email(recipients, subject, html_content, text_content)

            # Log notification
            history = NotificationHistory(
                project_id=project.id,
                scan_id=scan_id,
                notification_type="critical",
                subject=subject,
                recipients=recipients,
                status="sent" if success else "failed",
                critical_count=len(critical_vulns)
            )
            db.add(history)
            db.commit()

    def send_scan_summary(self, db: Session, scan_id: int):
        """Send scan summary with fixed/new/open vulnerabilities"""
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return

        project = db.query(Project).filter(Project.id == scan.project_id).first()
        if not project:
            return

        # Get notification settings
        settings = db.query(NotificationSettings).filter(
            NotificationSettings.project_id == project.id
        ).first()

        if not settings or not settings.scan_summary_enabled:
            return

        # Get vulnerability statistics
        stats = self._get_scan_statistics(db, scan_id, project.id)

        # Check if should send based on send_when setting
        should_send = False
        if settings.summary_send_when == "always":
            should_send = True
        elif settings.summary_send_when == "has_changes":
            should_send = stats['fixed_count'] > 0 or stats['new_count'] > 0
        elif settings.summary_send_when == "has_critical_high":
            should_send = stats['new_critical'] > 0 or stats['new_high'] > 0

        if not should_send:
            return

        # Prepare email
        status_emoji = "✅" if stats['fixed_count'] > stats['new_count'] else "⚠️"
        subject = f"{status_emoji} Scan Complete: \"{project.name}\" - {stats['fixed_count']} Fixed, {stats['new_count']} New Issues"

        html_content = self._render_scan_summary_html(project, scan, stats)
        text_content = self._render_scan_summary_text(project, scan, stats)

        # Send email
        recipients = settings.summary_recipients or []
        if recipients:
            success = self.send_email(recipients, subject, html_content, text_content)

            # Log notification
            history = NotificationHistory(
                project_id=project.id,
                scan_id=scan_id,
                notification_type="summary",
                subject=subject,
                recipients=recipients,
                status="sent" if success else "failed",
                critical_count=stats['new_critical'],
                high_count=stats['new_high'],
                fixed_count=stats['fixed_count'],
                new_count=stats['new_count']
            )
            db.add(history)
            db.commit()

    def send_scan_failed_alert(self, db: Session, scan_id: int):
        """Send alert when scan fails"""
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return

        project = db.query(Project).filter(Project.id == scan.project_id).first()
        if not project:
            return

        # Get notification settings
        settings = db.query(NotificationSettings).filter(
            NotificationSettings.project_id == project.id
        ).first()

        if not settings or not settings.scan_failed_enabled:
            return

        # Prepare email
        subject = f"❌ Scan Failed: \"{project.name}\" - Action Required"

        html_content = self._render_scan_failed_html(project, scan)
        text_content = self._render_scan_failed_text(project, scan)

        # Send to critical recipients (scan failures are critical)
        recipients = settings.critical_recipients or []
        if recipients:
            success = self.send_email(recipients, subject, html_content, text_content)

            # Log notification
            history = NotificationHistory(
                project_id=project.id,
                scan_id=scan_id,
                notification_type="failed",
                subject=subject,
                recipients=recipients,
                status="sent" if success else "failed"
            )
            db.add(history)
            db.commit()

    def _get_scan_statistics(self, db: Session, scan_id: int, project_id: int) -> Dict[str, Any]:
        """Get detailed statistics for scan summary"""
        # Get all vulnerabilities from current scan
        current_vulns = db.query(Vulnerability).filter(
            Vulnerability.scan_id == scan_id
        ).all()

        # Get fixed vulnerabilities (resolved in this scan)
        fixed_vulns = db.query(Vulnerability).filter(
            Vulnerability.resolution_scan_id == scan_id
        ).all()

        # Count new vs recurring
        new_vulns = [v for v in current_vulns if v.detected_at >= v.scan.started_at]

        # Count by severity
        new_critical = len([v for v in new_vulns if v.severity.value == 'critical'])
        new_high = len([v for v in new_vulns if v.severity.value == 'high'])
        new_medium = len([v for v in new_vulns if v.severity.value == 'medium'])
        new_low = len([v for v in new_vulns if v.severity.value == 'low'])

        # Get still open vulnerabilities
        still_open = [v for v in current_vulns if v not in new_vulns]

        return {
            'total_vulns': len(current_vulns),
            'fixed_count': len(fixed_vulns),
            'new_count': len(new_vulns),
            'still_open_count': len(still_open),
            'new_critical': new_critical,
            'new_high': new_high,
            'new_medium': new_medium,
            'new_low': new_low,
            'fixed_vulns': fixed_vulns,
            'new_vulns': new_vulns,
            'still_open_vulns': still_open
        }

    def _render_critical_alert_html(self, project: Project, scan: Scan, vulns: List[Vulnerability]) -> str:
        """Render HTML email for critical alert"""
        from app.templates.email_templates import render_critical_alert
        return render_critical_alert(project, scan, vulns, self.dashboard_url)

    def _render_critical_alert_text(self, project: Project, scan: Scan, vulns: List[Vulnerability]) -> str:
        """Render plain text email for critical alert"""
        lines = [
            f"CRITICAL ALERT: {len(vulns)} Critical Vulnerabilities Detected",
            "",
            f"Project: {project.name} ({project.framework})",
            f"Scan: #{scan.id} | Completed: {scan.completed_at}",
            "",
            "=" * 60,
            "CRITICAL VULNERABILITIES:",
            "=" * 60,
            ""
        ]

        for i, vuln in enumerate(vulns, 1):
            lines.extend([
                f"{i}. {vuln.check_id}: {vuln.check_name}",
                f"   File: {vuln.file_path} (line {vuln.line_number})",
                f"   Impact: {vuln.description[:100]}...",
                ""
            ])

        lines.extend([
            "=" * 60,
            "ACTION REQUIRED WITHIN 24 HOURS",
            "=" * 60,
            "",
            f"View details: {self.dashboard_url}/scans/{scan.id}",
            f"Project page: {self.dashboard_url}/projects/{project.id}",
        ])

        return "\n".join(lines)

    def _render_scan_summary_html(self, project: Project, scan: Scan, stats: Dict) -> str:
        """Render HTML email for scan summary"""
        from app.templates.email_templates import render_scan_summary
        return render_scan_summary(project, scan, stats, self.dashboard_url)

    def _render_scan_summary_text(self, project: Project, scan: Scan, stats: Dict) -> str:
        """Render plain text email for scan summary"""
        lines = [
            f"Scan Complete: {project.name}",
            "",
            f"Project: {project.name} ({project.framework})",
            f"Scan: #{scan.id} | Completed: {scan.completed_at}",
            f"Duration: {scan.scan_duration}s",
            "",
            "=" * 60,
            "SCAN SUMMARY",
            "=" * 60,
            "",
            f"✅ Fixed:        {stats['fixed_count']} vulnerabilities",
            f"🆕 New:          {stats['new_count']} vulnerabilities",
            f"🔄 Still Open:   {stats['still_open_count']} vulnerabilities",
            f"📈 Total Checks: {scan.passed_checks} passed, {scan.failed_checks} failed",
            "",
            f"View full report: {self.dashboard_url}/scans/{scan.id}",
        ]

        return "\n".join(lines)

    def _render_scan_failed_html(self, project: Project, scan: Scan) -> str:
        """Render HTML email for scan failure"""
        from app.templates.email_templates import render_scan_failed
        return render_scan_failed(project, scan, self.dashboard_url)

    def _render_scan_failed_text(self, project: Project, scan: Scan) -> str:
        """Render plain text email for scan failure"""
        lines = [
            f"❌ SCAN FAILED: {project.name}",
            "",
            f"Project: {project.name}",
            f"Scan: #{scan.id} | Failed at: {scan.completed_at}",
            f"Error: {scan.error_message}",
            "",
            "Action Required:",
            "1. Review scan logs",
            "2. Fix configuration issues",
            "3. Re-run scan",
            "",
            f"View logs: {self.dashboard_url}/scans/{scan.id}/logs",
        ]

        return "\n".join(lines)
