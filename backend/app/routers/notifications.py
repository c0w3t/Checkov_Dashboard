"""
Notification Settings Router
API endpoints for managing email notification preferences
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.notification_settings import NotificationSettings, NotificationHistory
from app.models.project import Project
from pydantic import BaseModel, EmailStr

router = APIRouter()

# Pydantic models
class NotificationSettingsUpdate(BaseModel):
    critical_recipients: Optional[List[EmailStr]] = None
    summary_recipients: Optional[List[EmailStr]] = None
    weekly_recipients: Optional[List[EmailStr]] = None

    critical_immediate_enabled: Optional[bool] = None
    scan_summary_enabled: Optional[bool] = None
    weekly_summary_enabled: Optional[bool] = None
    scan_failed_enabled: Optional[bool] = None

    critical_threshold: Optional[int] = None
    high_threshold: Optional[int] = None
    fixed_threshold: Optional[int] = None

    summary_send_when: Optional[str] = None  # "has_changes", "always", "has_critical_high"
    summary_include_fixed: Optional[bool] = None
    summary_include_new: Optional[bool] = None
    summary_include_still_open: Optional[bool] = None

    weekly_day: Optional[str] = None
    weekly_time: Optional[str] = None
    weekly_include_trends: Optional[bool] = None

    digest_mode: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

class NotificationSettingsResponse(BaseModel):
    id: int
    project_id: int

    critical_recipients: List[str]
    summary_recipients: List[str]
    weekly_recipients: List[str]

    critical_immediate_enabled: bool
    scan_summary_enabled: bool
    weekly_summary_enabled: bool
    scan_failed_enabled: bool

    critical_threshold: int
    high_threshold: int
    fixed_threshold: int

    summary_send_when: str
    summary_include_fixed: bool
    summary_include_new: bool
    summary_include_still_open: bool

    weekly_day: str
    weekly_time: str
    weekly_include_trends: bool

    digest_mode: bool
    quiet_hours_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationHistoryResponse(BaseModel):
    id: int
    project_id: int
    scan_id: Optional[int]
    notification_type: str
    subject: str
    recipients: List[str]
    sent_at: datetime
    status: str
    critical_count: int
    high_count: int
    fixed_count: int
    new_count: int

    class Config:
        from_attributes = True

@router.get("/projects/{project_id}/notifications/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get notification settings for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get or create settings
    settings = db.query(NotificationSettings).filter(
        NotificationSettings.project_id == project_id
    ).first()

    if not settings:
        # Create default settings
        settings = NotificationSettings(
            project_id=project_id,
            critical_recipients=[],
            summary_recipients=[],
            weekly_recipients=[]
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings

@router.put("/projects/{project_id}/notifications/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    project_id: int,
    updates: NotificationSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update notification settings for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get or create settings
    settings = db.query(NotificationSettings).filter(
        NotificationSettings.project_id == project_id
    ).first()

    if not settings:
        settings = NotificationSettings(project_id=project_id)
        db.add(settings)

    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(settings)

    return settings

@router.post("/projects/{project_id}/notifications/test")
async def test_notification(
    project_id: int,
    notification_type: str = "summary",  # "critical", "summary", "failed"
    db: Session = Depends(get_db)
):
    """Send a test notification email"""
    from app.services.email_service import EmailService

    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get settings
    settings = db.query(NotificationSettings).filter(
        NotificationSettings.project_id == project_id
    ).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Notification settings not configured")

    email_service = EmailService()

    # Check which recipients to use based on notification type
    recipients = []
    if notification_type == "critical":
        recipients = settings.critical_recipients
    elif notification_type == "summary":
        recipients = settings.summary_recipients
    elif notification_type == "weekly":
        recipients = settings.weekly_recipients

    if not recipients:
        raise HTTPException(status_code=400, detail=f"No recipients configured for {notification_type} notifications")

    # Send test email
    subject = f"🧪 Test Notification - {project.name}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Test Notification</h2>
        <p>This is a test email from your Security Dashboard.</p>
        <p><strong>Project:</strong> {project.name}</p>
        <p><strong>Notification Type:</strong> {notification_type}</p>
        <p>If you received this email, your notification settings are configured correctly!</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            This is a test email. No action required.
        </p>
    </body>
    </html>
    """

    text_content = f"""
    Test Notification

    This is a test email from your Security Dashboard.

    Project: {project.name}
    Notification Type: {notification_type}

    If you received this email, your notification settings are configured correctly!
    """

    success = email_service.send_email(recipients, subject, html_content, text_content)

    if success:
        return {"message": "Test email sent successfully", "recipients": recipients}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check SMTP configuration.")

@router.get("/projects/{project_id}/notifications/history", response_model=List[NotificationHistoryResponse])
async def get_notification_history(
    project_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get notification history for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    history = db.query(NotificationHistory).filter(
        NotificationHistory.project_id == project_id
    ).order_by(NotificationHistory.sent_at.desc()).limit(limit).all()

    return history

@router.delete("/projects/{project_id}/notifications/history")
async def clear_notification_history(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Clear notification history for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    deleted_count = db.query(NotificationHistory).filter(
        NotificationHistory.project_id == project_id
    ).delete()

    db.commit()

    return {"message": f"Deleted {deleted_count} notification records"}
