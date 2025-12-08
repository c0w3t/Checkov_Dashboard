"""
Report Service - Generates various report formats
"""
import io
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.models.scan import Scan
from app.models.vulnerability import Vulnerability
from app.models.project import Project

# Register DejaVu Sans font (supports Vietnamese)
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    FONT_NAME = 'DejaVuSans'
    FONT_NAME_BOLD = 'DejaVuSans-Bold'
except:
    # Fallback to default fonts
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'

class ReportService:
    def generate_pdf_report(self, scan: Scan, db: Session):
        """Generate PDF report with full vulnerability details"""
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=30, leftMargin=30,
                                topMargin=30, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            fontName=FONT_NAME_BOLD,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            fontName=FONT_NAME_BOLD,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Get project info
        project = db.query(Project).filter(Project.id == scan.project_id).first()
        
        # Title
        elements.append(Paragraph("Security Scan Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Scan Information
        elements.append(Paragraph("Scan Information", heading_style))
        scan_info_data = [
            ['Scan ID:', str(scan.id)],
            ['Project:', project.name if project else 'Unknown'],
            ['Framework:', project.framework if project else 'Unknown'],
            ['Status:', scan.status],
            ['Started:', scan.started_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['Completed:', scan.completed_at.strftime('%Y-%m-%d %H:%M:%S') if scan.completed_at else 'N/A'],
        ]
        
        scan_info_table = Table(scan_info_data, colWidths=[2*inch, 4*inch])
        scan_info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), FONT_NAME_BOLD),
            ('FONTNAME', (1, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(scan_info_table)
        elements.append(Spacer(1, 20))
        
        # Statistics
        elements.append(Paragraph("Statistics", heading_style))
        pass_rate = (scan.passed_checks / scan.total_checks * 100) if scan.total_checks > 0 else 0
        
        stats_data = [
            ['Metric', 'Value'],
            ['Total Checks', str(scan.total_checks)],
            ['Passed Checks', str(scan.passed_checks)],
            ['Failed Checks', str(scan.failed_checks)],
            ['Skipped Checks', str(scan.skipped_checks)],
            ['Pass Rate', f'{pass_rate:.1f}%']
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Vulnerabilities
        vulnerabilities = db.query(Vulnerability).filter(
            Vulnerability.scan_id == scan.id
        ).all()
        
        elements.append(Paragraph(f"Vulnerabilities ({len(vulnerabilities)} found)", heading_style))
        
        if vulnerabilities:
            # Group vulnerabilities by severity
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
            sorted_vulns = sorted(vulnerabilities, 
                                 key=lambda v: severity_order.get(v.severity.value.lower(), 5))
            
            for vuln in sorted_vulns:
                # Vulnerability header
                severity_colors = {
                    'critical': colors.HexColor('#d32f2f'),
                    'high': colors.HexColor('#f57c00'),
                    'medium': colors.HexColor('#ffa726'),
                    'low': colors.HexColor('#ffb74d'),
                    'info': colors.HexColor('#64b5f6')
                }
                severity = vuln.severity.value.lower()
                severity_color = severity_colors.get(severity, colors.grey)
                
                vuln_data = [
                    ['Check ID:', vuln.check_id],
                    ['Severity:', vuln.severity.value.upper()],
                    ['Check Name:', vuln.check_name or 'N/A'],
                    ['File Path:', vuln.file_path or 'N/A'],
                    ['Resource:', f"{vuln.resource_type or 'N/A'}: {vuln.resource_name or 'N/A'}"],
                    ['Line Range:', f"{vuln.line_start or 'N/A'} - {vuln.line_end or 'N/A'}"],
                ]
                
                # Add description with better formatting if available
                if vuln.description and vuln.description.strip():
                    import re
                    # Clean description text
                    desc_text = vuln.description.strip()
                    
                    # AGGRESSIVELY remove ALL Unicode special characters
                    # Remove all non-printable and special box/block characters
                    desc_text = ''.join(char for char in desc_text if ord(char) < 0x2500 or ord(char) > 0x25FF)
                    desc_text = ''.join(char for char in desc_text if ord(char) < 0x2580 or ord(char) > 0x259F)
                    
                    # Remove specific problematic characters by their exact representation
                    problematic_chars = ['■', '□', '▪', '▫', '▬', '▭', '▮', '▯', 
                                        '◼', '◻', '◾', '◽', '▀', '▁', '▂', '▃', 
                                        '▄', '▅', '▆', '▇', '█', '▉', '▊', '▋', 
                                        '▌', '▍', '▎', '▏', '▐', '░', '▒', '▓']
                    for char in problematic_chars:
                        desc_text = desc_text.replace(char, '')
                    
                    # Clean up "Lỗi" or "Lni" prefixes that appear with numbers
                    desc_text = re.sub(r'(Lỗi|Lni|Ln)\s*\d+:', '', desc_text)
                    
                    # Clean up excessive spaces and newlines
                    desc_text = re.sub(r'\s+', ' ', desc_text)
                    desc_text = desc_text.strip()
                    
                    # Now format with line breaks before each numbered item
                    # Only match standalone numbers followed by colon at start or after space
                    desc_text = re.sub(r'(?<=\s)(\d+:)', r'<br/>\1', desc_text)
                    desc_text = re.sub(r'^(\d+:)', r'\1', desc_text)  # Don't break first item
                    
                    desc_style = ParagraphStyle(
                        'DescStyle',
                        parent=styles['Normal'],
                        fontSize=9,
                        fontName=FONT_NAME,
                        leading=12,
                        textColor=colors.HexColor('#424242'),
                        leftIndent=5,
                        spaceAfter=0,
                        wordWrap='CJK'
                    )
                    vuln_data.append(['Description:', Paragraph(desc_text, desc_style)])
                
                vuln_table = Table(vuln_data, colWidths=[1.5*inch, 4.5*inch])
                vuln_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
                    ('BACKGROUND', (1, 1), (1, 1), severity_color),
                    ('TEXTCOLOR', (1, 1), (1, 1), colors.whitesmoke),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (0, -1), FONT_NAME_BOLD),
                    ('FONTNAME', (1, 0), (-1, -1), FONT_NAME),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                elements.append(vuln_table)
                
                elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("No vulnerabilities found.", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
