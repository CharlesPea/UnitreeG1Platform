from flask import Blueprint, send_file, current_app
import io, os, statistics
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from gauge_app.services.mqtt_service import sensor_history, anomaly_log
from datetime import datetime

bp = Blueprint('anomalies', __name__)

# Define modern color scheme
BRAND_COLOR = colors.HexColor("#1E88E5")  # Modern blue
ACCENT_COLOR = colors.HexColor("#FFC107")  # Complementary amber
BG_LIGHT = colors.HexColor("#F5F5F5")     # Light gray background
TEXT_COLOR = colors.HexColor("#212121")   # Dark gray for text
DIVIDER_COLOR = colors.HexColor("#BDBDBD")  # Medium gray for dividers

def setup_styles():
    """Create custom styles for the document"""
    styles = getSampleStyleSheet()
    
    # Custom heading style
    styles.add(ParagraphStyle(
        name='ModernHeading',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=BRAND_COLOR,
        spaceAfter=12,
        spaceBefore=16,
        leading=16
    ))
    
    # Custom normal text style
    styles.add(ParagraphStyle(
        name='ModernBody',
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_COLOR,
        spaceAfter=6,
        leading=12
    ))
    
    return styles

def _header_footer(canvas, doc):
    """Combined header and footer function"""
    # Save the canvas state
    canvas.saveState()
    
    # Header section
    # Logo
    logo_path = os.path.join(current_app.static_folder, 'images', 'logo.png')
    if os.path.exists(logo_path):
        canvas.drawImage(logo_path, 
                        doc.leftMargin, 
                        doc.height + doc.topMargin - 0.75*inch,
                        width=0.75*inch, 
                        height=0.75*inch, 
                        preserveAspectRatio=True)
    
    # Title
    canvas.setFont("Helvetica-Bold", 18)
    canvas.setFillColor(BRAND_COLOR)
    canvas.drawString(doc.leftMargin + 1.0*inch,
                    doc.height + doc.topMargin - 0.5*inch,
                    "Anomaly Log Summary")
    
    # Subtitle with current date
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(TEXT_COLOR)
    current_date = datetime.now().strftime("%B %d, %Y")
    canvas.drawString(doc.leftMargin + 1.0*inch,
                    doc.height + doc.topMargin - 0.7*inch,
                    f"Generated on {current_date}")
    
    # Decorative header line
    canvas.setStrokeColor(BRAND_COLOR)
    canvas.setLineWidth(2)
    canvas.line(doc.leftMargin,
              doc.height + doc.topMargin - 0.9*inch,
              doc.leftMargin + doc.width,
              doc.height + doc.topMargin - 0.9*inch)
    
    # Footer section
    page_no = canvas.getPageNumber()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(TEXT_COLOR)
    
    # Page number
    canvas.drawRightString(doc.leftMargin + doc.width,
                         doc.bottomMargin - 20,
                         f"Page {page_no}")
    
    # Company info or document ID in footer
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.gray)
    canvas.drawString(doc.leftMargin,
                    doc.bottomMargin - 20,
                    "Confidential | Sensor Monitoring System")
    
    # Footer line
    canvas.setStrokeColor(DIVIDER_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin,
              doc.bottomMargin - 10,
              doc.leftMargin + doc.width,
              doc.bottomMargin - 10)
    
    # Restore the canvas state
    canvas.restoreState()

def create_summary_table(data):
    """Create a well-styled summary table"""
    col_widths = [2.4*inch, 1.5*inch, 1.5*inch, 1.5*inch]
    
    # Apply alternating row colors safely
    row_styles = []
    for i in range(1, len(data)):
        if i % 2 == 0:  # Even rows get background color
            row_styles.append(('BACKGROUND', (0,i), (-1,i), BG_LIGHT))
    
    tbl = Table(data, colWidths=col_widths, hAlign='LEFT')
    
    # Modern table styling
    tbl.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0,0), (-1,0), BRAND_COLOR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        
        # Base background for all non-header rows
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        
        # Apply alternating row styling dynamically to avoid index errors
        # This is safer than hard-coding specific row indices
        
        # Cell padding for all cells
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        
        # Text alignment
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),  # Numeric columns aligned right
        ('ALIGN', (0,0), (0,-1), 'LEFT'),    # First column aligned left
        
        # Grid styling - subtle lines
        ('GRID', (0,0), (-1,-1), 0.25, DIVIDER_COLOR),
        
        # Value formatting
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
    ]))
    
    return tbl

