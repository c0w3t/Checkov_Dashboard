"""
HTML Email Templates
Beautiful, responsive email templates for notifications
"""
from typing import List, Dict, Any
from app.models.project import Project
from app.models.scan import Scan
from app.models.vulnerability import Vulnerability

def get_severity_color(severity: str) -> str:
    """Get color for severity level"""
    colors = {
        'critical': '#DC2626',  # Red
        'high': '#F59E0B',      # Orange
        'medium': '#3B82F6',    # Blue
        'low': '#10B981',       # Green
        'info': '#6B7280'       # Gray
    }
    return colors.get(severity.lower(), '#6B7280')

def get_base_styles() -> str:
    """Get base CSS styles for email"""
    return """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .email-container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 3px solid #3B82F6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
            color: #1F2937;
        }
        .header .meta {
            color: #6B7280;
            font-size: 14px;
            margin-top: 8px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #1F2937;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #E5E7EB;
        }
        .vuln-card {
            background-color: #F9FAFB;
            border-left: 4px solid;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }
        .vuln-card.critical { border-left-color: #DC2626; }
        .vuln-card.high { border-left-color: #F59E0B; }
        .vuln-card.medium { border-left-color: #3B82F6; }
        .vuln-card.low { border-left-color: #10B981; }
        .vuln-title {
            font-weight: 600;
            color: #1F2937;
            margin-bottom: 5px;
        }
        .vuln-meta {
            color: #6B7280;
            font-size: 13px;
            margin-bottom: 8px;
        }
        .vuln-description {
            color: #4B5563;
            font-size: 14px;
            line-height: 1.5;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            color: white;
            margin-right: 8px;
        }
        .badge.critical { background-color: #DC2626; }
        .badge.high { background-color: #F59E0B; }
        .badge.medium { background-color: #3B82F6; }
        .badge.low { background-color: #10B981; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background-color: #F9FAFB;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #1F2937;
        }
        .stat-label {
            color: #6B7280;
            font-size: 14px;
            margin-top: 5px;
        }
        .cta-button {
            display: inline-block;
            background-color: #3B82F6;
            color: white !important;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 20px;
        }
        .alert-box {
            background-color: #FEF2F2;
            border: 1px solid #FCA5A5;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .alert-box.success {
            background-color: #F0FDF4;
            border-color: #86EFAC;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #E5E7EB;
            color: #6B7280;
            font-size: 13px;
            text-align: center;
        }
        hr {
            border: none;
            border-top: 1px solid #E5E7EB;
            margin: 20px 0;
        }
    </style>
    """

def render_critical_alert(project: Project, scan: Scan, vulns: List[Vulnerability], dashboard_url: str) -> str:
    """Render HTML for critical vulnerability alert"""

    vuln_cards = ""
    for i, vuln in enumerate(vulns, 1):
        vuln_cards += f"""
        <div class="vuln-card critical">
            <div class="vuln-title">
                {i}. {vuln.check_id}: {vuln.check_name}
            </div>
            <div class="vuln-meta">
                📄 File: {vuln.file_path} (line {vuln.line_number})
            </div>
            <div class="vuln-description">
                <strong>Impact:</strong> {vuln.description[:200]}...
                <br><br>
                <strong>Action:</strong> {vuln.remediation or 'Review and fix immediately'}
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {get_base_styles()}
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🔴 CRITICAL SECURITY ALERT</h1>
                <div class="meta">
                    Project: <strong>{project.name}</strong> ({project.framework})<br>
                    Scan: #{scan.id} | Completed: {scan.completed_at.strftime('%Y-%m-%d %H:%M')}
                </div>
            </div>

            <div class="alert-box">
                <strong>⚠️ {len(vulns)} CRITICAL vulnerabilities detected</strong><br>
                These issues pose immediate security risks and require urgent attention.
            </div>

            <div class="section">
                <div class="section-title">Critical Vulnerabilities</div>
                {vuln_cards}
            </div>

            <div class="alert-box">
                <strong>⚡ ACTION REQUIRED WITHIN 24 HOURS</strong><br>
                Please review and address these critical security issues immediately.
            </div>

            <a href="{dashboard_url}/scans/{scan.id}" class="cta-button">
                View Full Details →
            </a>

            <div class="footer">
                Security Dashboard | Generated on {scan.completed_at.strftime('%Y-%m-%d at %H:%M')}<br>
                <a href="{dashboard_url}/projects/{project.id}/settings">Manage notification settings</a>
            </div>
        </div>
    </body>
    </html>
    """

    return html

