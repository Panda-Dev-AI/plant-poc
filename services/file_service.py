import os
import shutil
from pathlib import Path
from typing import Optional

def ensure_directory(directory: Path) -> None:
    """Ensure the specified directory exists."""
    directory.mkdir(parents=True, exist_ok=True)

async def save_upload_file(upload_file, destination: Path) -> str:
    """
    Save uploaded file with a unique filename in the specified directory.
    
    Args:
        upload_file: The uploaded file object from FastAPI
        destination: Directory where the file should be saved
        
    Returns:
        str: Path to the saved file
    """
    try:
        ensure_directory(destination)
        
        # Get file extension and generate a unique filename
        file_extension = os.path.splitext(upload_file.filename)[1].lower()
        if file_extension != '.pdf':
            raise ValueError("Only PDF files are supported")
            
        unique_filename = f"{os.urandom(8).hex()}{file_extension}"
        file_path = destination / unique_filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return str(file_path)
    except Exception as e:
        raise Exception(f"Error saving uploaded file: {str(e)}")

def get_unique_filename(filepath: str) -> str:
    """
    Generate a unique filename by appending version numbers if the file exists.
    
    Args:
        filepath: The desired file path
        
    Returns:
        str: A unique file path with versioning if needed
    """
    if not os.path.exists(filepath):
        return filepath
        
    base, ext = os.path.splitext(filepath)
    base, ext = os.path.splitext(original_path)
    version = 1
    
    while True:
        new_path = f"{base}_v{version}{ext}"
        if not os.path.exists(new_path):
            return new_path
        version += 1