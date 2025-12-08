"""
Scan Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    scan_type = Column(String(50), nullable=False)  # docker, kubernetes, terraform
    commit_sha = Column(String(255), nullable=True)
    branch = Column(String(255), nullable=True)
    triggered_by = Column(String(255), nullable=True)
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Scan statistics
    total_checks = Column(Integer, default=0)
    passed_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    skipped_checks = Column(Integer, default=0)
    scan_duration = Column(Integer, nullable=True)  # seconds
    
    # Additional metadata
    scan_metadata = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="scans")
    vulnerabilities = relationship(
        "Vulnerability",
        back_populates="scan",
        foreign_keys="Vulnerability.scan_id",
        cascade="all, delete-orphan"
    )
