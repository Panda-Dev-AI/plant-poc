# pdf_Convertor.py - UPDATED (cleaner, no dashes under sections)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from datetime import datetime
import re


class HeaderFooterCanvas(canvas.Canvas):
    """Custom canvas class to add professional headers, footers, and page numbers."""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    def showPage(self):
        """Override showPage to save page state."""
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Override save to add headers and footers before final save."""
        num_pages = len(self.pages)
        for page in range(num_pages):
            self.__dict__.update(self.pages[page])
            self.draw_header_footer(page + 1, num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, page_num, total_pages):
        """Draw professional header and footer on each page."""
        self.saveState()

        # ===== HEADER =====
        self.setStrokeColorRGB(0.2, 0.4, 0.6)  # Professional blue
        self.setLineWidth(1.5)
        self.line(
            40, self._pagesize[1] - 60,
            self._pagesize[0] - 40, self._pagesize[1] - 60
        )

        self.setFont("Helvetica-Bold", 11)
        self.setFillColorRGB(0.2, 0.4, 0.6)
        self.drawString(50, self._pagesize[1] - 45, "Plant Design Document Analysis")

        self.setFont("Helvetica", 9)
        self.setFillColorRGB(0.5, 0.5, 0.5)
        self.drawRightString(
            self._pagesize[0] - 50,
            self._pagesize[1] - 45,
            "Engineering Specification Report",
        )

        # ===== FOOTER =====
        self.setStrokeColorRGB(0.2, 0.4, 0.6)
        self.setLineWidth(1.5)
        self.line(40, 50, self._pagesize[0] - 40, 50)

        self.setFont("Helvetica", 9)
        self.setFillColorRGB(0.3, 0.3, 0.3)
        page_text = f"Page {page_num} of {total_pages}"
        page_width = self.stringWidth(page_text, "Helvetica", 9)
        self.drawString((self._pagesize[0] - page_width) / 2, 32, page_text)

        self.setFont("Helvetica", 8)
        self.setFillColorRGB(0.6, 0.6, 0.6)
        date_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.drawString(50, 32, date_text)
        self.drawRightString(self._pagesize[0] - 50, 32, "Confidential")

        self.restoreState()


def create_styled_document(text_content: str, pdf_file: str):
    """
    Convert CLEAN text content to a styled, professional PDF.
    No decorative separators - clean and professional.
    """

    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        leftMargin=60,
        rightMargin=60,
        topMargin=90,
        bottomMargin=70,
        title="Engineering Specification Report",
    )

    styles = getSampleStyleSheet()

    # Title style - main report title
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        spaceAfter=6,
        textColor=colors.HexColor("#1a4d7a"),
        alignment=TA_CENTER,
    )

    # Subtitle style
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=11,
        leading=14,
        spaceAfter=18,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
    )

    # Section header style - blue band (CLEAN, no dashes)
    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        spaceAfter=12,
        spaceBefore=18,
        textColor=colors.HexColor("#ffffff"),
        alignment=TA_LEFT,
        backColor=colors.HexColor("#2c5aa0"),
        leftIndent=0,
    )

    # Subsection header style
    subsection_style = ParagraphStyle(
        "SubsectionHeader",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceAfter=8,
        spaceBefore=12,
        textColor=colors.HexColor("#2c5aa0"),
        alignment=TA_LEFT,
    )

    # Body text style
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        spaceAfter=6,
        spaceBefore=0,
        textColor=colors.HexColor("#333333"),
        alignment=TA_LEFT,
    )

    # Bullet point style
    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        spaceAfter=4,
        spaceBefore=0,
        textColor=colors.HexColor("#333333"),
        leftIndent=25,
        bulletIndent=15,
        alignment=TA_LEFT,
    )

    # Source reference style
    source_style = ParagraphStyle(
        "SourceReference",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        spaceAfter=4,
        spaceBefore=0,
        textColor=colors.HexColor("#666666"),
        alignment=TA_LEFT,
        leftIndent=25,
    )

    # Metadata style
    metadata_style = ParagraphStyle(
        "Metadata",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        spaceAfter=24,
        textColor=colors.HexColor("#777777"),
        alignment=TA_CENTER,
    )

    # End marker style
    end_marker_style = ParagraphStyle(
        "EndMarker",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=0,
        textColor=colors.HexColor("#2c5aa0"),
    )

    story = []

    # ===== TITLE PAGE =====
    story.append(Spacer(1, 60))
    story.append(Paragraph("Engineering Specification Report", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Plant Design Document Analysis", subtitle_style))
    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}",
            metadata_style,
        )
    )
    story.append(Spacer(1, 60))
    story.append(PageBreak())

    # ===== PROCESS CONTENT (plain text) =====
    lines = text_content.split("\n")

    section_keywords = [
        "purpose and scope",
        "applicable codes",
        "design and performance",
        "material and component",
        "material and component specifications",
        "loads, allowables",
        "loads and allowables",
        "execution, testing",
        "execution requirements",
        "client inputs",
        "client requirements",
    ]

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue

        lower = line.lower()

        # Section header (NO decorative dashes)
        if any(lower.startswith(kw) or kw in lower[:40] for kw in section_keywords):
            story.append(Spacer(1, 8))
            story.append(Paragraph(line, section_header_style))
            story.append(Spacer(1, 6))

        # Our artificial subsection tag from formatter
        elif line.startswith("[SUBSECTION] "):
            clean = line.replace("[SUBSECTION]", "").strip()
            story.append(Paragraph(clean, subsection_style))
            story.append(Spacer(1, 4))

        # Bullets
        elif line.startswith("•") or line.startswith("  •"):
            clean_line = line.lstrip(" •").strip()
            story.append(Paragraph(f"• {clean_line}", bullet_style))
            story.append(Spacer(1, 2))

        # Marked sources
        elif line.startswith("[SOURCE] ") or line.strip().startswith("    [SOURCE]"):
            clean = line.replace("[SOURCE]", "").strip()
            story.append(Paragraph(clean, source_style))
            story.append(Spacer(1, 2))

        # "END OF ..." - clean, NO decorative nnnnn or dashes
        elif line.startswith("END OF"):
            story.append(Spacer(1, 20))
            story.append(Paragraph(line, end_marker_style))

        # Regular body text
        else:
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 4))

    # Build
    doc.build(story, canvasmaker=HeaderFooterCanvas)
    print(f"✓ Professional PDF report created successfully: {pdf_file}")
    return pdf_file


def convert_txt_to_pdf(input_file, output_file):
    """Convert text file to beautifully formatted PDF report."""
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            content = file.read()
        create_styled_document(content, output_file)
    except Exception as e:
        print(f"Error in convert_txt_to_pdf: {str(e)}")
        raise


def text_to_pdf(text_content: str, pdf_file: str):
    """Convert raw text content directly to a beautifully formatted PDF report."""
    try:
        create_styled_document(text_content, pdf_file)
    except Exception as e:
        print(f"Error in text_to_pdf: {str(e)}")
        raise
