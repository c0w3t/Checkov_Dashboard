"""
API Token Model for GitHub Actions Authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from app.database import Base


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Token name/description
    token = Column(String(64), unique=True, nullable=False, index=True)  # The actual token
    is_active = Column(Boolean, default=True)
    permissions = Column(Text, nullable=True)  # JSON string of permissions
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)  # Who created this token
