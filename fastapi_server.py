#!/usr/bin/env python3
"""
FastAPI Server for Code Chat AI

This module provides a REST API server for the Code Chat AI application,
exposing AI processing and codebase analysis capabilities through HTTP endpoints.

Features:
- RESTful API for code analysis
- Multiple AI provider support
- File scanning and content processing
- CORS support for web frontend
- Comprehensive error handling
- Health check endpoint

Endpoints:
- GET /health - Server health check
- GET /models - List available AI models
- GET /providers - List available AI providers
- GET /system-prompts - List available system prompts
- POST /analyze - Perform code analysis

Usage:
    python fastapi_server.py

The server will start on http://localhost:8000 by default.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import local modules
from ai import create_ai_processor, AIProviderFactory
from file_scanner import CodebaseScanner
from lazy_file_scanner import LazyCodebaseScanner
from env_manager import EnvManager
from logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize environment manager
env_manager = EnvManager()

# Create FastAPI app
app = FastAPI(
    title="Code Chat AI API",
    description="REST API for Code Chat AI - Advanced codebase analysis with AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    """Request model for code analysis."""
    folder: str = Field(..., description="Path to the codebase folder")
    question: str = Field(..., description="Question about the codebase")
    model: str = Field(default="gpt-3.5-turbo", description="AI model to use")
    provider: str = Field(default="openrouter", description="AI provider to use")
    include: Optional[str] = Field(default="*.py,*.js,*.ts,*.java,*.cpp,*.c,*.h", description="File patterns to include")
    exclude: Optional[str] = Field(default="test_*,__pycache__,*.pyc,node_modules,venv,.venv", description="File patterns to exclude")
    output: str = Field(default="structured", description="Output format")
    api_key: Optional[str] = Field(default=None, description="API key (optional, uses environment)")

class AnalysisResponse(BaseModel):
    """Response model for code analysis."""
    response: str = Field(..., description="AI analysis response")
    model: str = Field(..., description="Model used for analysis")
    provider: str = Field(..., description="Provider used for analysis")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: str = Field(..., description="Response timestamp")
    files_count: int = Field(..., description="Number of files processed")

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Server status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")

class ModelsResponse(BaseModel):
    """Available models response."""
    models: List[str] = Field(..., description="List of available models")
    default: str = Field(..., description="Default model")

class ProvidersResponse(BaseModel):
    """Available providers response."""
    providers: List[str] = Field(..., description="List of available providers")
    default: str = Field(..., description="Default provider")

# Global variables
ai_processor = None
scanner = None
lazy_scanner = None

def initialize_components():
    """Initialize AI processor and scanners."""
    global ai_processor, scanner, lazy_scanner

    try:
        # Initialize scanners
        scanner = CodebaseScanner()
        lazy_scanner = LazyCodebaseScanner()

        # Get API key from environment
        env_vars = env_manager.load_env_file()
        api_key = env_vars.get("API_KEY", "")
        provider = env_vars.get("DEFAULT_PROVIDER", "openrouter")

        if not api_key:
            logger.warning("No API_KEY found in environment variables")
            return False

        # Initialize AI processor
        ai_processor = create_ai_processor(api_key=api_key, provider=provider)
        logger.info(f"Initialized AI processor with provider: {provider}")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    if not initialize_components():
        logger.warning("Some components failed to initialize - API may not work fully")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/models", response_model=ModelsResponse)
async def get_models():
    """Get available AI models."""
    try:
        if not ai_processor:
            raise HTTPException(status_code=503, detail="AI processor not initialized")

        # Get provider info which includes available models
        provider_info = ai_processor.get_provider_info()
        models = provider_info.get("models", [])

        return ModelsResponse(
            models=models,
            default=provider_info.get("default_model", "gpt-3.5-turbo")
        )

    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """Get available AI providers."""
    try:
        providers = AIProviderFactory.get_available_providers()
        env_vars = env_manager.load_env_file()
        default_provider = env_vars.get("DEFAULT_PROVIDER", "openrouter")

        return ProvidersResponse(
            providers=providers,
            default=default_provider
        )

    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system-prompts")
async def get_system_prompts():
    """Get available system prompts."""
    try:
        # This would typically read from a configuration file
        # For now, return a simple list
        prompts = [
            {"id": "default", "name": "Default", "description": "General code analysis"},
            {"id": "security", "name": "Security Review", "description": "Security-focused analysis"},
            {"id": "performance", "name": "Performance", "description": "Performance optimization"},
            {"id": "architecture", "name": "Architecture", "description": "System architecture review"}
        ]

        return {"prompts": prompts}

    except Exception as e:
        logger.error(f"Error getting system prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_code(request: AnalysisRequest):
    """Analyze codebase with AI."""
    start_time = datetime.now()

    try:
        if not ai_processor:
            raise HTTPException(status_code=503, detail="AI processor not initialized")

        # Validate directory
        if not scanner:
            raise HTTPException(status_code=503, detail="File scanner not initialized")

        is_valid, error_msg = scanner.validate_directory(request.folder)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid directory: {error_msg}")

        # Set API key if provided
        if request.api_key:
            ai_processor.set_api_key(request.api_key)

        # Set provider if different
        if request.provider != ai_processor.provider:
            ai_processor.set_provider(request.provider)

        # Scan directory for files
        logger.info(f"Scanning directory: {request.folder}")
        files = scanner.scan_directory(request.folder)

        if not files:
            raise HTTPException(status_code=400, detail="No supported files found in directory")

        # Filter files based on include/exclude patterns
        if request.include or request.exclude:
            filtered_files = []
            include_patterns = [p.strip() for p in request.include.split(',')] if request.include else []
            exclude_patterns = [p.strip() for p in request.exclude.split(',')] if request.exclude else []

            for file_path in files:
                filename = os.path.basename(file_path)

                # Check include patterns
                if include_patterns:
                    if not any(pattern in filename for pattern in include_patterns):
                        continue

                # Check exclude patterns
                if exclude_patterns:
                    if any(pattern in filename for pattern in exclude_patterns):
                        continue

                filtered_files.append(file_path)

            files = filtered_files

        logger.info(f"Processing {len(files)} files")

        # Get codebase content
        codebase_content = scanner.get_codebase_content(files)

        # Process question with AI
        logger.info(f"Processing question with model: {request.model}")
        response = ai_processor.process_question(
            question=request.question,
            conversation_history=[],
            codebase_content=codebase_content,
            model=request.model
        )

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(".2f")

        return AnalysisResponse(
            response=response,
            model=request.model,
            provider=request.provider,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            files_count=len(files)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        processing_time = (datetime.now() - start_time).total_seconds()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="FastAPI Server for Code Chat AI")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    print("🚀 Starting Code Chat AI FastAPI Server")
    print(f"📡 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API documentation at: http://{args.host}:{args.port}/docs")
    print("=" * 50)

    uvicorn.run(
        "fastapi_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()