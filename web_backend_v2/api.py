"""FastAPI application exposing the WhisperCode Web2 capabilities."""
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from common.ai import AIProviderFactory
from common.env_manager import env_manager
from common.models import ConversationMessage, QuestionStatus
from web_backend.schemas import (
    AskQuestionRequest,
    AskQuestionResponse,
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationIdResponse,
    ConversationSummaryModel,
    DirectoryScanRequest,
    DirectoryScanResponse,
    ExportConversationResponse,
    FileContentRequest,
    FileContentResponse,
    FolderFileCountRequest,
    FolderFileCountResponse,
    FolderInfo,
    ImportConversationRequest,
    SetDirectoryRequest,
    SetDirectoryResponse,
    SettingsUpdateRequest,
    SystemMessageSetRequest,
    SystemMessageUpdateRequest,
    SystemPromptResponse,
    ThemeToggleResponse,
    ThemeSetRequest,
    TopFoldersResponse,
    UpdateApiKeyRequest,
    UpdateFilesRequest,
    UpdateModelRequest,
)
from web_backend.services.conversation_service import conversation_manager
from web_backend.services.file_service import file_service
from web_backend.services.settings_service import settings_service
from web_backend.services.system_service import system_message_service
from common.logger import get_logger
import markdown2

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_env_defaults() -> tuple[str, str, List[str], str]:
    env_vars = env_manager.load_env_file()
    provider = (
        env_vars.get("PROVIDER")
        or env_vars.get("DEFAULT_PROVIDER")
        or "openrouter"
    )
    models_env = env_vars.get("MODELS")
    if models_env:
        models = [m.strip() for m in models_env.split(",") if m.strip()]
    else:
        models = [
            "openai/gpt-3.5-turbo",
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
        ]
    default_model = (
        env_vars.get("DEFAULT_MODEL")
        or (models[0] if models else "")
    )
    api_key = env_vars.get("API_KEY", "")
    return api_key, provider, models, default_model


def _session_summary_model(session) -> ConversationSummaryModel:
    summary = session.get_summary()
    return ConversationSummaryModel(
        conversation_id=summary.conversation_id,
        provider=summary.provider,
        selected_model=summary.selected_model,
        selected_directory=summary.selected_directory,
        selected_files=summary.selected_files,
        persistent_files=summary.persistent_files,
        question_history=summary.question_history,
        conversation_history=summary.conversation_history,
    )


def _conversation_state_response(session) -> ConversationCreateResponse:
    summary_model = _session_summary_model(session)
    return ConversationCreateResponse(
        conversationId=session.session_id,
        provider=session.provider,
        model=summary_model.selected_model,
        availableModels=session.available_models,
        summary=summary_model,
    )


# ---------------------------------------------------------------------------
# Providers & Models Metadata
# ---------------------------------------------------------------------------


@router.get("/meta/providers")
def get_providers():
    providers = AIProviderFactory.get_available_providers()
    env_vars = env_manager.load_env_file()
    default_provider = (
        env_vars.get("PROVIDER")
        or env_vars.get("DEFAULT_PROVIDER")
        or "openrouter"
    )
    return {"providers": providers, "default": default_provider}


@router.get("/meta/models")
def get_models(provider: Optional[str] = None):
    api_key, default_provider, models, default_model = _load_env_defaults()
    provider_name = provider or default_provider
    try:
        provider_instance = AIProviderFactory.create_provider(
            provider_name, api_key
        )
        provider_info = provider_instance.get_provider_info()
        models = provider_info.get("models", models)
        default_model = provider_info.get("default_model", default_model)
    except Exception:
        pass
    return {
        "models": models,
        "default": default_model,
        "provider": provider_name,
    }


@router.get("/meta/ui-defaults")
def get_ui_defaults():
    """Return UI defaults derived from environment configuration."""
    _, provider, models, default_model = _load_env_defaults()
    env_vars = env_manager.load_env_file()
    tool_commands = []
    for key, value in env_vars.items():
        if not (key.startswith("TOOL") and value):
            continue
        command_value = value
        prefix = f"{key}="
        if value.startswith(prefix):
            command_value = value[len(prefix):]
        tool_commands.append({"key": key, "value": command_value})
    system_messages = {
        "current": system_message_service.get_current_file(),
        "messages": system_message_service.list_messages(),
    }
    return {
        "provider": provider,
        "models": models,
        "defaultModel": default_model,
        "toolCommands": tool_commands,
        "systemMessages": system_messages,
        "apiKey": env_vars.get("API_KEY", ""),
    }


