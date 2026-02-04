"""
Log Parser Service

Handles parsing of JSON, CSV, and XLSX log files into structured LogEntry objects.
"""

import json
import csv
import io
from typing import List, Dict, Any, Union
import pandas as pd
from ..models import LogEntry


def parse_json_logs(content: str) -> List[LogEntry]:
    """
    Parse JSON log content into LogEntry objects.
    
    Supports two formats:
    1. Array of entries: [{"user": "...", "human": "...", "agent": "..."}, ...]
    2. Single entry: {"user": "...", "human": "...", "agent": "..."}
    """
    try:
        data = json.loads(content)
        
        # Handle single entry
        if isinstance(data, dict):
            data = [data]
        
        entries = []
        for item in data:
            entry = LogEntry(
                user=item.get("user", ""),
                human=item.get("human", ""),
                agent=item.get("agent", ""),
                latency_ms=item.get("latency_ms")
            )
            entries.append(entry)
        
        return entries
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")


def parse_csv_logs(content: str) -> List[LogEntry]:
    """
    Parse CSV log content into LogEntry objects.
    
    Expected columns: user, human, agent, latency_ms (optional)
    """
    try:
        reader = csv.DictReader(io.StringIO(content))
        entries = []
        
        for row in reader:
            # Normalize column names (case-insensitive)
            row_lower = {k.lower().strip(): v for k, v in row.items()}
            
            entry = LogEntry(
                user=row_lower.get("user", ""),
                human=row_lower.get("human", ""),
                agent=row_lower.get("agent", ""),
                latency_ms=float(row_lower.get("latency_ms")) if row_lower.get("latency_ms") else None
            )
            entries.append(entry)
        
        return entries
    
    except Exception as e:
        raise ValueError(f"Invalid CSV format: {str(e)}")


def parse_xlsx_logs(content: bytes) -> List[LogEntry]:
    """
    Parse XLSX log content into LogEntry objects.
    
    Expected columns: user, human, agent, latency_ms (optional)
    """
    try:
        import io as bytes_io
        df = pd.read_excel(bytes_io.BytesIO(content))
        
        # Normalize column names (case-insensitive)
        df.columns = [col.lower().strip() for col in df.columns]
        
        entries = []
        for _, row in df.iterrows():
            entry = LogEntry(
                user=str(row.get("user", "")) if pd.notna(row.get("user")) else "",
                human=str(row.get("human", "")) if pd.notna(row.get("human")) else "",
                agent=str(row.get("agent", "")) if pd.notna(row.get("agent")) else "",
                latency_ms=float(row.get("latency_ms")) if pd.notna(row.get("latency_ms", None)) else None
            )
            entries.append(entry)
        
        return entries
    
    except Exception as e:
        raise ValueError(f"Invalid XLSX format: {str(e)}")


def parse_log_file(content: Union[str, bytes], filename: str) -> List[LogEntry]:
    """
    Parse log file content based on file extension.
    Supports JSON, CSV, and XLSX formats.
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        if isinstance(content, str):
            raise ValueError("XLSX files must be read as binary")
        return parse_xlsx_logs(content)
    elif filename_lower.endswith(".json"):
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return parse_json_logs(content)
    elif filename_lower.endswith(".csv"):
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return parse_csv_logs(content)
    else:
        # Try JSON first, then CSV
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        try:
            return parse_json_logs(content)
        except ValueError:
            try:
                return parse_csv_logs(content)
            except ValueError:
                raise ValueError("Unable to parse file. Please provide a valid JSON, CSV, or XLSX file.")


def validate_entries(entries: List[LogEntry]) -> List[str]:
    """
    Validate log entries and return list of warnings.
    """
    warnings = []
    
    for i, entry in enumerate(entries):
        if not entry.user.strip():
            warnings.append(f"Entry {i+1}: Missing user query")
        if not entry.human.strip():
            warnings.append(f"Entry {i+1}: Missing human response")
        if not entry.agent.strip():
            warnings.append(f"Entry {i+1}: Missing agent response")
    
    return warnings
