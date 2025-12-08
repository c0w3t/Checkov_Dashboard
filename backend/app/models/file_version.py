"""
File Version History Model
Tracks all changes made to files through the edit & scan feature
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class FileVersion(Base):
    __tablename__ = "file_versions"

    id = Column(Integer, primary_key=True, index=True)

    # File identification
    upload_id = Column(String(100), nullable=False, index=True)  # Format: project_id_timestamp
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(1000), nullable=False)  # Relative path within upload

    # Version details
    content = Column(Text, nullable=False)  # Full file content at this version
    content_hash = Column(String(64), nullable=False)  # SHA256 hash for deduplication
    version_number = Column(Integer, nullable=False)  # Sequential version for this file

    # Scan tracking
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=True, index=True)  # Scan triggered after this edit

    # Change metadata
    change_summary = Column(String(500), nullable=True)  # Optional description of changes
    edited_by = Column(String(100), nullable=True)  # User who made the edit (for future multi-user support)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    project = relationship("Project")
    scan = relationship("Scan")

    def __repr__(self):
        return f"<FileVersion {self.file_path} v{self.version_number} ({self.created_at})>"