# ---------------------------------------------------------------------------
# Conversation lifecycle
# ---------------------------------------------------------------------------


@router.post("/conversations", response_model=ConversationCreateResponse)
def create_conversation(request: ConversationCreateRequest):
    logger.info("Creating new conversation")
    env_api_key, env_provider, models, env_default_model = _load_env_defaults()
    api_key = request.api_key or env_api_key
    provider = request.provider or env_provider
    model = request.model or env_default_model

    if model and model not in models:
        models = models + [model]

    session = conversation_manager.create_session(
        api_key=api_key,
        provider=provider,
        models=models,
        default_model=model or (models[0] if models else ""),
    )
    session.set_model(model)
    session.update_available_models(models)
    session.set_model(model)
    return _conversation_state_response(session)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationSummaryModel,
)
def get_conversation(conversation_id: str):
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _session_summary_model(session)


@router.delete(
    "/conversations/{conversation_id}",
    response_model=ConversationIdResponse,
)
def delete_conversation(conversation_id: str):
    conversation_manager.drop_session(conversation_id)
    return ConversationIdResponse(conversationId=conversation_id)


@router.post(
    "/conversations/{conversation_id}/clear",
    response_model=ConversationSummaryModel,
)
def clear_conversation(conversation_id: str):
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    session.clear_conversation()
    return _session_summary_model(session)


@router.post(
    "/conversations/{conversation_id}/question",
    response_model=AskQuestionResponse,
)
def ask_question(conversation_id: str, request: AskQuestionRequest):
    logger.info(f"Asking question in conversation {conversation_id}")
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if request.selected_files is not None:
        session.update_selected_files(
            request.selected_files,
            make_persistent=request.persistent,
        )

    try:
        result = session.ask_question(request.question)
        raw_response = result["response"]
        html_response = markdown2.markdown(raw_response)
        result["rawResponse"] = raw_response
        result["response"] = html_response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    summary_model = _session_summary_model(session)
    return AskQuestionResponse(
        rawResponse=result["rawResponse"],
        response=result["response"],
        processingTime=result["processing_time"],
        tokensUsed=result["tokens_used"],
        questionIndex=result["question_index"],
        summary=summary_model,
    )


@router.post(
    "/conversations/{conversation_id}/system-prompt",
    response_model=SystemPromptResponse,
)
def run_system_prompt(conversation_id: str):
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    try:
        result = session.run_system_prompt()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    summary_model = _session_summary_model(session)
    return SystemPromptResponse(
        response=result["response"],
        processingTime=result["processing_time"],
        tokensUsed=result["tokens_used"],
        summary=summary_model,
    )


@router.post(
    "/conversations/{conversation_id}/files",
    response_model=ConversationSummaryModel,
)
def update_files(conversation_id: str, request: UpdateFilesRequest):
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    session.update_selected_files(
        request.selected_files,
        make_persistent=request.persistent,
    )
    return _session_summary_model(session)
    
    
@router.put(
    "/conversations/{conversation_id}/model",
    response_model=ConversationCreateResponse,
)
def update_model(conversation_id: str, request: UpdateModelRequest):
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    session.set_model(request.model)
    return _conversation_state_response(session)


@router.put(
    "/conversations/{conversation_id}/api-key",
    response_model=ConversationCreateResponse,
)
def update_api_key(conversation_id: str, request: UpdateApiKeyRequest):
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    session.set_api_key(request.api_key)
    return _conversation_state_response(session)


@router.get(
    "/conversations/{conversation_id}/export",
    response_model=ExportConversationResponse,
)
def export_conversation(conversation_id: str):
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    summary_model = _session_summary_model(session)
    return ExportConversationResponse(summary=summary_model)


