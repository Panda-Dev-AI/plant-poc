import os
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, status
import uvicorn

# Local imports
from services.file_service import save_upload_file
from services.pdf_service import process_pdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="PDF Processing API",
    description="API for processing PDF files through text extraction and AI analysis",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Form, File, UploadFile

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(..., description="PDF file to process"),
    user_input: str = Form("", description="Additional input text to include in processing")
):
    """
    Upload a PDF file for processing.
    
    The uploaded file will be processed as follows:
    1. Saved to the uploads directory with a unique name
    2. Text is extracted using Marker library
    3. Extracted text is processed by OpenAI
    4. Result is converted back to PDF with '_Specs' suffix
    5. Versioning is applied if file already exists
    
    Returns:
        FileResponse: The processed PDF file
    """
    try:
        logger.info(f"Received file upload: {file.filename}")
        
        # 1. Save the uploaded file
        try:
            file_path = await save_upload_file(file, UPLOAD_DIR)
            logger.info(f"File saved to: {file_path}")
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file: {str(e)}"
            )
        
        try:
            # Process the PDF with the additional user input
            output_pdf_path = process_pdf(file_path, user_input=user_input)
            logger.info(f"File processed successfully: {output_pdf_path}")
            
            # 5. Return the processed file
            return FileResponse(
                output_pdf_path,
                media_type="application/pdf",
                filename=os.path.basename(output_pdf_path)
            )
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing file: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "upload_dir": str(UPLOAD_DIR.absolute()),
        "processed_dir": str(PROCESSED_DIR.absolute())
    }

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )