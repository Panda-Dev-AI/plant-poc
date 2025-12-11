import os
from pathlib import Path
import torch
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from model import process_with_openai
from pdf_Convertor import convert_txt_to_pdf
from services.file_service import get_unique_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_processed_text(text: str, user_input: str) -> str:
    """
    Format the processed text with professional structure for PDF generation.
    Returns text optimized for reportlab PDF conversion.
    """
    from datetime import datetime

    if not text:
        return "No content available."

    # Split text into lines and clean up
    lines = text.split('\n')
    formatted_lines = []

    # Add professional document header
    formatted_lines.append(
        "<b><font name='Helvetica-Bold' size=18 color='#2c3e50'>"
        "ENGINEERING SPECIFICATION ANALYSIS"
        "</font></b>"
    )
    formatted_lines.append(
        f"<font name='Helvetica' size=14 color='#34495e'>"
        f"<i>Focus Area: {user_input}</i></font>"
    )
    formatted_lines.append(
        "<font name='Helvetica-Oblique' size=10 color='#7f8c8d'>"
        f"Generated on {datetime.now().strftime('%B %d, %Y')}"
        "</font>"
    )
    formatted_lines.append("<br/>")
    formatted_lines.append("<br/>")

    current_section = None
    bullet_points = False
    table_data = []
    in_table = False

    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append("<br/>")
            continue

        # Check for section headers
        if line.startswith("Section") or line.startswith("Focus:"):
            # Close any open table first
            if in_table and table_data:
                formatted_lines.append(create_table_html(table_data))
                table_data = []
                in_table = False
                formatted_lines.append("<br/>")

            # Add section header with professional styling
            formatted_lines.append("<br/>")
            formatted_lines.append(
                f"<b><font name='Helvetica-Bold' size=14 color='#2c3e50'>{line}</font></b>"
            )
            formatted_lines.append("<br/>")
            current_section = line
            bullet_points = False
            continue

        # Check for bullet points or numbered lists
        if (
            line.startswith("-")
            or line.startswith("*")
            or (line[0].isdigit() and "." in line[:5])
        ):
            # Close any open table
            if in_table and table_data:
                formatted_lines.append(create_table_html(table_data))
                table_data = []
                in_table = False
                formatted_lines.append("<br/>")

            clean_point = line.lstrip("-*0123456789. ")
            formatted_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&bull; {clean_point}")
            bullet_points = True

        # Check for key-value pairs (potential table data)
        elif ":" in line and not line.startswith("Section") and not line.startswith("Focus:"):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                table_data.append([key, value])
                in_table = True
                bullet_points = False

        # Regular paragraph content
        else:
            # Close any open table
            if in_table and table_data:
                formatted_lines.append(create_table_html(table_data))
                table_data = []
                in_table = False
                formatted_lines.append("<br/>")

            if bullet_points:
                formatted_lines.append("<br/>")
                bullet_points = False

            # Add paragraph with proper spacing
            formatted_lines.append(line)
            formatted_lines.append("<br/>")

    # Close any remaining table
    if in_table and table_data:
        formatted_lines.append(create_table_html(table_data))

    # Add professional footer
    formatted_lines.append("<br/>")
    formatted_lines.append("<br/>")
    formatted_lines.append("<hr/>")
    return "\n".join(formatted_lines)


