import os
import logging
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

# Local imports
from services.file_service import save_upload_file, get_unique_filename
from services.pdf_service import (
    process_pdf,
    extract_text_from_pdf,
    process_with_openai,
    format_processed_text,
    convert_txt_to_pdf
)

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
    files: list[UploadFile] = File(..., description="PDF files to process"),
    user_input: str = Form("", description="Additional input text to include in processing")
):
    """
    Upload multiple PDF files for processing.
    
    The uploaded files will be processed as follows:
    1. Each file is saved to the uploads directory with a unique name
    2. Text is extracted from each file using Marker library
    3. Extracted text from all files is combined
    4. Combined text is processed by OpenAI with the user input
    5. Result is converted to a single PDF with '_Specs' suffix
    
    Returns:
        JSONResponse: Contains success status, message, and path to the processed PDF
    """
    try:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )

        logger.info(f"Received {len(files)} files for processing")
        
        saved_files = []
        all_processed_text = ""
        
        # Process each uploaded file
        for file in files:
            try:
                # 1. Save the uploaded file
                file_path = await save_upload_file(file, UPLOAD_DIR / file.filename)
                logger.info(f"File saved to: {file_path}")
                saved_files.append(file_path)
                
                # 2. Extract text from the file
                try:
                    processed_text = extract_text_from_pdf(file_path)
                    all_processed_text += f"\n\n--- File: {file.filename} ---\n{processed_text}"
                except Exception as e:
                    logger.error(f"Error extracting text from {file.filename}: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Error processing {file.filename}: {str(e)}"
                    )
                    
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                # Clean up any saved files if there's an error
                for f in saved_files:
                    try:
                        os.remove(f)
                    except:
                        pass
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing {file.filename}: {str(e)}"
                )
        
        try:
            # Process all files together with the user input
            output_pdf_path, processed_text = process_pdf(
                saved_files[0],  # Use first file's path for naming
                user_input=user_input,
                combined_text=all_processed_text
            )
            
            logger.info(f"Files processed successfully. Output: {output_pdf_path}")
            
            return JSONResponse(
                content={
                    "success": True,
                    "message": f"Successfully processed {len(files)} files",
                    "file_path": output_pdf_path,
                    "processed_text": processed_text
                }
            )
            
        except Exception as e:
            logger.error(f"Error in final processing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in final processing: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
@app.get("/download/")
async def download_file(output_pdf_path):
    try:
        return FileResponse(
            output_pdf_path,
            media_type="application/pdf",
            filename=os.path.basename(output_pdf_path)
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "upload_dir": str(UPLOAD_DIR.absolute()),
        "processed_dir": str(PROCESSED_DIR.absolute())
    }

def get_local_ip():
    """Get the local IP address for the network"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == "__main__":
    # Get local IP address
    host = '0.0.0.0'  # Listen on all network interfaces
    port = 8000
    local_ip = get_local_ip()
    
    print("\n" + "="*50)
    print(f"Backend server starting...")
    print(f"Local: http://127.0.0.1:{port}")
    print(f"Network: http://{local_ip}:{port}")
    print("="*50 + "\n")
    
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )