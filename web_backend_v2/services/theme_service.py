"""Theme management service for the web backend."""
from __future__ import annotations

import os
from typing import List

from common.logger import get_logger

logger = get_logger(__name__)


class ThemeManager:
    """
    Simple theme manager for web backend that handles light/dark themes.

    This is a simplified version of the tkinter theme manager, adapted for
    web use without GUI dependencies.
    """

    def __init__(self):
        """
        Initialize the theme manager with available themes.

        Loads the user's saved theme preference from UI_THEME environment variable.
        """
        # Available themes
        self.themes = ['light', 'dark']

        # Default to light theme initially
        self.current_theme_name = 'light'

        # Load user's saved theme preference
        self._load_theme_preference()

    def _load_theme_preference(self):
        """
        Load user's theme preference from UI_THEME environment variable.
        Falls back to 'light' if invalid or not set.
        """
        theme_pref = os.getenv('UI_THEME', 'light')

        if theme_pref in self.themes:
            self.current_theme_name = theme_pref

    def switch_theme(self, theme_name: str) -> bool:
        """
        Switch to a specific theme by name.

        Args:
            theme_name (str): Name of the theme to switch to ('light' or 'dark')

        Returns:
            bool: True if theme was successfully switched, False if invalid
        """
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            return True
        return False

    def get_current_theme(self) -> str:
        """
        Get the currently active theme name.

        Returns:
            str: The active theme name ('light' or 'dark')
        """
        return self.current_theme_name

    def get_available_themes(self) -> List[str]:
        """
        Get list of all available theme names.

        Returns:
            List[str]: List of theme names ['light', 'dark']
        """
        return self.themes.copy()

    def toggle_theme(self) -> bool:
        """
        Toggle between light and dark themes.

        Returns:
            bool: True if toggle was successful
        """
        new_theme = 'dark' if self.current_theme_name == 'light' else 'light'
        return self.switch_theme(new_theme)


# Global theme manager instance
theme_manager = ThemeManager()