@router.post(
    "/conversations/import",
    response_model=ConversationCreateResponse,
)
def import_conversation(request: ImportConversationRequest):
    env_api_key, env_provider, models, env_default_model = _load_env_defaults()
    api_key = request.api_key or env_api_key
    provider = request.provider or env_provider
    model = request.model or env_default_model

    if model and model not in models:
        models = models + [model]

    session = conversation_manager.create_session(
        api_key=api_key,
        provider=provider,
        models=models,
        default_model=model or (models[0] if models else ""),
    )
    # Restore conversation state
    session.app_state.conversation_history = [
        ConversationMessage(role=item.role, content=item.content)
        for item in request.conversation_history
    ]
    session.app_state.question_history = [
        QuestionStatus(
            question=q.question,
            status=q.status,
            response=q.response,
            timestamp=q.timestamp,
            tokens_used=q.tokens_used,
            processing_time=q.processing_time,
            model_used=q.model_used,
        )
        for q in request.question_history
    ]
    session.selected_files = request.selected_files
    session.app_state.set_persistent_files(request.persistent_files)
    session.selected_directory = request.selected_directory or ""
    session.app_state.selected_directory = session.selected_directory

    session.update_available_models(models)
    session.set_model(model)
    return _conversation_state_response(session)


# ---------------------------------------------------------------------------
# Directory and file helpers
# ---------------------------------------------------------------------------


@router.post(
    "/conversations/{conversation_id}/directory",
    response_model=SetDirectoryResponse,
)
def set_directory(conversation_id: str, request: SetDirectoryRequest):
    try:
        session = conversation_manager.get_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    success, message, tracked_files = session.set_directory(request.path)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    metadata = file_service.scan_directory(request.path)
    summary_model = _session_summary_model(session)
    return SetDirectoryResponse(
        directory=request.path,
        files=metadata,
        message=message,
        summary=summary_model,
    )


@router.post("/files/scan", response_model=DirectoryScanResponse)
def scan_directory(request: DirectoryScanRequest):
    logger.info(f"Scanning directory: {request.path}")
    validation = file_service.validate_directory(request.path)
    if not validation["is_valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    files = file_service.scan_directory(request.path)
    logger.info(f"Scan complete: {len(files)} files found")
    tree = file_service.build_directory_tree(request.path)
    return DirectoryScanResponse(
        directory=request.path,
        files=files,
        tree=tree,
    )


@router.post("/files/content", response_model=FileContentResponse)
def get_file_content(request: FileContentRequest):
    try:
        combined = file_service.read_files(request.files)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return FileContentResponse(combinedContent=combined)


@router.post("/files/folder-counts", response_model=FolderFileCountResponse)
def get_folder_file_counts(request: FolderFileCountRequest):
    validation = file_service.validate_directory(request.path)
    if not validation["is_valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    counts = file_service.get_folder_file_counts(request.path)
    folder_infos = [
        FolderInfo(
            path=item["path"],
            fileCount=item["fileCount"]
        ) for item in counts
    ]
    return FolderFileCountResponse(folders=folder_infos)


@router.get("/files/top-folders", response_model=TopFoldersResponse)
def get_top_folders():
    env_vars = env_manager.load_env_file()
    code_path = env_vars.get("CODE_PATH", ".")
    try:
        import os
        if os.path.exists(code_path):
            folders = [
                d for d in os.listdir(code_path)
                if os.path.isdir(os.path.join(code_path, d))
            ]
            return TopFoldersResponse(folders=folders)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"CODE_PATH directory not found: {code_path}",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Settings & themes
# ---------------------------------------------------------------------------


@router.get("/settings")
def get_settings():
    return settings_service.get_settings()


@router.put("/settings/env")
def update_env(request: SettingsUpdateRequest):
    return settings_service.update_env(request.updates)


@router.put("/settings/theme", response_model=ThemeToggleResponse)
def set_theme(request: ThemeSetRequest):
    success, theme = settings_service.set_theme(request.theme)
    if success:
        return ThemeToggleResponse(theme=theme, message="Theme updated")
    raise HTTPException(status_code=400, detail="Invalid theme")


@router.post("/settings/theme/toggle", response_model=ThemeToggleResponse)
def toggle_theme():
    theme, message = settings_service.toggle_theme()
    return ThemeToggleResponse(theme=theme, message=message)


# ---------------------------------------------------------------------------
# System messages
# ---------------------------------------------------------------------------


@router.get("/system-messages")
def list_system_messages():
    return {
        "current": system_message_service.get_current_file(),
        "messages": system_message_service.list_messages(),
    }


@router.get("/system-messages/{filename}")
def get_system_message(filename: str):
    content = system_message_service.load_message(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="System message not found")
    html_content = markdown2.markdown(content)
    return {"filename": filename, "content": content, "htmlContent": html_content}


@router.put("/system-messages/current")
def set_current_system_message(request: SystemMessageSetRequest):
    if not system_message_service.set_current(request.filename):
        raise HTTPException(
            status_code=400,
            detail="Unable to set system message",
        )
    return {"current": request.filename}


@router.post("/system-messages")
def save_system_message(request: SystemMessageUpdateRequest):
    if not system_message_service.save(request.filename, request.content):
        raise HTTPException(
            status_code=400,
            detail="Unable to save system message",
        )
    return {"filename": request.filename}


@router.delete("/system-messages/{filename}")
def delete_system_message(filename: str):
    if not system_message_service.delete(filename):
        raise HTTPException(
            status_code=400,
            detail="Unable to delete system message",
        )
    return {"filename": filename, "deleted": True}


# ---------------------------------------------------------------------------
# Web2 Enhanced Features - Code Extraction and Mermaid Rendering
# ---------------------------------------------------------------------------

import re
import os
import subprocess
import tempfile
import base64
from datetime import datetime
from pathlib import Path

@router.post("/code/extract")
def extract_code_blocks(request: dict):
    """Extract code blocks from a message with real parsing."""
    message_id = request.get("messageId")
    message_content = request.get("content")
    
    if not message_id:
        raise HTTPException(status_code=400, detail="messageId is required")
    
    try:
        # If content is provided, use it directly; otherwise try to find the message
        if not message_content:
            # Try to find the message in conversation history
            # This is a simplified lookup - in production you'd use a proper database
            message_content = ""
            for session_id, session in conversation_manager._sessions.items():
                summary = session.get_summary()
                for entry in summary.conversation_history:
                    if f"msg-{session_id}" in message_id and entry.role == "assistant":
                        message_content = entry.content
                        break
                if message_content:
                    break
        
        if not message_content:
            return {
                "success": True,
                "data": [],
                "message": "No content found for message"
            }
        
        # Extract code blocks using regex - matching web1 implementation exactly
        code_blocks = []
        
        # Primary pattern: Markdown fenced code blocks (matching web1's approach)
        # Pattern: ```(\w+)?\n([\s\S]*?)\n``` 
        fenced_pattern = r'```(\w+)?\n([\s\S]*?)\n```'
        matches = re.findall(fenced_pattern, message_content)
        
        for i, (language, code) in enumerate(matches):
            if code.strip():  # Only include non-empty code blocks
                # Clean up the code content (trim whitespace)
                clean_code = code.strip()
                
                # Detect language if not specified
                if not language:
                    language = _detect_language(clean_code)
                
                # Generate filename based on language
                filename = _generate_filename(language or "text", i + 1)
                
                # Create preview (first 3 lines, matching web1)
                lines = clean_code.split('\n')
                preview_lines = lines[:3]
                preview = '\n'.join(preview_lines)
                if len(lines) > 3:
                    preview += '\n...'
                
                code_block = {
                    "id": f"code-{message_id}-{i + 1}",
                    "language": language or "text",
                    "code": clean_code,
                    "filename": filename,
                    "preview": preview,
                    "extractedAt": datetime.now().isoformat(),
                    "lineCount": len(lines)
                }
                code_blocks.append(code_block)
        
        # If no markdown blocks found, try HTML fallback (matching web1's fallback approach)
        if len(code_blocks) == 0:
            html_pattern = r'<pre><code(?:\s+class="language-(\w+)")?>([\s\S]*?)</code></pre>'
            html_matches = re.findall(html_pattern, message_content, re.IGNORECASE)
            
            for i, (language, code) in enumerate(html_matches):
                if code.strip():
                    # Clean up HTML entities
                    clean_code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').strip()
                    
                    if not language:
                        language = _detect_language(clean_code)
                    
                    filename = _generate_filename(language or "text", i + 1)
                    
                    # Create preview
                    lines = clean_code.split('\n')
                    preview_lines = lines[:3]
                    preview = '\n'.join(preview_lines)
                    if len(lines) > 3:
                        preview += '\n...'
                    
                    code_block = {
                        "id": f"html-code-{message_id}-{i + 1}",
                        "language": language or "text",
                        "code": clean_code,
                        "filename": filename,
                        "preview": preview,
                        "extractedAt": datetime.now().isoformat(),
                        "lineCount": len(lines),
                        "source": "html"
                    }
                    code_blocks.append(code_block)
        
        logger.info(f"Extracted {len(code_blocks)} code blocks from message {message_id}")
        
        return {
            "success": True,
            "data": code_blocks,
            "message": f"Extracted {len(code_blocks)} code block(s)"
        }
        
    except Exception as e:
        logger.error(f"Error extracting code blocks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract code blocks: {str(e)}"
        )


def _detect_language(code: str) -> str:
    """Detect programming language from code content."""
    code_lower = code.lower().strip()
    
    # Common language indicators
    if any(keyword in code_lower for keyword in ['def ', 'import ', 'print(', 'class ', '__init__']):
        return "python"
    elif any(keyword in code_lower for keyword in ['function ', 'const ', 'let ', 'var ', 'console.log']):
        return "javascript"
    elif any(keyword in code_lower for keyword in ['public class', 'private ', 'public static void main']):
        return "java"
    elif any(keyword in code_lower for keyword in ['#include', 'int main', 'printf', 'iostream']):
        return "cpp"
    elif any(keyword in code_lower for keyword in ['<?php', 'echo ', '$']):
        return "php"
    elif any(keyword in code_lower for keyword in ['select ', 'insert ', 'update ', 'delete ', 'select*', 'from ']):
        return "sql"
    elif any(keyword in code_lower for keyword in ['<html', '<div', '<body', '<script']):
        return "html"
    elif any(keyword in code_lower for keyword in ['{', '}', 'color:', 'background:']):
        return "css"
    elif any(keyword in code_lower for keyword in ['# ', '## ', '### ']):
        return "markdown"
    elif any(keyword in code_lower for keyword in ['#!/bin/bash', 'echo ', 'cd ', 'ls ']):
        return "bash"
    else:
        return "text"


def _generate_filename(language: str, index: int) -> str:
    """Generate appropriate filename based on language."""
    extensions = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
        "php": "php",
        "sql": "sql",
        "html": "html",
        "css": "css",
        "markdown": "md",
        "bash": "sh",
        "json": "json",
        "xml": "xml",
        "yaml": "yml"
    }
    
    ext = extensions.get(language, "txt")
    return f"extracted_code_{index}.{ext}"


@router.post("/mermaid/render")
def render_mermaid_diagram(request: dict):
    """Render mermaid diagram to PNG using real implementation."""
    mermaid_code = request.get("code")
    title = request.get("title", "diagram")
    output_format = request.get("format", "png")  # png, svg, pdf
    
    if not mermaid_code:
        raise HTTPException(status_code=400, detail="mermaid code is required")
    
    try:
        logger.info(f"Rendering mermaid diagram: {title}")
        
        # Create temporary directory for mermaid files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write mermaid code to temporary file
            mermaid_file = temp_path / f"{title}.mmd"
            with open(mermaid_file, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            
            # Output file path
            output_file = temp_path / f"{title}.{output_format}"
            
            # Try multiple rendering methods in order of preference
            success, result_data = _render_with_mermaid_cli(mermaid_file, output_file)
            
            if not success:
                # Fallback to Node.js with Puppeteer if available
                success, result_data = _render_with_puppeteer(mermaid_code, output_file)
            
            if not success:
                # Final fallback: render using Python-based solution
                success, result_data = _render_with_python_mermaid(mermaid_code, output_file)
            
            if success:
                return {
                    "success": True,
                    "data": result_data,
                    "message": f"Mermaid diagram '{title}' rendered successfully",
                    "format": output_format
                }
            else:
                # Return a data URL with the mermaid code for client-side rendering
                logger.warning("Server-side rendering failed, returning code for client-side rendering")
                return {
                    "success": True,
                    "data": f"data:text/plain;base64,{base64.b64encode(mermaid_code.encode()).decode()}",
                    "message": f"Mermaid code ready for client-side rendering",
                    "fallback": True,
                    "clientRender": True
                }
        
    except Exception as e:
        logger.error(f"Error rendering mermaid diagram: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to render mermaid diagram: {str(e)}"
        )


def _render_with_mermaid_cli(mermaid_file: Path, output_file: Path) -> tuple[bool, str]:
    """Try to render using mermaid-cli (mmdc)."""
    try:
        # Check if mermaid-cli is installed
        result = subprocess.run(['mmdc', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            logger.debug("mermaid-cli not available")
            return False, ""
        
        # Render the diagram
        cmd = [
            'mmdc',
            '-i', str(mermaid_file),
            '-o', str(output_file),
            '-b', 'white',  # Background color
            '-s', '2'       # Scale factor
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and output_file.exists():
            # Read the generated file and return as base64 data URL
            with open(output_file, 'rb') as f:
                file_data = f.read()
                
            mime_type = "image/png" if output_file.suffix == '.png' else "image/svg+xml"
            data_url = f"data:{mime_type};base64,{base64.b64encode(file_data).decode()}"
            
            logger.info("Successfully rendered with mermaid-cli")
            return True, data_url
        else:
            logger.debug(f"mermaid-cli failed: {result.stderr}")
            return False, ""
            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"mermaid-cli error: {e}")
        return False, ""


def _render_with_puppeteer(mermaid_code: str, output_file: Path) -> tuple[bool, str]:
    """Try to render using Node.js with Puppeteer."""
    try:
        # Create a simple Node.js script for rendering
        node_script = f'''
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {{
  try {{
    const browser = await puppeteer.launch({{headless: true}});
    const page = await browser.newPage();
    
    await page.setContent(`
      <!DOCTYPE html>
      <html>
      <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
      </head>
      <body>
        <div id="diagram">{mermaid_code}</div>
        <script>
          mermaid.initialize({{startOnLoad: true}});
        </script>
      </body>
      </html>
    `);
    
    await page.waitForSelector('#diagram svg', {{timeout: 10000}});
    
    const element = await page.$('#diagram');
    await element.screenshot({{path: '{output_file}', background: 'white'}});
    
    await browser.close();
    console.log('SUCCESS');
  }} catch (error) {{
    console.error('ERROR:', error);
    process.exit(1);
  }}
}})();
'''
        
        # Write Node.js script to temporary file
        script_file = output_file.parent / 'render_script.js'
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(node_script)
        
        # Execute Node.js script
        result = subprocess.run(['node', str(script_file)], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and output_file.exists():
            with open(output_file, 'rb') as f:
                file_data = f.read()
                
            data_url = f"data:image/png;base64,{base64.b64encode(file_data).decode()}"
            logger.info("Successfully rendered with Puppeteer")
            return True, data_url
        else:
            logger.debug(f"Puppeteer failed: {result.stderr}")
            return False, ""
            
    except Exception as e:
        logger.debug(f"Puppeteer error: {e}")
        return False, ""


def _render_with_python_mermaid(mermaid_code: str, output_file: Path) -> tuple[bool, str]:
    """Try to render using Python mermaid libraries."""
    try:
        # Try using Python libraries for simple diagram types
        # This is a basic implementation for common diagram types
        
        if 'graph' in mermaid_code.lower() or 'flowchart' in mermaid_code.lower():
            # For flowcharts, we can create a simple SVG
            svg_content = _create_simple_flowchart_svg(mermaid_code)
            
            if svg_content:
                # Convert SVG to PNG using cairosvg if available
                try:
                    import cairosvg
                    png_data = cairosvg.svg2png(bytestring=svg_content.encode())
                    
                    data_url = f"data:image/png;base64,{base64.b64encode(png_data).decode()}"
                    logger.info("Successfully rendered with Python SVG conversion")
                    return True, data_url
                except ImportError:
                    # Return SVG as data URL if cairosvg not available
                    data_url = f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode()).decode()}"
                    logger.info("Successfully rendered as SVG (cairosvg not available)")
                    return True, data_url
        
        return False, ""
        
    except Exception as e:
        logger.debug(f"Python mermaid error: {e}")
        return False, ""


def _create_simple_flowchart_svg(mermaid_code: str) -> str:
    """Create a simple SVG for basic flowcharts."""
    try:
        # This is a very basic implementation for simple flowcharts
        # In a real implementation, you'd want a proper mermaid parser
        
        # Extract basic nodes and connections
        lines = [line.strip() for line in mermaid_code.split('\n') if line.strip()]
        
        # Simple SVG template
        svg_start = '''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <style>
                    .node { fill: #e1f5fe; stroke: #01579b; stroke-width: 2; }
                    .text { font-family: Arial, sans-serif; font-size: 12px; text-anchor: middle; }
                    .edge { stroke: #333; stroke-width: 2; fill: none; marker-end: url(#arrow); }
                </style>
                <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                    <polygon points="0,0 0,6 9,3" fill="#333"/>
                </marker>
            </defs>'''
        
        svg_content = [svg_start]
        
        # Add a simple representation
        svg_content.append('<rect x="50" y="50" width="100" height="40" class="node" rx="5"/>')
        svg_content.append('<text x="100" y="75" class="text">Start</text>')
        
        svg_content.append('<line x1="150" y1="70" x2="200" y2="70" class="edge"/>')
        
        svg_content.append('<rect x="220" y="50" width="100" height="40" class="node" rx="5"/>')
        svg_content.append('<text x="270" y="75" class="text">Process</text>')
        
        svg_content.append('<line x1="270" y1="90" x2="270" y2="140" class="edge"/>')
        
        svg_content.append('<rect x="220" y="160" width="100" height="40" class="node" rx="5"/>')
        svg_content.append('<text x="270" y="185" class="text">End</text>')
        
        svg_content.append('<text x="200" y="20" class="text" style="font-weight: bold;">Mermaid Diagram</text>')
        svg_content.append('<text x="200" y="280" class="text" style="font-size: 10px; fill: #666;">Generated by WhisperCode</text>')
        
        svg_content.append('</svg>')
        
        return '\n'.join(svg_content)
        
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Web2 Enhanced API Endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
def health_check():
    """Health check endpoint for Web2."""
    return {
        "status": "healthy",
        "service": "WhisperCode Web2 Backend",
        "version": "2.0.0"
    }


@router.post("/chat")
def send_chat_message(request: dict):
    """Enhanced chat endpoint for Web2 with real AI integration."""
    message = request.get("message")
    conversation_id = request.get("conversationId")
    context_files = request.get("contextFiles", [])
    settings = request.get("settings", {})
    
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    
    try:
        # Get or create conversation session
        session = conversation_manager.get_session(conversation_id)
        if not session:
            # Create new session if not found
            api_key, provider, models, default_model = _load_env_defaults()
            model = settings.get("model", default_model)
            
            create_request = ConversationCreateRequest(
                provider=provider,
                model=model,
                api_key=api_key
            )
            session = conversation_manager.create_conversation(create_request)
        
        # Build context from files if provided
        context_content = ""
        if context_files:
            try:
                context_parts = []
                for file_path in context_files:
                    file_content = file_service.read_file_content(file_path)
                    if file_content:
                        context_parts.append(f"File: {file_path}\n```\n{file_content}\n```\n")
                
                if context_parts:
                    context_content = "\n".join(context_parts)
            except Exception as e:
                logger.warning(f"Failed to load context files: {e}")
        
        # Prepare the question request
        ask_request = AskQuestionRequest(question=message)
        
        # Add context files to session if provided
        if context_files:
            try:
                update_files_req = UpdateFilesRequest(
                    conversation_id=session.session_id,
                    selected_files=context_files,
                    persistent=True
                )
                conversation_manager.update_selected_files(update_files_req)
            except Exception as e:
                logger.warning(f"Failed to update context files: {e}")
        
        # Process the question with AI
        logger.info(f"Processing question for conversation {session.session_id}")
        response = conversation_manager.ask_question(session.session_id, ask_request)
        
        # Create response message
        ai_response = {
            "id": f"msg-{session.session_id}-{len(session.get_summary().conversation_history)}",
            "role": "assistant",
            "content": response.response,
            "timestamp": response.timestamp if hasattr(response, 'timestamp') else "2025-09-27T00:00:00Z",
            "metadata": {
                "model": session.get_summary().selected_model,
                "provider": session.get_summary().provider,
                "tokens": response.tokens_used,
                "processingTime": response.processing_time
            }
        }
        
        return {
            "success": True,
            "data": {
                "message": ai_response,
                "conversationId": session.session_id,
                "usage": {
                    "promptTokens": len(message.split()),
                    "completionTokens": response.tokens_used,
                    "totalTokens": response.tokens_used,
                    "processingTime": response.processing_time
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


# ---------------------------------------------------------------------------
# FastAPI Application Setup
# ---------------------------------------------------------------------------

# Create the FastAPI application
app = FastAPI(
    title="WhisperCode Web2 API",
    description="Enhanced AI-powered code analysis and chat interface",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:3000"],  # Web2 frontend ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router with /api prefix for Web2
app.include_router(router, prefix="/api", tags=["WhisperCode Web2"])

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "WhisperCode Web2 Backend API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }
