import os
import shutil
from pathlib import Path
from typing import Union, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory for uploads and processed files
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

async def save_upload_file(upload_file, destination: Path) -> str:
    """Save an uploaded file to the specified destination."""
    try:
        # Create the destination directory if it doesn't exist
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return str(destination)
    except Exception as e:
        logger.error(f"Error saving file {upload_file.filename}: {str(e)}")
        raise

def get_unique_filename(path: Union[str, Path]) -> Path:
    """Generate a unique filename by appending numbers if the file exists."""
    path = Path(path)
    if not path.exists():
        return path
        
    # If file exists, append a number to the filename
    counter = 1
    while True:
        new_path = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not new_path.exists():
            return new_path
        counter += 1