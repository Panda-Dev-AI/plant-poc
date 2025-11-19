from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch
import re
from datetime import datetime
from reportlab.platypus import Frame, PageTemplate
from reportlab.pdfgen import canvas
import time

class PageNumberCanvas(canvas.Canvas):
    """Custom canvas class to add page numbers to PDF footer"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
    
    def showPage(self):
        """Override showPage to save page state"""
        self.pages.append(dict(self.__dict__))
        self._startPage()
    
    def save(self):
        """Override save to add page numbers before final save"""
        num_pages = len(self.pages)
        for page in range(num_pages):
            self.__dict__.update(self.pages[page])
            self.draw_page_number(page + 1, num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    
    def draw_page_number(self, page_num, total_pages):
        """Draw page number in footer"""
        self.saveState()
        self.setFont('Helvetica', 9)
        self.setFillColorRGB(0.58, 0.65, 0.65)  # #95a5a6
        self.drawCentredString(self._pagesize[0] / 2, 30, f"Page {page_num} of {total_pages}")
        self.restoreState()

def convert_txt_to_pdf(input_file, output_file):
    # Create a PDF document with margins
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        leftMargin=72,
        rightMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get default styles
    styles = getSampleStyleSheet()
    
    # Function to safely add or update style
    def add_or_update_style(name, **kwargs):
        if name in styles:
            for key, value in kwargs.items():
                setattr(styles[name], key, value)
        else:
            styles.add(ParagraphStyle(name=name, **kwargs))
    
    # Add or update styles
    add_or_update_style(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        spaceAfter=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER
    )
    
    add_or_update_style(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        spaceAfter=12,
        spaceBefore=24,
        textColor=colors.HexColor('#2c3e50'),
        borderPadding=5
    )
    
    add_or_update_style(
        'Normal_Spaced',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=8,
        textColor=colors.HexColor('#333333')
    )
    
    add_or_update_style(
        'Bullet',
        parent=styles['Normal'],
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=4,
        bulletIndent=10
    )
    
    # Subtitle style
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceAfter=20,
        spaceBefore=6,
        textColor=colors.HexColor('#34495e'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # Section header style
    section_style = ParagraphStyle(
        'CustomSection',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceAfter=12,
        spaceBefore=24,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    # Body text style - justified for professional look
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=6,
        spaceBefore=6,
        textColor=colors.black,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    # Date style
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        spaceAfter=30,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    # Footer style for page numbers
    footer_style = ParagraphStyle(
        name='FooterStyle',
        fontName='Helvetica',
        fontSize=9,
        textColor='#95a5a6',
        alignment=TA_CENTER,  # Center the text
    )
    
    # Read the input text file
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    
    # Create story (content container)
    story = []
    
    # Add title
    title = Paragraph("Plant Document Analysis", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 24))
    
    # Add metadata
    metadata = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    story.append(Paragraph(metadata, styles['Normal_Spaced']))
    story.append(Spacer(1, 36))  # Add space after metadata
    story.append(Paragraph("End of Engineering Analysis Report", footer_style))

    # Process each paragraph
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
        
        # Split paragraph into lines
        lines = paragraph.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            
            # Add the line as a justified paragraph
            story.append(Paragraph(line, body_style))

    # Add footer
    story.append(Paragraph("End of Engineering Analysis Report", footer_style))

    # Build the PDF with page numbering
    doc.build(story, canvasmaker=PageNumberCanvas)
    print(f"PDF created successfully: {output_file}")



def text_to_pdf(text_content: str, pdf_file: str):
    """Convert raw text content directly into a styled PDF file with bold subheadings and status labels."""

    styles = getSampleStyleSheet()
    
    # Normal style
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=11,
        leading=14,
        spaceAfter=10
    )

    # Bold style for subheadings and status
    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=11,
        leading=14,
        spaceAfter=10,
        textColor=colors.black
    )

    # Title style
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontName='Times-Bold',
        fontSize=16,
        spaceAfter=20,
        textColor=colors.black
    )

    # Create PDF
    doc = SimpleDocTemplate(
        pdf_file, 
        pagesize=A4, 
        rightMargin=40, 
        leftMargin=40, 
        topMargin=50, 
        bottomMargin=40
    )
    story = []

    # Add Title
    story.append(Paragraph("Engineering Specification Report", title_style))
    story.append(Spacer(1, 12))

    # Keywords for subheadings or competency
    bold_keywords = [
        "Section 1",
        "Section 2", 
        "Section 3",
    ]

    # Add text content line by line
    for line in text_content.split("\n"):
        if line.strip():
            # Check if line is a subheading or competency result
            if any(line.strip().startswith(keyword) for keyword in bold_keywords):
                story.append(Paragraph(line.strip(), bold_style))
            else:
                story.append(Paragraph(line.strip(), normal_style))
        else:
            story.append(Spacer(1, 6))

    doc.build(story)
    print(f" PDF saved to: {pdf_file}")

# if __name__ == "__main__":
#     # Test the original convert_txt_to_pdf function
#     input_file = "New_First_Draft_7.txt"
#     output_file = "New_First_Draft_7.pdf"
    
#     try:
#         convert_txt_to_pdf(input_file, output_file)
#     except Exception as e:
#         print(f"An error occurred in convert_txt_to_pdf: {str(e)}")
    
    # Test the new text_to_pdf function with sample content
#     sample_text = """Section 1: System Requirements
# This section outlines the technical specifications for the plant automation system.
# All components must meet industry standards.

# Section 2: Implementation Plan
# The system will be deployed in three phases.
# Each phase requires thorough testing.

# Section 3: Maintenance Protocol
# Regular maintenance schedules must be followed.
# All personnel must be trained on safety procedures.

# Knowledge evidence: Technical documentation completed.
# Performance evidence: All tests passed successfully.

# COMPETENT: System meets all requirements.
# FINAL GRADE: APPROVED"""
    
#     try:
#         text_to_pdf(sample_text, "engineering_specification_report.pdf")
#     except Exception as e:
#         print(f"An error occurred in text_to_pdf: {str(e)}")