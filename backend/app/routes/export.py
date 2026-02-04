"""
Export Routes

Handles Excel export functionality.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

from ..models import MetricResult
from ..services.excel_export import create_excel_report
from .metrics import evaluation_cache
from .upload import get_filename_for_file

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{file_id}/excel")
async def export_to_excel(file_id: str):
    """
    Export evaluation results to Excel format.
    """
    # Check if evaluation exists
    if file_id not in evaluation_cache:
        raise HTTPException(
            status_code=404, 
            detail="No evaluation results found. Please evaluate the file first."
        )
    
    # Get cached results
    cached = evaluation_cache[file_id]
    filename = cached["filename"]
    metrics = [MetricResult(**m) for m in cached["metrics"]]
    
    # Generate Excel file
    try:
        excel_bytes = create_excel_report(metrics, filename, file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel: {str(e)}")
    
    # Create streaming response
    excel_stream = io.BytesIO(excel_bytes)
    
    # Generate export filename
    export_filename = f"evaluation_{filename.rsplit('.', 1)[0]}.xlsx"
    
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={export_filename}"
        }
    )
