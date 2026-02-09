"""
Pipeline Routes

Handles the new hybrid pipeline for log analysis.
"""

import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
import pandas as pd
import io

from ..services.pipeline import LogAnalyzerPipeline
from ..services.evaluator import MetricEvaluator

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Cache for pipeline results
pipeline_cache: dict = {}


def get_evaluator() -> Optional[MetricEvaluator]:
    """Get LLM evaluator if API key is configured"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return MetricEvaluator(api_key=api_key)
    return None


@router.post("/analyze")
async def analyze_log_file(
    file: UploadFile = File(...),
    use_llm: bool = Query(True, description="Whether to use LLM for semantic metrics")
):
    """
    Analyze a log file through the full hybrid pipeline.
    
    Stages:
    1. Ingestion + Cleaning
    2. Data Normalization
    3. Rule-Based Feature Extraction
    4. Ground Truth Extraction
    5. Hybrid Metric Computation
    6. Binary Labeling (TP/TN/FP/FN)
    7. Metric Normalization (0-1)
    8. Aggregation (turn/conversation/scenario)
    
    Returns aggregated results at all levels.
    """
    # Read file content
    content = await file.read()
    filename = file.filename or "unknown"
    
    try:
        # Parse to DataFrame
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(content))
        elif filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    # Initialize pipeline
    evaluator = get_evaluator() if use_llm else None
    pipeline = LogAnalyzerPipeline(evaluator=evaluator)
    
    try:
        # Run pipeline
        results = pipeline.process_dataframe(df, use_llm_metrics=use_llm)
        
        # Convert to JSON
        output = pipeline.to_json(results)
        output["filename"] = filename
        output["analyzed_at"] = datetime.now().isoformat()
        output["llm_enabled"] = use_llm
        
        # Cache results
        file_id = f"pipeline_{datetime.now().timestamp()}"
        pipeline_cache[file_id] = output
        output["file_id"] = file_id
        
        return output
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@router.get("/{file_id}/results")
async def get_pipeline_results(file_id: str):
    """
    Get cached pipeline results.
    """
    if file_id not in pipeline_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    
    return pipeline_cache[file_id]


@router.get("/{file_id}/conversation/{conv_id}")
async def get_conversation_details(file_id: str, conv_id: str):
    """
    Get detailed metrics for a specific conversation.
    """
    if file_id not in pipeline_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = pipeline_cache[file_id]
    
    for conv in results.get("conversation_level", []):
        if conv["id"] == conv_id:
            return conv
    
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/{file_id}/scenarios")
async def get_scenario_breakdown(file_id: str):
    """
    Get scenario-level aggregation.
    """
    if file_id not in pipeline_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = pipeline_cache[file_id]
    return {
        "scenarios": results.get("scenario_level", []),
        "total_conversations": results.get("total_conversations", 0)
    }


@router.get("/{file_id}/labels")
async def get_label_distribution(file_id: str):
    """
    Get binary label distribution (TP/TN/FP/FN).
    """
    if file_id not in pipeline_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = pipeline_cache[file_id]
    overall = results.get("overall", {})
    
    return {
        "label_distribution": overall.get("label_distribution", {}),
        "total_conversations": results.get("total_conversations", 0)
    }
