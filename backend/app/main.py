"""
Log Analyzer Agent - FastAPI Application

Main entry point for the backend API.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .routes import upload, metrics, export

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Log Analyzer Agent",
    description="Evaluates chatbot logs using LangChain with Google Gemini",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(metrics.router)
app.include_router(export.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Log Analyzer Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload": "/api/upload/",
            "history": "/api/upload/history",
            "evaluate": "/api/metrics/{file_id}/evaluate",
            "export": "/api/export/{file_id}/excel"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    api_key_set = bool(os.getenv("GOOGLE_API_KEY"))
    return {
        "status": "healthy",
        "api_key_configured": api_key_set
    }
