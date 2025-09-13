"""
FastAPI Server for Code Chat AI
Provides REST API endpoints for codebase analysis using AI.
"""

import os
import json
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

from cli_interface import CLIInterface
from logger import get_logger

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Code Chat AI API",
    description="REST API for analyzing codebases with AI assistance",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logger
logger = get_logger("fastapi")

# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    """Request model for codebase analysis."""
    folder: str = Field(..., description="Path to the codebase folder to analyze")
    question: str = Field(..., description="Question to ask about the codebase")
    model: Optional[str] = Field(None, description="AI model to use")
    provider: Optional[str] = Field(None, description="AI provider to use")
    api_key: Optional[str] = Field(None, description="API key (overrides .env)")
    system_prompt: Optional[str] = Field(None, description="System prompt file name")
    include: Optional[str] = Field(None, description="File patterns to include (comma-separated)")
    exclude: Optional[str] = Field(None, description="File patterns to exclude (comma-separated)")
    output: str = Field("structured", description="Output format: 'structured' or 'json'")
    save_to: Optional[str] = Field(None, description="Save output to file path")
    verbose: bool = Field(False, description="Enable verbose logging")

    @field_validator('provider')
    def validate_provider(cls, v):
        """Validate provider against available providers."""
        if v is not None:
            from ai import AIProviderFactory
            available = AIProviderFactory.get_available_providers()
            if v not in available:
                raise ValueError(f"Provider must be one of: {', '.join(available)}")
        return v

    @field_validator('output')
    def validate_output_format(cls, v):
        """Validate output format."""
        if v not in ['structured', 'json']:
            raise ValueError("Output format must be 'structured' or 'json'")
        return v

class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    response: str = Field(..., description="AI response content")
    model: str = Field(..., description="Model used for analysis")
    provider: str = Field(..., description="Provider used for analysis")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: str = Field(..., description="Timestamp of analysis")
    files_count: int = Field(..., description="Number of files analyzed")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")

# Global CLI interface instance
cli_interface = CLIInterface()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_codebase_json(request: AnalysisRequest):
    """
    Analyze a codebase with AI assistance (JSON body).

    This endpoint accepts parameters as JSON in the request body.
    Use this for programmatic access with structured data.

    Supports all CLI parameters including:
    - Dynamic provider selection from environment
    - File filtering with include/exclude patterns
    - Output formatting (structured/json)
    - Optional file saving
    - Verbose logging
    """
    return await _analyze_codebase_impl(
        folder=request.folder,
        question=request.question,
        model=request.model,
        provider=request.provider,
        api_key=request.api_key,
        system_prompt=request.system_prompt,
        include=request.include,
        exclude=request.exclude,
        output=request.output,
        save_to=request.save_to,
        verbose=request.verbose
    )

@app.get("/analyze", response_model=AnalysisResponse)
async def analyze_codebase_params(
    folder: str,
    question: str,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    output: str = "structured",
    save_to: Optional[str] = None,
    verbose: bool = False
):
    """
    Analyze a codebase with AI assistance (query parameters).

    This endpoint accepts parameters as URL query parameters.
    Use this for simple requests or when you prefer URL-based parameters.

    Args:
        folder: Path to the codebase folder to analyze
        question: Question to ask about the codebase
        model: AI model to use (optional)
        provider: AI provider to use (optional)
        api_key: API key override (optional)
        system_prompt: System prompt file name (optional)
        include: File patterns to include (optional)
        exclude: File patterns to exclude (optional)
        output: Output format ('structured' or 'json')
        save_to: Save output to file path (optional)
        verbose: Enable verbose logging (optional)
    """
    # Validate parameters
    if output not in ['structured', 'json']:
        raise HTTPException(
            status_code=400,
            detail="Output format must be 'structured' or 'json'"
        )

    if provider is not None:
        from ai import AIProviderFactory
        available = AIProviderFactory.get_available_providers()
        if provider not in available:
            raise HTTPException(
                status_code=400,
                detail=f"Provider must be one of: {', '.join(available)}"
            )

    return await _analyze_codebase_impl(
        folder=folder,
        question=question,
        model=model,
        provider=provider,
        api_key=api_key,
        system_prompt=system_prompt,
        include=include,
        exclude=exclude,
        output=output,
        save_to=save_to,
        verbose=verbose
    )

