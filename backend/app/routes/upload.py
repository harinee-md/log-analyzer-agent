"""
Upload Routes

Handles file upload and history management.
"""

import os
import uuid
import json
import aiofiles
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException

from ..models import UploadResponse, UploadHistory, LogEntry
from ..services.log_parser import parse_log_file, validate_entries

router = APIRouter(prefix="/api/upload", tags=["upload"])

# In-memory storage for upload history (would use database in production)
upload_history: List[dict] = []
uploaded_files: dict = {}  # id -> file content and entries

# Get uploads directory
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a JSON, CSV, or XLSX log file for evaluation.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    filename_lower = file.filename.lower()
    valid_extensions = (".json", ".csv", ".xlsx", ".xls")
    if not any(filename_lower.endswith(ext) for ext in valid_extensions):
        raise HTTPException(status_code=400, detail="Only JSON, CSV, and XLSX files are supported")
    
    # Read file content
    try:
        content = await file.read()
        is_excel = filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls")
        
        # For non-Excel files, decode to string for storage
        if not is_excel:
            content_str = content.decode("utf-8")
        else:
            content_str = None  # Excel files stored as binary
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Parse the log file (pass bytes for Excel, string for others)
    try:
        if is_excel:
            entries = parse_log_file(content, file.filename)
        else:
            entries = parse_log_file(content_str, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not entries:
        raise HTTPException(status_code=400, detail="No valid log entries found in file")
    
    # Validate entries
    warnings = validate_entries(entries)
    
    # Generate unique ID
    file_id = str(uuid.uuid4())
    upload_time = datetime.now()
    
    # Save file to disk
    file_path = os.path.join(UPLOADS_DIR, f"{file_id}_{file.filename}")
    if is_excel:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
    else:
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content_str)
    
    # Store in memory (store entries, not raw Excel binary)
    uploaded_files[file_id] = {
        "filename": file.filename,
        "content": content_str if not is_excel else "[Excel binary file]",
        "entries": [e.model_dump() for e in entries],
        "upload_time": upload_time.isoformat(),
        "file_path": file_path,
        "is_excel": is_excel
    }
    
    # Add to history
    upload_history.insert(0, {
        "id": file_id,
        "filename": file.filename,
        "upload_time": upload_time.isoformat(),
        "entry_count": len(entries),
        "status": "uploaded"
    })
    
    return UploadResponse(
        id=file_id,
        filename=file.filename,
        message=f"Successfully uploaded {len(entries)} log entries",
        entry_count=len(entries)
    )


@router.get("/history", response_model=List[UploadHistory])
async def get_upload_history():
    """
    Get list of previously uploaded files.
    """
    return [
        UploadHistory(
            id=item["id"],
            filename=item["filename"],
            upload_time=datetime.fromisoformat(item["upload_time"]),
            entry_count=item["entry_count"],
            status=item["status"]
        )
        for item in upload_history
    ]


@router.get("/{file_id}")
async def get_uploaded_file(file_id: str):
    """
    Get details of an uploaded file.
    """
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = uploaded_files[file_id]
    return {
        "id": file_id,
        "filename": file_data["filename"],
        "entry_count": len(file_data["entries"]),
        "upload_time": file_data["upload_time"],
        "entries": file_data["entries"]
    }


@router.delete("/{file_id}")
async def delete_uploaded_file(file_id: str):
    """
    Delete an uploaded file.
    """
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from disk
    file_data = uploaded_files[file_id]
    if os.path.exists(file_data["file_path"]):
        os.remove(file_data["file_path"])
    
    # Remove from memory
    del uploaded_files[file_id]
    
    # Remove from history
    global upload_history
    upload_history = [h for h in upload_history if h["id"] != file_id]
    
    return {"message": "File deleted successfully"}


def get_entries_for_file(file_id: str) -> List[LogEntry]:
    """
    Get parsed log entries for a file ID.
    Used by other routes.
    """
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = uploaded_files[file_id]
    return [LogEntry(**entry) for entry in file_data["entries"]]


def get_filename_for_file(file_id: str) -> str:
    """Get filename for a file ID."""
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    return uploaded_files[file_id]["filename"]
