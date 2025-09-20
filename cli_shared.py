"""Shared helpers for CLI workflows."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv

from ai import AIProcessor, AIProviderFactory
from system_message_manager import system_message_manager


class ConfigurationError(Exception):
    """Raised when CLI configuration cannot be completed."""


def load_configuration(
    api_key_override: Optional[str] = None,
    provider_override: Optional[str] = None,
    model_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Load configuration from the environment and apply overrides."""
    load_dotenv()

    config = {
        "api_key": os.getenv("API_KEY", ""),
        "provider": os.getenv("PROVIDER", "openrouter"),
        "model": os.getenv("DEFAULT_MODEL", "openai/gpt-3.5-turbo"),
        "models": [m.strip() for m in os.getenv("MODELS", "").split(",") if m.strip()],
    }

    if api_key_override:
        config["api_key"] = api_key_override
    if provider_override:
        config["provider"] = provider_override
    if model_override:
        config["model"] = model_override

    return config


def create_ai_processor(provider_name: str, api_key: str) -> AIProcessor:
    """Create an AI processor for the selected provider and API key."""
    try:
        factory = AIProviderFactory()
        provider = factory.create_provider(provider_name, api_key)
        ai_processor = AIProcessor(provider)
    except Exception as exc:  # pragma: no cover - defensive
        raise ConfigurationError(f"Failed to initialize AI processor: {exc}") from exc

    if not ai_processor.validate_api_key():
        raise ConfigurationError(
            "No API key configured. Please set API_KEY in your environment or provide --api-key."
        )

    return ai_processor


def configure_system_prompt(system_prompt_name: Optional[str]) -> Tuple[bool, str]:
    """Configure the system prompt; returns success flag and status message."""
    if not system_prompt_name:
        return True, "Using default system prompt"

    filename = f"systemmessage_{system_prompt_name}.txt"
    if not os.path.exists(filename):
        return False, f"System prompt file '{filename}' not found."

    success = system_message_manager.set_current_system_message_file(filename)
    if success:
        return True, f"Using system prompt: {system_prompt_name}"

    return False, f"Failed to load system prompt file '{filename}'."