async def _analyze_codebase_impl(
    folder: str,
    question: str,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    output: str = "structured",
    save_to: Optional[str] = None,
    verbose: bool = False
):
    """
    Internal implementation for codebase analysis.
    Shared between JSON and parameter-based endpoints.
    """
    try:
        logger.info(f"Received analysis request for folder: {folder}")

        # Create a mock args object for CLI interface compatibility
        from argparse import Namespace

        args = Namespace()
        args.folder = folder
        args.question = question
        args.model = model
        args.provider = provider
        args.api_key = api_key
        args.system_prompt = system_prompt
        args.include = include
        args.exclude = exclude
        args.output = output
        args.verbose = verbose
        args.save_to = save_to

        # Load configuration
        config = cli_interface.load_configuration(args)

        # Setup AI processor
        if not cli_interface.setup_ai_processor(config):
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize AI processor. Check API key configuration."
            )

        # Setup system prompt
        if not cli_interface.setup_system_prompt(args.system_prompt):
            raise HTTPException(
                status_code=400,
                detail=f"System prompt '{args.system_prompt}' not found"
            )

        # Scan codebase
        files, codebase_content = cli_interface.scan_codebase(
            args.folder, args.include, args.exclude
        )

        if not files:
            raise HTTPException(
                status_code=400,
                detail="No files found in the specified folder after applying filters"
            )

        # Process question
        result = cli_interface.process_question(
            args.question, codebase_content, config['model']
        )

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to process question with AI"
            )

        # Add files count to result
        result['files_count'] = len(files)

        # Handle file saving if requested
        if save_to:
            try:
                from file_lock import safe_file_operation

                # Format output based on request
                if output == 'json':
                    output_content = json.dumps(result, indent=2, ensure_ascii=False)
                else:
                    # Create structured text output
                    lines = [
                        "# Code Chat AI - API Analysis Results",
                        "",
                        f"**Timestamp:** {result['timestamp']}",
                        f"**Model:** {result['model']}",
                        f"**Provider:** {result['provider']}",
                        f"**Processing Time:** {result['processing_time']:.2f}s",
                        f"**Files Analyzed:** {len(files)}",
                        "",
                        "## Question",
                        f"{question}",
                        "",
                        "## Response",
                        "",
                        result['response']
                    ]
                    output_content = '\n'.join(lines)

                # Save with file locking
                with safe_file_operation(save_to, timeout=10.0):
                    with open(save_to, 'w', encoding='utf-8') as f:
                        f.write(output_content)

                logger.info(f"Results saved to: {save_to}")

            except Exception as e:
                logger.warning(f"Failed to save results to file: {str(e)}")
                # Don't fail the request if file saving fails

        logger.info(f"Analysis completed successfully for {len(files)} files")

        return AnalysisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing analysis request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/models")
async def get_available_models():
    """Get list of available AI models."""
    try:
        # Load configuration to get available models
        load_dotenv()
        models_env = os.getenv('MODELS', '')
        if models_env:
            models = [m.strip() for m in models_env.split(',') if m.strip()]
        else:
            models = [
                "openai/gpt-3.5-turbo",
                "openai/gpt-4",
                "openai/gpt-4-turbo",
                "anthropic/claude-3-haiku",
                "anthropic/claude-3-sonnet"
            ]

        return {"models": models}

    except Exception as e:
        logger.exception(f"Error getting models: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve models: {str(e)}"
        )

@app.get("/providers")
async def get_available_providers():
    """Get list of available AI providers."""
    try:
        from ai import AIProviderFactory
        factory = AIProviderFactory()
        providers = factory.get_available_providers()
        return {"providers": providers}

    except Exception as e:
        logger.exception(f"Error getting providers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve providers: {str(e)}"
        )

@app.get("/system-prompts")
async def get_system_prompts():
    """Get list of available system prompt files."""
    try:
        from system_message_manager import system_message_manager
        files_info = system_message_manager.get_system_message_files_info()

        prompts = []
        for file_info in files_info:
            prompts.append({
                "name": file_info['display_name'],
                "filename": file_info['filename'],
                "is_current": file_info['is_current']
            })

        return {"system_prompts": prompts}

    except Exception as e:
        logger.exception(f"Error getting system prompts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve system prompts: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")

    print(f"Starting FastAPI server on {host}:{port}")
    print(f"API documentation available at: http://{host}:{port}/docs")

    uvicorn.run(
        "fastapi_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )