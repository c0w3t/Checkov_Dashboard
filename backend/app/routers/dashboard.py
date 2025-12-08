"""
Dashboard Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Project, Scan, Vulnerability
from app.models.vulnerability import SeverityLevel, VulnerabilityStatus
from app.schemas.dashboard import DashboardStats
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive dashboard statistics"""
    
    # Project statistics
    total_projects = db.query(Project).count()
    frameworks = db.query(
        Project.framework,
        func.count(Project.id)
    ).group_by(Project.framework).all()
    
    # Scan statistics
    total_scans = db.query(Scan).count()
    completed_scans = db.query(Scan).filter(Scan.status == "completed").count()
    failed_scans = db.query(Scan).filter(Scan.status == "failed").count()
    
    # Calculate average pass rate
    avg_pass_rate = 0.0
    if completed_scans > 0:
        scans_with_checks = db.query(Scan).filter(
            Scan.status == "completed",
            Scan.total_checks > 0
        ).all()
        if scans_with_checks:
            pass_rates = [
                (s.passed_checks / s.total_checks * 100) 
                for s in scans_with_checks
            ]
            avg_pass_rate = sum(pass_rates) / len(pass_rates)
    
    # Vulnerability statistics
    vuln_by_severity = {
        "critical": db.query(Vulnerability).filter(Vulnerability.severity == SeverityLevel.CRITICAL.value).count(),
        "high": db.query(Vulnerability).filter(Vulnerability.severity == SeverityLevel.HIGH.value).count(),
        "medium": db.query(Vulnerability).filter(Vulnerability.severity == SeverityLevel.MEDIUM.value).count(),
        "low": db.query(Vulnerability).filter(Vulnerability.severity == SeverityLevel.LOW.value).count(),
        "info": db.query(Vulnerability).filter(Vulnerability.severity == SeverityLevel.INFO.value).count(),
    }
    
    # Trend data (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Generate daily trend data
    trends_scans = []
    trends_vulnerabilities = []
    trends_pass_rate = []
    
    for i in range(30):
        day = datetime.utcnow() - timedelta(days=29-i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Count scans for this day
        daily_scans = db.query(Scan).filter(
            Scan.started_at >= day_start,
            Scan.started_at <= day_end
        ).count()
        
        # Count vulnerabilities detected on this day
        daily_vulns = db.query(Vulnerability).filter(
            Vulnerability.detected_at >= day_start,
            Vulnerability.detected_at <= day_end
        ).count()
        
        # Calculate pass rate for this day
        day_scans = db.query(Scan).filter(
            Scan.started_at >= day_start,
            Scan.started_at <= day_end,
            Scan.status == "completed",
            Scan.total_checks > 0
        ).all()
        
        daily_pass_rate = 0.0
        if day_scans:
            pass_rates = [(s.passed_checks / s.total_checks * 100) for s in day_scans]
            daily_pass_rate = sum(pass_rates) / len(pass_rates)
        
        trends_scans.append({
            "date": day.strftime("%Y-%m-%d"),
            "value": daily_scans
        })
        
        trends_vulnerabilities.append({
            "date": day.strftime("%Y-%m-%d"),
            "value": daily_vulns
        })
        
        trends_pass_rate.append({
            "date": day.strftime("%Y-%m-%d"),
            "value": round(daily_pass_rate, 1)
        })
    
    # Top vulnerabilities
    top_vulns = db.query(
        Vulnerability.check_id,
        Vulnerability.check_name,
        Vulnerability.severity,
        func.count(Vulnerability.id).label("count")
    ).filter(
        Vulnerability.status == VulnerabilityStatus.OPEN.value
    ).group_by(
        Vulnerability.check_id,
        Vulnerability.check_name,
        Vulnerability.severity
    ).order_by(
        func.count(Vulnerability.id).desc()
    ).limit(10).all()
    
    # Recent scans
    recent_scans = db.query(Scan).order_by(Scan.started_at.desc()).limit(5).all()
    
    # Get severity breakdown for each recent scan
    recent_scans_with_severity = []
    for scan in recent_scans:
        severity_counts = db.query(
            Vulnerability.severity,
            func.count(Vulnerability.id)
        ).filter(
            Vulnerability.scan_id == scan.id,
            Vulnerability.status == VulnerabilityStatus.OPEN.value
        ).group_by(
            Vulnerability.severity
        ).all()
        
        severity_dict = {severity: count for severity, count in severity_counts}
        recent_scans_with_severity.append({
            "scan": scan,
            "severity": severity_dict
        })
    
    # Vulnerabilities by project
    vulns_by_project = db.query(
        Project.name,
        func.count(Vulnerability.id).label("failed_checks")
    ).join(
        Scan, Project.id == Scan.project_id
    ).join(
        Vulnerability, Scan.id == Vulnerability.scan_id
    ).filter(
        Vulnerability.status == VulnerabilityStatus.OPEN.value
    ).group_by(
        Project.name
    ).order_by(
        func.count(Vulnerability.id).desc()
    ).all()
    
    return {
        "projects": {
            "total_projects": total_projects,
            "active_projects": total_projects,
            "frameworks": {fw: count for fw, count in frameworks}
        },
        "scans": {
            "total_scans": total_scans,
            "completed_scans": completed_scans,
            "failed_scans": failed_scans,
            "average_pass_rate": round(avg_pass_rate, 2)
        },
        "vulnerabilities": vuln_by_severity,
        "trends": {
            "scans": trends_scans,
            "vulnerabilities": trends_vulnerabilities,
            "pass_rate": trends_pass_rate
        },
        "top_vulnerabilities": [
            {
                "check_id": v.check_id,
                "check_name": v.check_name,
                "severity": v.severity,
                "count": v.count
            }
            for v in top_vulns
        ],
        "recent_scans": [
            {
                "id": item["scan"].id,
                "project_id": item["scan"].project_id,
                "project_name": db.query(Project.name).filter(Project.id == item["scan"].project_id).scalar(),
                "status": item["scan"].status,
                "started_at": item["scan"].started_at.isoformat(),
                "failed_checks": item["scan"].failed_checks,
                "severity": {
                    "critical": item["severity"].get("critical", 0),
                    "high": item["severity"].get("high", 0),
                    "medium": item["severity"].get("medium", 0),
                    "low": item["severity"].get("low", 0),
                    "info": item["severity"].get("info", 0)
                }
            }
            for item in recent_scans_with_severity
        ],
        "vulnerabilities_by_project": [
            {
                "project_name": name,
                "failed_checks": count
            }
            for name, count in vulns_by_project
        ]
    }