def create_table_html(table_data):
    """
    Helper function to create HTML table for reportlab.
    """
    if not table_data:
        return ""

    table_html = "<table border=1 cellpadding=8 cellspacing=0 width='100%'>"

    for i, row in enumerate(table_data):
        if len(row) >= 2:
            bg_color = '#ecf0f1' if i % 2 == 0 else '#ffffff'
            table_html += "<tr>"
            table_html += f"<td bgcolor='{bg_color}'><b>{row[0]}</b></td>"
            table_html += f"<td bgcolor='{bg_color}'>{row[1]}</td>"
            table_html += "</tr>"

    table_html += "</table>"
    return table_html


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using Marker library with GPU acceleration."""
    try:
        # Check CUDA availability and GPU info
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"Current CUDA device: {torch.cuda.current_device()}")
            print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
            print(
                "CUDA memory allocated: "
                f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB"
            )
        else:
            print("CUDA not available - checking reasons:")
            print(f"PyTorch version: {torch.__version__}")
            print(f"PyTorch built with CUDA: {torch.cuda.is_built()}")

        # Set device to GPU if available
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {device}")

        # Add configuration to prevent tqdm issues
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'

        try:
            model_dict = create_model_dict()
            if model_dict is None:
                raise ValueError(
                    "Failed to create model dictionary - Marker models not properly initialized"
                )

            if torch.cuda.is_available():
                # Move model components to GPU
                for key in model_dict:
                    if model_dict[key] is not None and hasattr(model_dict[key], 'to'):
                        model_dict[key] = model_dict[key].to(device)

            converter = PdfConverter(artifact_dict=model_dict)

            # Convert PDF to text
            rendered = converter(pdf_path)
            text, _, _ = text_from_rendered(rendered)

            if not text:
                raise ValueError("No text could be extracted from the PDF")

            return text

        except AttributeError as ae:
            if 'disable_tqdm' in str(ae):
                # Specific handling for tqdm disable issue
                print("Encountered tqdm configuration issue, attempting fallback...")
                try:
                    from tqdm import tqdm
                    tqdm.disable = True

                    model_dict = create_model_dict()
                    if model_dict is None:
                        raise ValueError(
                            "Failed to create model dictionary in fallback mode"
                        )

                    converter = PdfConverter(artifact_dict=model_dict)
                    rendered = converter(pdf_path)
                    text, _, _ = text_from_rendered(rendered)

                    if not text:
                        raise ValueError(
                            "No text could be extracted from the PDF in fallback mode"
                        )

                    return text
                except Exception as fallback_error:
                    raise Exception(
                        f"Fallback extraction also failed: {str(fallback_error)}"
                    )
            else:
                raise ae

    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def process_pdf(
    input_pdf_path: str,
    user_input: str = "",
    combined_text: str = None
) -> tuple[str, str]:
    """
    Process a PDF, run it through OpenAI, and generate a formatted PDF.
    Returns (output_pdf_path_as_str, processed_text).
    """
    try:
        # If combined_text is not provided, extract text from the input file
        if combined_text is None:
            text = extract_text_from_pdf(input_pdf_path)
        else:
            text = combined_text

        # Process the text with OpenAI
        print("OPENAI Processing")
        processed_text = process_with_openai(text, user_input=user_input)

        # Format the processed text for PDF
        print("Formatting")
        formatted_text = format_processed_text(processed_text, user_input)

        # Generate output filename
        print("Generating output filename")
        input_path = Path(input_pdf_path)
        output_filename = f"{input_path.stem}_Specs.pdf"

        # Use pathlib for the processed directory
        processed_dir = Path("processed")
        processed_dir.mkdir(exist_ok=True)
        output_pdf_path = processed_dir / output_filename  # Path object

        # Save formatted text to a temporary file
        print("Saving formatted text to a temporary file")
        temp_txt = "temp_processed.txt"
        try:
            with open(temp_txt, "w", encoding="utf-8") as f:
                f.write(formatted_text)

            # Convert to PDF; ensure output path is a string
            print("Converting to PDF")
            convert_txt_to_pdf(temp_txt, str(output_pdf_path))

            # Return string paths instead of Path objects
            print("Returning string paths")
            return str(output_pdf_path), processed_text
        finally:
            # Cleanup temp file
            print("Cleanup temp file")
            if os.path.exists(temp_txt):
                os.remove(temp_txt)

    except Exception as e:
        logger.error(f"Error in process_pdf: {str(e)}")
        raise


def get_output_path(input_pdf_path: str) -> Path:
    """
    Generate output path for the processed PDF.

    Args:
        input_pdf_path: Path to the input PDF file

    Returns:
        Path: Output path for the processed PDF
    """
    input_path = Path(input_pdf_path)
    output_filename = f"{input_path.stem}_processed{input_path.suffix}"
    return Path("processed") / output_filename


def create_pdf_from_text(text: str, output_path: str) -> None:
    """
    Create a PDF from the given text.

    Args:
        text: Text content to convert to PDF
        output_path: Path where the PDF should be saved
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    # Normalize to Path and ensure directory exists
    output_path_obj = Path(output_path)
    output_dir = output_path_obj.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a PDF document
    doc = SimpleDocTemplate(str(output_path_obj), pagesize=letter)

    # Get default style
    styles = getSampleStyleSheet()
    style_normal = styles['Normal']

    # Create a custom style for better formatting
    custom_style = ParagraphStyle(
        'CustomStyle',
        parent=style_normal,
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    # Split text into paragraphs and create story
    story = []
    for line in text.split('\n'):
        if line.strip():
            p = Paragraph(line, custom_style)
            story.append(p)
            story.append(Spacer(1, 6))  # Add some space between paragraphs

    # Build the PDF
    doc.build(story)
