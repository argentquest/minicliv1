"""Environment and theme helpers for the web backend."""
from __future__ import annotations

from typing import Dict, Tuple

from common.env_manager import env_manager
from common.logger import get_logger
from security_utils import SecurityUtils
from web_backend.services.theme_service import theme_manager

logger = get_logger(__name__)


class SettingsService:
    """Expose environment configuration and theme controls via REST."""

    def get_settings(self) -> Dict[str, object]:
        env_vars = env_manager.load_env_file()
        masked = {
            key: SecurityUtils.mask_api_key(value) if "KEY" in key else value
            for key, value in env_vars.items()
        }
        return {
            "values": env_vars,
            "masked": masked,
            "descriptions": env_manager.get_env_descriptions(),
            "theme": theme_manager.current_theme_name,
            "availableThemes": theme_manager.get_available_themes(),
        }

    def update_env(self, changes: Dict[str, str]) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for key, value in changes.items():
            results[key] = env_manager.update_single_var(key, value)
        return results

    def set_theme(self, theme_name: str) -> Tuple[bool, str]:
        success = theme_manager.switch_theme(theme_name)
        if success:
            env_manager.update_single_var("UI_THEME", theme_name)
            return True, theme_name
        return False, theme_manager.current_theme_name

    def toggle_theme(self) -> Tuple[str, str]:
        theme_manager.toggle_theme()
        new_theme = theme_manager.current_theme_name
        env_manager.update_single_var("UI_THEME", new_theme)
        return new_theme, "Theme updated"


settings_service = SettingsService()
