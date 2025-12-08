"""
Report Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # compliance, vulnerability, trend
    title = Column(String(255), nullable=False)
    format = Column(String(20), nullable=False)  # pdf, json, csv
    file_path = Column(String(500), nullable=True)
    generated_by = Column(String(255), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="reports")