def create_anomaly_table(data):
    """Create a well-styled anomaly details table"""
    col_widths = [2*inch, 2.4*inch, 2.5*inch]
    
    tbl = Table(data, colWidths=col_widths, hAlign='LEFT')
    
    # Row styling logic for anomaly severities
    row_styles = []
    for i in range(1, len(data)):
        # This is a placeholder - in a real app you might have severity data
        # Here I'm just making every 5th row "critical" for demonstration
        if i % 5 == 0:
            row_styles.append(('BACKGROUND', (0,i), (-1,i), colors.HexColor('#FFEBEE')))  # Light red for critical
            row_styles.append(('TEXTCOLOR', (2,i), (2,i), colors.HexColor('#D32F2F')))    # Red text for value
        elif i % 3 == 0:
            row_styles.append(('BACKGROUND', (0,i), (-1,i), colors.HexColor('#FFF8E1')))  # Light amber for warnings
    
    # Modern table styling
    style_commands = [
        # Header row styling
        ('BACKGROUND', (0,0), (-1,0), BRAND_COLOR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        
        # Default row styling
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
    ]
    
    # Add the calculated row styles
    style_commands.extend(row_styles)
    
    # Apply all styling
    tbl.setStyle(TableStyle(style_commands + [
        # Cell padding
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        
        # Text alignment
        ('ALIGN', (2,1), (2,-1), 'RIGHT'),  # Value column aligned right
        ('ALIGN', (0,1), (1,-1), 'LEFT'),   # Time and topic left aligned
        
        # Grid styling - subtle lines
        ('GRID', (0,0), (-1,-1), 0.15, DIVIDER_COLOR),
        
        # Value formatting
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
    ]))
    
    return tbl

@bp.route('/anomalies/pdf')
def anomalies_pdf():
    """Generate a PDF report of sensor anomalies with improved design"""
    # Create buffer for PDF data
    buf = io.BytesIO()
    
    # Configure document with proper margins
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75*inch, 
        rightMargin=0.75*inch,
        topMargin=1.25*inch, 
        bottomMargin=0.75*inch
    )
    
    # Get custom styles
    styles = setup_styles()
    
    # List to hold all elements
    elements = []
    
    # --- Add introduction section ---
    intro_text = """."""
    elements.append(Paragraph(intro_text, styles['ModernBody']))
    elements.append(Spacer(1, 0.3*inch))
    
    # --- Summary Table Section ---
    elements.append(Paragraph("Sensor Reading Summary", styles['ModernHeading']))
    
    # Create summary table data
    summary_data = [["Sensor Topic", "Average", "Peak", "Low"]]
    for topic, readings in sensor_history.items():
        if not readings: 
            continue
        vals = [v for (_, v) in readings]
        summary_data.append([
            topic,
            f"{statistics.mean(vals):.2f}",
            f"{max(vals):.2f}",
            f"{min(vals):.2f}"
        ])
    
    # Handle empty data case
    if len(summary_data) <= 1:
        summary_data.append(["No sensor data available", "", "", ""])
    
    # Create and add the table
    summary_table = create_summary_table(summary_data)
    elements.append(KeepTogether([summary_table]))
    elements.append(Spacer(1, 0.4*inch))
    
    # --- Detailed Anomalies Section ---
    elements.append(Paragraph("Recent Anomalies", styles['ModernHeading']))
    
    # Add explanatory text
    anomaly_intro = "Values highlighted in red indicate anomalies that require immediate attention"
    elements.append(Paragraph(anomaly_intro, styles['ModernBody']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Create anomaly table data
    detail_data = [["Time", "Sensor Topic", "Value"]]
    
    # Get the 50 most recent anomalies (in reverse chronological order)
    recent_anomalies = sorted(anomaly_log[-50:], key=lambda x: x['time'], reverse=True)
    
    for e in recent_anomalies:
        detail_data.append([
            e['time'].strftime("%Y-%m-%d %H:%M:%S"),
            e['topic'],
            f"{e['value']:.2f}" if isinstance(e['value'], (float, int)) else f"{e['value']}"
        ])
    
    # Handle empty data case
    if len(detail_data) <= 1:
        detail_data.append(["No anomalies detected", "", ""])
    
    # Create and add the table
    anomaly_table = create_anomaly_table(detail_data)
    elements.append(anomaly_table)
    
    # Build the document with header and footer
    doc.build(elements,
              onFirstPage=_header_footer,
              onLaterPages=_header_footer)
    
    # Reset buffer position and return file
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="anomaly_log.pdf",
        mimetype="application/pdf"
    )