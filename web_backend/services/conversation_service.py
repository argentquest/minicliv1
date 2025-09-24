"""Conversation management service for the web backend.

This module adapts the Tkinter conversation orchestration from minicli.py
for use in a REST environment.  It keeps the business logic (AI processing,
code aggregation, persistent file context, system prompt execution) while
removing UI dependencies so the same functionality can serve the web client.
"""
from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from common.ai import create_ai_processor
from common.lazy_file_scanner import LazyCodebaseScanner
from common.logger import get_logger
from common.models import AppState, ConversationMessage
from pattern_matcher import pattern_matcher
from common.system_message_manager import system_message_manager
from common.env_manager import env_manager
from common.logger import get_logger
import markdown2

logger = get_logger(__name__)


@dataclass
class ConversationSummary:
    """Serialisable snapshot of a conversation session."""

    conversation_id: str
    selected_model: str
    provider: str
    selected_directory: str
    selected_files: List[str]
    persistent_files: List[str]
    question_history: List[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]


@dataclass
class ConversationSession:
    """In-memory representation of a user conversation."""

    session_id: str
    ai_processor: Any
    provider: str
    available_models: List[str]
    default_model: str
    app_state: AppState = field(default_factory=AppState)
    codebase_scanner: LazyCodebaseScanner = field(default_factory=LazyCodebaseScanner)
    selected_directory: str = ""
    selected_files: List[str] = field(default_factory=list)
    logger = get_logger("conversation")

    def __post_init__(self) -> None:
        self.app_state.selected_model = self.default_model
        self.logger = get_logger(f"conversation.{self.session_id}")
        self.logger.set_context(component="conversation", operation="init")
        self.logger.info(
            "Created new conversation session",
            extra={
                "session_id": self.session_id,
                "provider": self.provider,
                "model": self.default_model,
            },
        )

    # ---------------------------------------------------------------------
    # Session setup helpers
    # ---------------------------------------------------------------------
    def set_api_key(self, api_key: str) -> None:
        self.app_state.api_key = api_key or ""
        self.ai_processor.set_api_key(self.app_state.api_key)

    def set_model(self, model: str) -> None:
        if not model:
            return
        if model not in self.available_models:
            self.available_models.append(model)
        self.app_state.selected_model = model
        self.logger.info(
            "Model updated",
            extra={"session_id": self.session_id, "model": model},
        )

    def set_provider(self, provider: str) -> None:
        if provider and provider != self.provider:
            self.provider = provider
            self.ai_processor.set_provider(provider)
            self.logger.info(
                "Provider updated",
                extra={"session_id": self.session_id, "provider": provider},
            )

    def update_available_models(self, models: List[str]) -> None:
        if not models:
            return
        self.available_models = models
        if self.app_state.selected_model not in models:
            self.app_state.selected_model = models[0]

    # ------------------------------------------------------------------
    # Directory and file handling
    # ------------------------------------------------------------------
    def set_directory(self, directory: str) -> Tuple[bool, str, List[str]]:
        """Validate and scan a directory, returning files on success."""
        is_valid, error_message = self.codebase_scanner.validate_directory(directory)
        if not is_valid:
            return False, error_message, []

        self.selected_directory = directory
        files = self.codebase_scanner.scan_directory(directory)
        self.app_state.selected_directory = directory
        self.app_state.codebase_files = files
        self.selected_files = []
        self.app_state.persistent_selected_files = []
        self.logger.info(
            "Directory scanned",
            extra={
                "session_id": self.session_id,
                "directory": directory,
                "file_count": len(files),
            },
        )
        return True, "Directory scanned successfully", files

    def update_selected_files(
        self, selected_files: Optional[List[str]] = None, make_persistent: bool = False
    ) -> None:
        selected_files = selected_files or []
        self.selected_files = selected_files
        if make_persistent:
            self.app_state.set_persistent_files(selected_files)
        self.logger.debug(
            "Updated file selection",
            extra={
                "session_id": self.session_id,
                "selected": len(selected_files),
                "persistent": len(self.app_state.get_persistent_files()),
            },
        )

    # ------------------------------------------------------------------
    # Conversation operations
    # ------------------------------------------------------------------
    def ask_question(self, question: str) -> Dict[str, any]:
        """Process a new question and return response metadata."""
        if not question.strip():
            raise ValueError("Question cannot be empty")
        if not self.ai_processor.validate_api_key():
            raise ValueError("API key is not configured")

        is_first_message = len(self.app_state.conversation_history) == 0
        if is_first_message and not self.selected_files:
            raise ValueError("At least one file must be selected for the first question")

        question_status = self.app_state.add_question(question)
        question_index = len(self.app_state.question_history) - 1

        self.logger.set_context(component="conversation", operation="ask_question")
        self.logger.info(
            "Processing question",
            extra={
                "session_id": self.session_id,
                "question_preview": question[:80],
                "first_message": is_first_message,
            },
        )

        start_time = time.time()
        needs_codebase_context = is_first_message or self._is_tool_command(question)

        # Track user message in history
        self.app_state.conversation_history.append(
            ConversationMessage(role="user", content=question)
        )

        codebase_content = self._get_codebase_content(is_first_message, needs_codebase_context)

        response_text = self._process_with_ai(question, codebase_content)
        processing_time = time.time() - start_time
        tokens_used = self._get_last_token_usage()

        self._update_conversation_history(response_text, is_first_message, codebase_content)
        self.app_state.update_question_status(
            question_index,
            "completed",
            response=response_text,
            tokens_used=tokens_used,
            processing_time=processing_time,
            model_used=self.app_state.selected_model,
        )

        html_response = markdown2.markdown(response_text, extras=['fenced-code-blocks', 'tables', 'codehilite'])
        return {
            "response": html_response,
            "rawMarkdown": response_text,
            "processing_time": processing_time,
            "tokens_used": tokens_used,
            "question_index": question_index,
        }

    def run_system_prompt(self) -> Dict[str, any]:
        """Execute the active system prompt and return response metadata."""
        if not self.ai_processor.validate_api_key():
            raise ValueError("API key is not configured")

        is_first_message = len(self.app_state.conversation_history) == 0
        if is_first_message and not self.selected_files:
            raise ValueError("At least one file must be selected before running the system prompt")

        codebase_content = self._get_codebase_content(is_first_message=True, needs_codebase_context=True)
        system_message = system_message_manager.get_system_message(codebase_content)

        start_time = time.time()
        response_text = self.ai_processor.process_question(
            question=system_message,
            conversation_history=[],
            codebase_content="",
            model=self.app_state.selected_model,
        )
        processing_time = time.time() - start_time
        tokens_used = self._get_last_token_usage()

        self._update_system_prompt_history(response_text)

        html_response = markdown2.markdown(response_text, extras=['fenced-code-blocks', 'tables', 'codehilite'])
        return {
            "response": html_response,
            "rawMarkdown": response_text,
            "processing_time": processing_time,
            "tokens_used": tokens_used,
        }

    def clear_conversation(self) -> None:
        self.app_state.clear_conversation()
        self.logger.info("Conversation cleared", extra={"session_id": self.session_id})

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def get_summary(self) -> ConversationSummary:
        history = [message.to_dict() for message in self.app_state.conversation_history]
        question_history = [
            {
                "question": q.question,
                "status": q.status,
                "response": q.response,
                "timestamp": q.timestamp,
                "tokens_used": q.tokens_used,
                "processing_time": q.processing_time,
                "model_used": q.model_used,
            }
            for q in self.app_state.question_history
        ]
        return ConversationSummary(
            conversation_id=self.session_id,
            selected_model=self.app_state.selected_model,
            provider=self.provider,
            selected_directory=self.selected_directory,
            selected_files=self.selected_files,
            persistent_files=self.app_state.get_persistent_files(),
            conversation_history=history,
            question_history=question_history,
        )

    # ------------------------------------------------------------------
    # Internal helpers mirroring Tkinter implementation
    # ------------------------------------------------------------------
    def _is_tool_command(self, question: str) -> bool:
        try:
            env_vars = env_manager.load_env_file()
            tool_vars = {key: value for key, value in env_vars.items() if key.startswith("TOOL")}
            return pattern_matcher.is_tool_command(question, tool_vars, threshold=0.5)
        except Exception:
            return False

    def _get_codebase_content(self, is_first_message: bool, needs_codebase_context: bool) -> str:
        if not needs_codebase_context:
            return ""

        if is_first_message:
            if self.selected_files:
                self.app_state.set_persistent_files(self.selected_files)
                return self._load_files(self.selected_files)
            return ""

        persistent_files = self.app_state.get_persistent_files()
        if persistent_files:
            return self._load_files(persistent_files)

        if self.selected_files:
            return self._load_files(self.selected_files)

        return ""

    def _load_files(self, files: List[str]) -> str:
        if len(files) > 50:
            return self.codebase_scanner.get_codebase_content_lazy(files)
        return self.codebase_scanner.get_codebase_content(files)

    def _process_with_ai(self, question: str, codebase_content: str) -> str:
        conversation_for_api = []
        for message in self.app_state.conversation_history[:-1]:
            if message.role != "system":
                conversation_for_api.append(message.to_dict())

        return self.ai_processor.process_question(
            question=question,
            conversation_history=conversation_for_api,
            codebase_content=codebase_content,
            model=self.app_state.selected_model,
        )

    def _update_conversation_history(
        self, response_text: str, is_first_message: bool, codebase_content: str
    ) -> None:
        self.app_state.conversation_history.append(
            ConversationMessage(role="assistant", content=response_text)
        )
        if is_first_message:
            system_msg = system_message_manager.get_system_message(codebase_content)
            self.app_state.conversation_history.insert(
                0, ConversationMessage(role="system", content=system_msg)
            )

    def _update_system_prompt_history(self, response_text: str) -> None:
        self.app_state.conversation_history.append(
            ConversationMessage(role="user", content="[System Prompt Executed]")
        )
        self.app_state.conversation_history.append(
            ConversationMessage(role="assistant", content=response_text)
        )

    def _get_last_token_usage(self) -> int:
        try:
            provider = getattr(self.ai_processor, "_provider", None)
            if provider and hasattr(provider, "_last_token_usage"):
                return int(provider._last_token_usage)
        except Exception:
            pass
        return 0


class ConversationManager:
    """Registry for active conversation sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, ConversationSession] = {}
        self._logger = get_logger("conversation_manager")

    def create_session(
        self,
        api_key: str,
        provider: str,
        models: List[str],
        default_model: Optional[str] = None,
    ) -> ConversationSession:
        logger.info(f"Creating conversation session for provider {provider}")
        session_id = str(uuid.uuid4())
        ai_processor = create_ai_processor(api_key=api_key, provider=provider)
        default_model = default_model or (models[0] if models else "")
        session = ConversationSession(
            session_id=session_id,
            ai_processor=ai_processor,
            provider=provider,
            available_models=models,
            default_model=default_model,
        )
        session.set_api_key(api_key)
        self._sessions[session_id] = session
        logger.info(f"Session created: {session_id}")
        return session

    def get_session(self, session_id: str) -> ConversationSession:
        if session_id not in self._sessions:
            raise KeyError(f"Conversation {session_id} not found")
        return self._sessions[session_id]

    def drop_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._logger.info("Conversation session removed", extra={"session_id": session_id})
            del self._sessions[session_id]


conversation_manager = ConversationManager()
