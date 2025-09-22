"""FastAPI router exposing the Code Chat capabilities for the web client."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException

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
