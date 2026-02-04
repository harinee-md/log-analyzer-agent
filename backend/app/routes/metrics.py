"""
Metrics Routes

Handles metric evaluation and retrieval.
"""

import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from ..models import MetricResult, EvaluationResult
from ..services.evaluator import MetricEvaluator
from .upload import get_entries_for_file, get_filename_for_file

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Cache for evaluation results
evaluation_cache: dict = {}


@router.post("/{file_id}/evaluate", response_model=EvaluationResult)
async def evaluate_log_file(file_id: str, force: bool = Query(False, description="Force re-evaluation")):
    """
    Evaluate a log file and return all metrics.
    Results are cached unless force=True.
    """
    # Check cache first
    if file_id in evaluation_cache and not force:
        cached = evaluation_cache[file_id]
        return EvaluationResult(
            log_file_id=file_id,
            filename=cached["filename"],
            metrics=[MetricResult(**m) for m in cached["metrics"]],
            evaluated_at=datetime.fromisoformat(cached["evaluated_at"])
        )
    
    # Get entries
    try:
        entries = get_entries_for_file(file_id)
        filename = get_filename_for_file(file_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GOOGLE_API_KEY not configured. Please set the environment variable."
        )
    
    # Run evaluation
    try:
        evaluator = MetricEvaluator(api_key=api_key)
        metrics = evaluator.evaluate_all(entries)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    
    # Cache results
    evaluated_at = datetime.now()
    evaluation_cache[file_id] = {
        "filename": filename,
        "metrics": [m.model_dump() for m in metrics],
        "evaluated_at": evaluated_at.isoformat()
    }
    
    return EvaluationResult(
        log_file_id=file_id,
        filename=filename,
        metrics=metrics,
        evaluated_at=evaluated_at
    )


@router.get("/{file_id}", response_model=Optional[EvaluationResult])
async def get_evaluation_results(file_id: str):
    """
    Get cached evaluation results for a file.
    Returns None if not evaluated yet.
    """
    if file_id not in evaluation_cache:
        return None
    
    cached = evaluation_cache[file_id]
    return EvaluationResult(
        log_file_id=file_id,
        filename=cached["filename"],
        metrics=[MetricResult(**m) for m in cached["metrics"]],
        evaluated_at=datetime.fromisoformat(cached["evaluated_at"])
    )


@router.get("/{file_id}/status")
async def get_evaluation_status(file_id: str):
    """
    Check if a file has been evaluated.
    """
    return {
        "file_id": file_id,
        "evaluated": file_id in evaluation_cache,
        "evaluated_at": evaluation_cache[file_id]["evaluated_at"] if file_id in evaluation_cache else None
    }
