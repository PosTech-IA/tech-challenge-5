import json
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor


def generate_pdf_report(
    filename: str,
    created_at: datetime,
    result_data: str | dict
) -> bytes:
    """
    Generate a clean PDF report from analysis result data.

    Args:
        filename: Original uploaded filename
        created_at: Analysis creation timestamp
        result_data: JSON result data (string or dict)

    Returns:
        PDF file bytes
    """
    # Parse result data if it's a string
    if isinstance(result_data, str):
        try:
            data = json.loads(result_data)
        except Exception:
            data = {"raw": result_data}
    else:
        data = result_data

    # Create PDF document in memory
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    # Get styles and customize
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=0  # Left align
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#333333'),
        spaceAfter=10,
        spaceBefore=12
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#555555'),
        spaceAfter=6,
        leftIndent=0.25 * inch
    )

    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#888888'),
        spaceAfter=12
    )

    # Build document content
    story = []

    # Title
    story.append(Paragraph("Architecture Analysis Report", title_style))

    # Metadata
    formatted_date = created_at.strftime("%B %d, %Y at %H:%M") if created_at else "Unknown"
    story.append(Paragraph(f"<b>File:</b> {filename}", meta_style))
    story.append(Paragraph(f"<b>Generated:</b> {formatted_date}", meta_style))
    story.append(Spacer(1, 0.2 * inch))

    # Components section
    components = data.get("components", [])
    if components:
        story.append(Paragraph("Components", heading_style))
        if isinstance(components, list):
            for component in components:
                story.append(Paragraph(f"• {component}", normal_style))
        else:
            story.append(Paragraph(str(components), normal_style))
        story.append(Spacer(1, 0.15 * inch))

    # Risks section
    risks = data.get("risks", [])
    if risks:
        story.append(Paragraph("Identified Risks", heading_style))
        if isinstance(risks, list):
            for risk in risks:
                story.append(Paragraph(f"• {risk}", normal_style))
        else:
            story.append(Paragraph(str(risks), normal_style))
        story.append(Spacer(1, 0.15 * inch))

    # Recommendations section
    recommendations = data.get("recommendations", [])
    if recommendations:
        story.append(Paragraph("Recommendations", heading_style))
        if isinstance(recommendations, list):
            for recommendation in recommendations:
                story.append(Paragraph(f"• {recommendation}", normal_style))
        else:
            story.append(Paragraph(str(recommendations), normal_style))

    # Build PDF
    doc.build(story)

    # Get bytes and return
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
