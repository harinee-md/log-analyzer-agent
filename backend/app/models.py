from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class LogEntry(BaseModel):
    """Single log entry with user, human, and agent responses"""
    user: str
    human: str
    agent: str
    latency_ms: Optional[float] = None


class LogFile(BaseModel):
    """Uploaded log file containing multiple entries"""
    id: str
    filename: str
    upload_time: datetime
    entries: List[LogEntry]
    entry_count: int


class MetricResult(BaseModel):
    """Result of a single metric evaluation"""
    metric_name: str
    metric_value: Any
    description: Optional[str] = None


class EvaluationResult(BaseModel):
    """Complete evaluation result for a log file"""
    log_file_id: str
    filename: str
    metrics: List[MetricResult]
    evaluated_at: datetime


class UploadHistory(BaseModel):
    """History entry for uploaded files"""
    id: str
    filename: str
    upload_time: datetime
    entry_count: int
    status: str  # 'processing', 'completed', 'failed'


class UploadResponse(BaseModel):
    """Response after file upload"""
    id: str
    filename: str
    message: str
    entry_count: int
