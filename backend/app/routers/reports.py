"""
Reports Router
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scan import Scan
from app.services.report_service import ReportService
from typing import Optional

router = APIRouter()
report_service = ReportService()

@router.get("/{scan_id}/pdf")
async def generate_pdf_report(
    scan_id: int,
    db: Session = Depends(get_db)
):
    """Generate PDF report for a scan"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    pdf_buffer = report_service.generate_pdf_report(scan, db)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=scan_{scan_id}_report.pdf"
        }
    )
