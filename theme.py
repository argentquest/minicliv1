"""
Modern theme system for the Code Chat application.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
import os

class Theme:
    """Base theme class."""
    
    def __init__(self):
        self.colors = {}
        self.fonts = {}
        self.styles = {}
        self._setup_theme()
    
    def _setup_theme(self):
        """Override in subclasses."""
        pass
    
    def apply_to_root(self, root: tk.Tk):
        """Apply theme to root window."""
        root.configure(bg=self.colors.get('bg_primary', '#ffffff'))
    
    def get_style(self, component: str) -> Dict[str, Any]:
        """Get style configuration for a component."""
        return self.styles.get(component, {})

class ModernLightTheme(Theme):
    """Modern light theme with clean, professional styling."""
    
    def _setup_theme(self):
        # Color palette - Modern blue/gray
        self.colors = {
            'bg_primary': '#f8f9fa',      # Main background
            'bg_secondary': '#ffffff',     # Cards, panels
            'bg_tertiary': '#e9ecef',     # Input fields
            'bg_accent': '#f0f7ff',       # Highlights
            'border': '#dee2e6',          # Borders
            'border_focus': '#0d6efd',    # Focused borders
            'text_primary': '#212529',    # Main text
            'text_secondary': '#6c757d',  # Secondary text
            'text_muted': '#adb5bd',      # Muted text
            'primary': '#0d6efd',         # Primary buttons
            'primary_hover': '#0b5ed7',   # Primary hover
            'success': '#198754',         # Success states
            'warning': '#ffc107',         # Warning states
            'danger': '#dc3545',          # Error states
            'selection': '#e7f3ff',       # Selected items
            'hover': '#f8f9fa',           # Hover states
        }
        
        # Typography
        self.fonts = {
            'heading': ('Segoe UI', 14, 'bold'),
            'body': ('Segoe UI', 10),
            'body_bold': ('Segoe UI', 10, 'bold'),
            'small': ('Segoe UI', 9),
            'code': ('Consolas', 10),
            'code_small': ('Consolas', 9),
        }
        
        # Component styles
        self.styles = {
            'main_window': {
                'bg': self.colors['bg_primary'],
                'padx': 20,
                'pady': 20,
            },
            'card': {
                'bg': self.colors['bg_secondary'],
                'relief': 'flat',
                'borderwidth': 1,
                'highlightbackground': self.colors['border'],
                'padx': 16,
                'pady': 16,
            },
            'button_primary': {
                'bg': self.colors['primary'],
                'activebackground': self.colors['primary_hover'],
                'relief': 'flat',
                'borderwidth': 0,
                'cursor': 'hand2',
            },
            'button_secondary': {
                'bg': self.colors['bg_tertiary'],
                'activebackground': self.colors['border'],
                'relief': 'flat',
                'borderwidth': 1,
                'cursor': 'hand2',
            },
            'listbox': {
                'bg': self.colors['bg_secondary'],
                'fg': self.colors['text_primary'],
                'selectbackground': self.colors['selection'],
                'selectforeground': self.colors['text_primary'],
                'borderwidth': 1,
                'highlightthickness': 0,
                'relief': 'flat',
                'font': self.fonts['body'],
                'activestyle': 'none',
            },
            'text_input': {
                'bg': self.colors['bg_secondary'],
                'fg': self.colors['text_primary'],
                'insertbackground': self.colors['text_primary'],
                'selectbackground': self.colors['selection'],
                'selectforeground': self.colors['text_primary'],
                'borderwidth': 1,
                'highlightthickness': 1,
                'highlightbackground': self.colors['border'],
                'highlightcolor': self.colors['border_focus'],
                'relief': 'flat',
                'font': self.fonts['body'],
            },
            'text_response': {
                'bg': self.colors['bg_tertiary'],
                'fg': self.colors['text_primary'],
                'selectbackground': self.colors['selection'],
                'selectforeground': self.colors['text_primary'],
                'borderwidth': 1,
                'highlightthickness': 0,
                'relief': 'flat',
                'font': self.fonts['code'],
            },
            'label_heading': {
                'bg': self.colors['bg_primary'],
            },
            'label_body': {
                'bg': self.colors['bg_primary'],
            },
            'label_secondary': {
                'bg': self.colors['bg_primary'],
            },
            'status_bar': {
                'bg': self.colors['bg_secondary'],
                'fg': self.colors['text_secondary'],
                'font': self.fonts['small'],
                'relief': 'flat',
                'borderwidth': 1,
                'highlightbackground': self.colors['border'],
            },
        }

class ModernDarkTheme(Theme):
    """Modern dark theme for night mode."""
    
    def _setup_theme(self):
        # Color palette - Dark mode
        self.colors = {
            'bg_primary': '#1a1a1a',      # Main background
            'bg_secondary': '#2d2d2d',     # Cards, panels
            'bg_tertiary': '#3d3d3d',     # Input fields
            'bg_accent': '#264653',       # Highlights
            'border': '#404040',          # Borders
            'border_focus': '#4dabf7',    # Focused borders
            'text_primary': '#ffffff',    # Main text
            'text_secondary': '#b0b0b0',  # Secondary text
            'text_muted': '#808080',      # Muted text
            'primary': '#4dabf7',         # Primary buttons
            'primary_hover': '#339af0',   # Primary hover
            'success': '#51cf66',         # Success states
            'warning': '#ffd43b',         # Warning states
            'danger': '#ff6b6b',          # Error states
            'selection': '#2b5797',       # Selected items
            'hover': '#404040',           # Hover states
        }
        
        # Typography (same as light theme)
        self.fonts = {
            'heading': ('Segoe UI', 14, 'bold'),
            'body': ('Segoe UI', 10),
            'body_bold': ('Segoe UI', 10, 'bold'),
            'small': ('Segoe UI', 9),
            'code': ('Consolas', 10),
            'code_small': ('Consolas', 9),
        }
        
        # Component styles (adapted for dark mode)
        self.styles = {
            'main_window': {
                'bg': self.colors['bg_primary'],
                'padx': 20,
                'pady': 20,
            },
            'card': {
                'bg': self.colors['bg_secondary'],
                'relief': 'flat',
                'borderwidth': 1,
                'highlightbackground': self.colors['border'],
                'padx': 16,
                'pady': 16,
            },
            'button_primary': {
                'bg': self.colors['primary'],
                'fg': 'white',
                'activebackground': self.colors['primary_hover'],
                'activeforeground': 'white',
                'relief': 'flat',
                'borderwidth': 0,
                'padx': 16,
                'pady': 8,
                'font': self.fonts['body_bold'],
                'cursor': 'hand2',
            },
            'button_secondary': {
                'bg': self.colors['bg_tertiary'],
                'fg': self.colors['text_primary'],
                'activebackground': self.colors['hover'],
                'activeforeground': self.colors['text_primary'],
                'relief': 'flat',
                'borderwidth': 1,
                'highlightbackground': self.colors['border'],
                'padx': 12,
                'pady': 6,
                'font': self.fonts['body'],
                'cursor': 'hand2',
            },
            'listbox': {
                'bg': self.colors['bg_secondary'],
                'fg': self.colors['text_primary'],
                'selectbackground': self.colors['selection'],
                'selectforeground': self.colors['text_primary'],
                'borderwidth': 1,
                'highlightthickness': 0,
                'relief': 'flat',
                'font': self.fonts['body'],
                'activestyle': 'none',
            },
            'text_input': {
                'bg': self.colors['bg_secondary'],
                'fg': self.colors['text_primary'],
                'insertbackground': self.colors['text_primary'],
                'selectbackground': self.colors['selection'],
                'selectforeground': self.colors['text_primary'],
                'borderwidth': 1,
                'highlightthickness': 1,
                'highlightbackground': self.colors['border'],
                'highlightcolor': self.colors['border_focus'],
                'relief': 'flat',
                'font': self.fonts['body'],
            },
            'text_response': {
                'bg': self.colors['bg_tertiary'],
                'fg': self.colors['text_primary'],
                'selectbackground': self.colors['selection'],
                'selectforeground': self.colors['text_primary'],
                'borderwidth': 1,
                'highlightthickness': 0,
                'relief': 'flat',
                'font': self.fonts['code'],
            },
            'label_heading': {
                'bg': self.colors['bg_primary'],
            },
            'label_body': {
                'bg': self.colors['bg_primary'],
            },
            'label_secondary': {
                'bg': self.colors['bg_primary'],
            },
            'status_bar': {
                'bg': self.colors['bg_secondary'],
                'fg': self.colors['text_secondary'],
                'font': self.fonts['small'],
                'relief': 'flat',
                'borderwidth': 1,
                'highlightbackground': self.colors['border'],
            },
        }

class ThemeManager:
    """Manages themes and provides easy switching."""
    
    def __init__(self):
        self.themes = {
            'light': ModernLightTheme(),
            'dark': ModernDarkTheme(),
        }
        self.current_theme_name = 'light'
        self.current_theme = self.themes[self.current_theme_name]
        
        # Load saved theme preference
        self._load_theme_preference()
    
    def _load_theme_preference(self):
        """Load theme preference from environment or file."""
        # Try to load from environment variable
        theme_pref = os.getenv('UI_THEME', 'light')
        if theme_pref in self.themes:
            self.current_theme_name = theme_pref
            self.current_theme = self.themes[theme_pref]
    
    def switch_theme(self, theme_name: str):
        """Switch to a different theme."""
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            self.current_theme = self.themes[theme_name]
            return True
        return False
    
    def get_current_theme(self) -> Theme:
        """Get the current active theme."""
        return self.current_theme
    
    def get_available_themes(self) -> list:
        """Get list of available theme names."""
        return list(self.themes.keys())
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = 'dark' if self.current_theme_name == 'light' else 'light'
        return self.switch_theme(new_theme)

# Global theme manager instance
theme_manager = ThemeManager()