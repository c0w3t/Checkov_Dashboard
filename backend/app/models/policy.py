"""
Policy Model - Store Checkov built-in and custom policies
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from datetime import datetime
from app.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(500), nullable=False)
    platform = Column(String(50), nullable=False, index=True)  # terraform, kubernetes, dockerfile
    severity = Column(String(50), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category = Column(String(100), index=True)  # ENCRYPTION, IAM, NETWORKING, etc.
    description = Column(Text)
    guideline = Column(Text)
    guideline_url = Column(String(500))
    built_in = Column(Boolean, default=True, index=True)  # True for Checkov built-in, False for custom
    file_path = Column(String(1000))  # For custom policies
    code = Column(Text)  # For custom policies
    supported_resources = Column(Text)  # JSON array of resource types
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_policy_platform_severity', 'platform', 'severity'),
        Index('idx_policy_builtin_platform', 'built_in', 'platform'),
        Index('idx_policy_category_severity', 'category', 'severity'),
    )