def render_scan_summary(project: Project, scan: Scan, stats: Dict[str, Any], dashboard_url: str) -> str:
    """Render HTML for scan summary"""

    # Fixed vulnerabilities
    fixed_cards = ""
    for vuln in stats['fixed_vulns'][:5]:  # Show top 5
        severity_class = vuln.severity.value.lower()
        fixed_cards += f"""
        <div class="vuln-card {severity_class}">
            <div class="vuln-title">
                <span class="badge {severity_class}">{vuln.severity.value.upper()}</span>
                {vuln.check_id}: {vuln.check_name}
            </div>
            <div class="vuln-meta">
                ✅ Fixed in: {vuln.file_path}
            </div>
        </div>
        """

    if len(stats['fixed_vulns']) > 5:
        fixed_cards += f"<div class='vuln-meta'>... and {len(stats['fixed_vulns']) - 5} more</div>"

    # New vulnerabilities
    new_cards = ""
    for vuln in stats['new_vulns'][:5]:  # Show top 5
        severity_class = vuln.severity.value.lower()
        new_cards += f"""
        <div class="vuln-card {severity_class}">
            <div class="vuln-title">
                <span class="badge {severity_class}">{vuln.severity.value.upper()}</span>
                {vuln.check_id}: {vuln.check_name}
            </div>
            <div class="vuln-meta">
                📄 File: {vuln.file_path} (line {vuln.line_number})
            </div>
            <div class="vuln-description">
                {vuln.description[:150]}...
            </div>
        </div>
        """

    if len(stats['new_vulns']) > 5:
        new_cards += f"<div class='vuln-meta'>... and {len(stats['new_vulns']) - 5} more</div>"

    progress_indicator = "↗️ Improving" if stats['fixed_count'] > stats['new_count'] else "↘️ Needs Attention" if stats['new_count'] > stats['fixed_count'] else "→ Stable"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {get_base_styles()}
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>📊 Scan Complete: {project.name}</h1>
                <div class="meta">
                    Scan: #{scan.id} | Completed: {scan.completed_at.strftime('%Y-%m-%d %H:%M')}<br>
                    Duration: {scan.scan_duration or 0}s | Framework: {project.framework}
                </div>
            </div>

            <div class="section">
                <div class="section-title">Summary</div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" style="color: #10B981;">✅ {stats['fixed_count']}</div>
                        <div class="stat-label">Fixed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" style="color: #F59E0B;">🆕 {stats['new_count']}</div>
                        <div class="stat-label">New</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" style="color: #3B82F6;">🔄 {stats['still_open_count']}</div>
                        <div class="stat-label">Still Open</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{scan.passed_checks}/{scan.total_checks}</div>
                        <div class="stat-label">Passed Checks</div>
                    </div>
                </div>
                <div style="text-align: center; color: #6B7280;">
                    Progress: <strong>{progress_indicator}</strong>
                </div>
            </div>

            {f'''
            <div class="section">
                <div class="section-title">✅ Fixed Vulnerabilities ({stats['fixed_count']})</div>
                <div class="alert-box success">
                    <strong>Great work! 🎉</strong> {stats['fixed_count']} vulnerabilities have been resolved.
                </div>
                {fixed_cards}
            </div>
            ''' if stats['fixed_count'] > 0 else ''}

            {f'''
            <div class="section">
                <div class="section-title">🆕 New Vulnerabilities ({stats['new_count']})</div>
                {new_cards}
            </div>
            ''' if stats['new_count'] > 0 else ''}

            {f'''
            <div class="section">
                <div class="section-title">🔄 Still Open ({stats['still_open_count']})</div>
                <div class="vuln-meta">
                    🔴 CRITICAL: {len([v for v in stats['still_open_vulns'] if v.severity.value == 'critical'])}<br>
                    🟠 HIGH: {len([v for v in stats['still_open_vulns'] if v.severity.value == 'high'])}<br>
                    🟡 MEDIUM: {len([v for v in stats['still_open_vulns'] if v.severity.value == 'medium'])}<br>
                    🟢 LOW: {len([v for v in stats['still_open_vulns'] if v.severity.value == 'low'])}
                </div>
            </div>
            ''' if stats['still_open_count'] > 0 else ''}

            <a href="{dashboard_url}/projects/{project.id}/tracking" class="cta-button">
                View Vulnerability Tracking →
            </a>

            <div class="footer">
                Security Dashboard | Generated on {scan.completed_at.strftime('%Y-%m-%d at %H:%M')}<br>
                <a href="{dashboard_url}/projects/{project.id}/settings">Manage notification settings</a>
            </div>
        </div>
    </body>
    </html>
    """

    return html

def render_scan_failed(project: Project, scan: Scan, dashboard_url: str) -> str:
    """Render HTML for scan failure notification"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {get_base_styles()}
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>❌ Scan Failed</h1>
                <div class="meta">
                    Project: <strong>{project.name}</strong><br>
                    Scan: #{scan.id} | Failed at: {scan.completed_at.strftime('%Y-%m-%d %H:%M')}
                </div>
            </div>

            <div class="alert-box">
                <strong>⚠️ Scan execution failed</strong><br>
                The security scan could not complete successfully.
            </div>

            <div class="section">
                <div class="section-title">Error Details</div>
                <div class="vuln-card critical">
                    <div class="vuln-description">
                        {scan.error_message or 'Unknown error occurred'}
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Action Required</div>
                <ol style="color: #4B5563;">
                    <li>Review the scan logs for detailed error information</li>
                    <li>Fix any configuration or infrastructure issues</li>
                    <li>Re-run the scan</li>
                </ol>
            </div>

            <a href="{dashboard_url}/scans/{scan.id}/logs" class="cta-button">
                View Scan Logs →
            </a>

            <div class="footer">
                Security Dashboard | Generated on {scan.completed_at.strftime('%Y-%m-%d at %H:%M')}<br>
                Need help? Contact your DevOps team
            </div>
        </div>
    </body>
    </html>
    """

    return html
