"""
Notification Settings Model
Stores user preferences for email notifications
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Email recipients
    critical_recipients = Column(JSON, default=list)  # List of emails for critical alerts
    summary_recipients = Column(JSON, default=list)   # List of emails for scan summaries
    weekly_recipients = Column(JSON, default=list)    # List of emails for weekly reports

    # Notification toggles
    critical_immediate_enabled = Column(Boolean, default=True)
    scan_summary_enabled = Column(Boolean, default=True)
    weekly_summary_enabled = Column(Boolean, default=True)
    scan_failed_enabled = Column(Boolean, default=True)

    # Thresholds
    critical_threshold = Column(Integer, default=1)  # Send if >= N critical vulns
    high_threshold = Column(Integer, default=5)      # Send if >= N high vulns
    fixed_threshold = Column(Integer, default=1)     # Send if >= N vulns fixed

    # Summary options
    summary_send_when = Column(String(50), default="has_changes")  # "has_changes", "always", "has_critical_high"
    summary_include_fixed = Column(Boolean, default=True)
    summary_include_new = Column(Boolean, default=True)
    summary_include_still_open = Column(Boolean, default=True)

    # Weekly options
    weekly_day = Column(String(20), default="monday")  # Day of week
    weekly_time = Column(String(10), default="09:00")  # Time in HH:MM format
    weekly_include_trends = Column(Boolean, default=True)

    # Advanced options
    digest_mode = Column(Boolean, default=False)  # Group notifications into digest
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(10), default="22:00")
    quiet_hours_end = Column(String(10), default="08:00")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project")

class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="SET NULL"), nullable=True, index=True)

    notification_type = Column(String(50), nullable=False)  # "critical", "summary", "weekly", "failed"
    subject = Column(String(500), nullable=False)
    recipients = Column(JSON, default=list)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), default="sent")  # "sent", "failed", "queued"
    error_message = Column(String(1000), nullable=True)

    # Email content summary
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    fixed_count = Column(Integer, default=0)
    new_count = Column(Integer, default=0)

    # Relationships
    project = relationship("Project")
    scan = relationship("Scan")
