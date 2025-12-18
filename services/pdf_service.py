# pdf_service.py - UPDATED (remove decorative separators)
import os
from pathlib import Path
import re
import torch
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from model import process_with_openai
from pdf_Convertor import text_to_pdf
from services.file_service import get_unique_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_processed_text(text: str, user_input: str) -> str:
    """
    Take OpenAI output and turn it into CLEAN PLAIN TEXT (no HTML) 
    NO decorative separators like dashes or n's
    """
    from datetime import datetime

    if not text:
        return "No content available."

    # Strip any LLM HTML / ReportLab markup completely
    text = re.sub(r'<[^>]*>', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&bull;', '•')
    text = text.replace('\u2011', '-')  # non‑breaking hyphen
    text = text.replace('\u2013', '-')  # en dash
    text = text.replace('\u2014', '-')  # em dash

    lines = [line.strip() for line in text.split('\n') if line.strip()]

    formatted: list[str] = []
    
    # Header block
    formatted.append("ENGINEERING SPECIFICATION ANALYSIS")
    formatted.append(f"Focus Area: {user_input if user_input else 'Entire Document'}")
    formatted.append(f"Generated on {datetime.now().strftime('%B %d, %Y')}")
    formatted.append("")

    for line in lines:
        l = line.strip()
        if not l:
            continue

        lower = l.lower()

        # Section-like lines (NO dashes underneath)
        if any(kw in lower for kw in [
            "purpose and scope",
            "applicable codes",
            "design and performance",
            "material and component",
            "loads, allowables",
            "loads and allowables",
            "execution, testing",
            "execution requirements",
            "client inputs",
            "client requirements"
        ]):
            formatted.append("")
            formatted.append(l)  # NO dashes, just the line

        # Subsection-like lines
        elif any(kw in lower for kw in [
            "requirements:", "standard:", "standards:",
            "specification:", "specifications:",
            "data:", "table", "note:"
        ]):
            formatted.append("")
            formatted.append(f"[SUBSECTION] {l}")

        # Bullet-ish lines (including numbered)
        elif l.startswith(("•", "-", "*")) or (l[:3].isdigit() and l[3:4] in {".", ")"}):
            clean = re.sub(r'^[\-\*\•\d\)\.\s]+', '', l).strip()
            formatted.append(f"  • {clean}")

        # Source / reference lines
        elif "(from" in lower:
            formatted.append(f"    [SOURCE] {l}")

        else:
            formatted.append(l)

    formatted.append("")
    # NO decorative nnnnn or dashes - just simple END marker
    formatted.append("END OF ENGINEERING SPECIFICATION ANALYSIS")

    return "\n".join(formatted)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using Marker with GPU if available."""
    try:
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

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {device}")

        os.environ['TOKENIZERS_PARALLELISM'] = 'false'

        try:
            model_dict = create_model_dict()
            if model_dict is None:
                raise ValueError(
                    "Failed to create model dictionary - Marker models not initialized"
                )

            if torch.cuda.is_available():
                for key in model_dict:
                    if model_dict[key] is not None and hasattr(model_dict[key], "to"):
                        model_dict[key] = model_dict[key].to(device)

            converter = PdfConverter(artifact_dict=model_dict)
            rendered = converter(pdf_path)
            text, _, _ = text_from_rendered(rendered)

            if not text:
                raise ValueError("No text could be extracted from the PDF")

            return text

        except AttributeError as ae:
            if "disable_tqdm" in str(ae):
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
    Process a PDF, run it through OpenAI, and generate a styled PDF.
    Returns (output_pdf_path_as_str, processed_text).
    """
    try:
        # 1. Extract or reuse text
        if combined_text is None:
            text = extract_text_from_pdf(input_pdf_path)
        else:
            text = combined_text

        # 2. OpenAI processing
        print("OPENAI Processing")
        processed_text = process_with_openai(text, user_input=user_input)

        # 3. Format as clean plain text
        print("Formatting")
        formatted_text = format_processed_text(processed_text, user_input)

        # 4. Output path
        print("Generating output filename")
        input_path = Path(input_pdf_path)
        output_filename = f"{input_path.stem}_Specs.pdf"
        processed_dir = Path("processed")
        processed_dir.mkdir(exist_ok=True)
        output_pdf_path = processed_dir / output_filename

        # 5. Direct text → PDF (no temp HTML)
        print("Converting to PDF")
        text_to_pdf(formatted_text, str(output_pdf_path))

        print("Returning string paths")
        return str(output_pdf_path), processed_text

    except Exception as e:
        logger.error(f"Error in process_pdf: {str(e)}")
        raise


def get_output_path(input_pdf_path: str) -> Path:
    """Generate output path for a processed PDF."""
    input_path = Path(input_pdf_path)
    output_filename = f"{input_path.stem}_processed{input_path.suffix}"
    return Path("processed") / output_filename


def convert_txt_to_pdf(text: str, output_path: str) -> None:
    """
    Legacy helper: simple text → PDF without styling.
    Kept in case you still use it elsewhere.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    output_path_obj = Path(output_path)
    output_dir = output_path_obj.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output_path_obj), pagesize=letter)

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]

    custom_style = ParagraphStyle(
        "CustomStyle",
        parent=style_normal,
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )

    story = []
    for line in text.split("\n"):
        if line.strip():
            p = Paragraph(line, custom_style)
            story.append(p)
            story.append(Spacer(1, 6))

    doc.build(story)
