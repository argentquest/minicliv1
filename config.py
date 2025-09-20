"""Centralized configuration access for Code Chat AI."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv


class Config:
    """Load and expose environment-driven configuration as typed properties."""

    def __init__(self, env_path: Optional[str] = None, *, override: bool = False) -> None:
        self._env_path = Path(env_path or ".env")
        if self._env_path.exists():
            load_dotenv(self._env_path, override=override)

    @staticmethod
    def _get(key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)

    @classmethod
    def _split(cls, key: str, default: Optional[List[str]] = None) -> List[str]:
        raw = cls._get(key)
        if not raw:
            return default or []
        return [part.strip() for part in raw.split(',') if part.strip()]

    @staticmethod
    def _get_int(key: str, default: Optional[int] = None) -> Optional[int]:
        value = Config._get(key)
        if value is None or value == "":
            return default
        try:
            return int(value)
        except ValueError:
            return default

    @staticmethod
    def _get_float(key: str, default: Optional[float] = None) -> Optional[float]:
        value = Config._get(key)
        if value is None or value == "":
            return default
        try:
            return float(value)
        except ValueError:
            return default

    @staticmethod
    def _get_bool(key: str, default: Optional[bool] = None) -> Optional[bool]:
        value = Config._get(key)
        if value is None or value == "":
            return default
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
        return default

    def reload(self, *, override: bool = False) -> None:
        """Reload .env values into the current environment."""
        if self._env_path.exists():
            load_dotenv(self._env_path, override=override)

    # API configuration -------------------------------------------------
    @property
    def api_key(self) -> Optional[str]:
        return self._get("API_KEY")

    @property
    def openrouter_api_key(self) -> Optional[str]:
        return self._get("OPENROUTER_API_KEY")

    @property
    def provider(self) -> Optional[str]:
        return self._get("PROVIDER")

    @property
    def providers(self) -> List[str]:
        return self._split("PROVIDERS")

    @property
    def api_url(self) -> Optional[str]:
        return self._get("API_URL")

    @property
    def token_url(self) -> Optional[str]:
        return self._get("TOKEN_URL")

    @property
    def token_use_id(self) -> Optional[str]:
        return self._get("TOKEN_USE_ID")

    @property
    def token_password(self) -> Optional[str]:
        return self._get("TOKEN_PASSWORD")

    # Model configuration ----------------------------------------------
    @property
    def default_model(self) -> Optional[str]:
        return self._get("DEFAULT_MODEL")

    @property
    def models(self) -> List[str]:
        models = self._split("MODELS")
        if not models:
            default = self.default_model
            return [default] if default else []
        return models

    # AI parameters -----------------------------------------------------
    @property
    def max_tokens(self) -> Optional[int]:
        return self._get_int("MAX_TOKENS")

    @property
    def temperature(self) -> Optional[float]:
        return self._get_float("TEMPERATURE")

    @property
    def top_p(self) -> Optional[float]:
        return self._get_float("TOP_P")

    @property
    def frequency_penalty(self) -> Optional[float]:
        return self._get_float("FREQUENCY_PENALTY")

    # UI configuration --------------------------------------------------
    @property
    def ui_theme(self) -> Optional[str]:
        return self._get("UI_THEME")

    @property
    def window_size(self) -> Optional[Tuple[int, int]]:
        raw = self._get("WINDOW_SIZE")
        if not raw:
            return None
        try:
            width_str, height_str = raw.lower().split('x', 1)
            return int(width_str), int(height_str)
        except (ValueError, AttributeError):
            return None

    # File system configuration ----------------------------------------
    @property
    def ignore_folders(self) -> List[str]:
        return self._split("IGNORE_FOLDERS", [
            "venv", ".venv", "env", ".env", "__pycache__", "node_modules", "dist", "build", ".git"
        ])

    @property
    def supported_extensions(self) -> List[str]:
        return self._split("SUPPORTED_EXTENSIONS")

    @property
    def max_file_size(self) -> Optional[int]:
        return self._get_int("MAX_FILE_SIZE")

    # System message configuration -------------------------------------
    @property
    def current_system_prompt(self) -> Optional[str]:
        return self._get("CURRENT_SYSTEM_PROMPT")

    # Logging configuration --------------------------------------------
    @property
    def log_level(self) -> Optional[str]:
        return self._get("LOG_LEVEL")

    @property
    def log_dir(self) -> Path:
        return Path(self._get("LOG_DIR", "logs"))

    # Advanced configuration -------------------------------------------
    @property
    def cache_size(self) -> Optional[int]:
        return self._get_int("CACHE_SIZE")

    @property
    def request_timeout(self) -> Optional[int]:
        return self._get_int("REQUEST_TIMEOUT")

    # FastAPI server configuration -------------------------------------
    @property
    def api_port(self) -> Optional[int]:
        return self._get_int("API_PORT")

    @property
    def api_host(self) -> Optional[str]:
        return self._get("API_HOST")

    # Web application configuration ------------------------------------
    @property
    def fastapi_url(self) -> Optional[str]:
        return self._get("FASTAPI_URL")

    @property
    def web_port(self) -> Optional[int]:
        return self._get_int("WEB_PORT")

    # Interactive CLI memory -------------------------------------------
    @property
    def last_used_folder(self) -> Optional[str]:
        return self._get("LAST_USED_FOLDER")

    @property
    def last_used_question(self) -> Optional[str]:
        return self._get("LAST_USED_QUESTION")

    @property
    def last_exclude_patterns(self) -> Optional[str]:
        return self._get("LAST_EXCLUDE_PATTERNS")

    @property
    def last_output_format(self) -> Optional[str]:
        return self._get("LAST_OUTPUT_FORMAT")

    @property
    def last_save_location(self) -> Optional[str]:
        return self._get("LAST_SAVE_LOCATION")

    @property
    def last_use_lazy(self) -> Optional[bool]:
        return self._get_bool("LAST_USE_LAZY", default=True)

    @property
    def last_show_tree(self) -> Optional[bool]:
        return self._get_bool("LAST_SHOW_TREE", default=True)

    # Output directory -------------------------------------------------
    @property
    def dir_save(self) -> Path:
        return Path(self._get("DIR_SAVE", "results"))

    def as_dict(self) -> dict:
        """Expose a dictionary of key configuration values."""
        return {
            "api_key": self.api_key,
            "provider": self.provider,
            "providers": self.providers,
            "default_model": self.default_model,
            "models": self.models,
            "log_dir": str(self.log_dir),
            "dir_save": str(self.dir_save),
        }


# Shared singleton-style configuration instance
config = Config()