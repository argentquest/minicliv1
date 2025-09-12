"""
Modern theme system for the Code Chat application.

This module provides a comprehensive theming system that supports multiple
visual themes (light/dark) with consistent color palettes, typography, and
component styling. The theme system is designed to be extensible and allows
for easy addition of new themes.

Key Components:
- Theme: Abstract base class for all themes
- ModernLightTheme: Professional light theme implementation  
- ModernDarkTheme: Eye-friendly dark theme implementation
- ThemeManager: Central theme management and switching logic

The theming system provides:
- Consistent color palettes across the application
- Typography scales and font definitions
- Component-specific styling rules  
- Dynamic theme switching with persistence
- Integration with environment variables for user preferences
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
import os

class Theme:
    """
    Abstract base class for application themes.
    
    This class defines the interface that all themes must implement and provides
    common functionality for theme application. Themes consist of three main
    components: colors, fonts, and component-specific styles.
    
    Attributes:
        colors (Dict): Color palette with semantic color names
        fonts (Dict): Font definitions for different text scales  
        styles (Dict): Component-specific styling rules
        
    Design Pattern:
        Uses the Template Method pattern where subclasses implement
        _setup_theme() to define their specific visual characteristics.
    """
    
    def __init__(self):
        """
        Initialize theme with empty defaults.
        
        Calls _setup_theme() to allow subclasses to populate the theme
        with their specific colors, fonts, and styles.
        """
        # Initialize empty theme containers
        self.colors = {}
        self.fonts = {}
        self.styles = {}
        
        # Let subclass populate theme data
        self._setup_theme()
    
    def _setup_theme(self):
        """
        Template method for subclasses to implement their theme.
        
        Subclasses should override this method to populate:
        - self.colors: Color palette dictionary
        - self.fonts: Font definition dictionary  
        - self.styles: Component styling dictionary
        
        Note:
            This is called during __init__, so subclasses can assume
            the base attributes are already initialized.
        """
        pass
    
    def apply_to_root(self, root: tk.Tk):
        """
        Apply theme's primary background color to the root window.
        
        Args:
            root (tk.Tk): The main application window to theme
            
        Note:
            Falls back to white if bg_primary is not defined in the theme.
        """
        primary_bg = self.colors.get('bg_primary', '#ffffff')
        root.configure(bg=primary_bg)
    
    def get_style(self, component: str) -> Dict[str, Any]:
        """
        Retrieve styling configuration for a specific UI component.
        
        Args:
            component (str): Name of the component to get styles for
            
        Returns:
            Dict[str, Any]: Styling dictionary with tkinter configuration
            options, or empty dict if component is not defined.
            
        Example:
            button_style = theme.get_style('button_primary')
            my_button.configure(**button_style)
        """
        return self.styles.get(component, {})

class ModernLightTheme(Theme):
    """
    Modern light theme with clean, professional styling.
    
    This theme implements a bright, high-contrast design suitable for
    daytime use and professional environments. It uses a modern blue and 
    gray color palette inspired by contemporary design systems.
    
    Design Philosophy:
    - High contrast for excellent readability
    - Professional blue accent colors
    - Clean, minimal visual hierarchy
    - Accessibility-focused color choices
    
    Best suited for:
    - Daytime work sessions
    - Professional presentations  
    - Users who prefer high contrast
    - Bright environments
    """
    
    def _setup_theme(self):
        """
        Configure the light theme's visual properties.
        
        Sets up a comprehensive color palette, typography scale, and
        component styles optimized for daytime use and readability.
        """
        # Color palette - Modern blue/gray with high contrast
        self.colors = {
            # Background hierarchy - from lightest to darkest
            'bg_primary': '#f8f9fa',      # Main app background (light gray)
            'bg_secondary': '#ffffff',     # Cards, panels, content areas (white)
            'bg_tertiary': '#e9ecef',     # Input fields, disabled states (medium gray)
            'bg_accent': '#f0f7ff',       # Highlights, selected areas (light blue tint)
            
            # Border colors for visual separation
            'border': '#dee2e6',          # Standard borders (light gray)
            'border_focus': '#0d6efd',    # Focused element borders (blue)
            
            # Text hierarchy - from most prominent to subtle
            'text_primary': '#212529',    # Main text, headings (dark gray)
            'text_secondary': '#6c757d',  # Supporting text, labels (medium gray)
            'text_muted': '#adb5bd',      # Placeholder text, disabled (light gray)
            
            # Interactive element colors
            'primary': '#0d6efd',         # Primary action buttons (blue)
            'primary_hover': '#0b5ed7',   # Primary button hover state (darker blue)
            
            # Semantic colors for user feedback
            'success': '#198754',         # Success messages, confirmations (green)
            'warning': '#ffc107',         # Warnings, alerts (yellow/orange)
            'danger': '#dc3545',          # Errors, destructive actions (red)
            
            # Interactive states
            'selection': '#e7f3ff',       # Selected list items, highlights (light blue)
            'hover': '#f8f9fa',           # Subtle hover effects (light gray)
        }
        
        # Typography scale - optimized for Windows/cross-platform readability
        self.fonts = {
            'heading': ('Segoe UI', 14, 'bold'),    # Section headers, dialog titles
            'body': ('Segoe UI', 10),               # Main body text, buttons, labels
            'body_bold': ('Segoe UI', 10, 'bold'),  # Emphasized body text
            'small': ('Segoe UI', 9),               # Secondary info, captions
            'code': ('Consolas', 10),               # Code blocks, file content
            'code_small': ('Consolas', 9),          # Inline code, file lists
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
    """
    Central theme management system for the application.
    
    This singleton-like class manages all available themes, handles theme
    switching, and provides access to the current theme throughout the
    application. It integrates with the environment variable system to
    persist user theme preferences across sessions.
    
    Features:
    - Theme registration and management
    - Persistent theme preferences via environment variables
    - Runtime theme switching
    - Default theme fallback handling
    
    Usage:
        # Get current theme for styling
        theme = theme_manager.get_current_theme()
        
        # Switch themes programmatically
        theme_manager.switch_theme('dark')
        
        # Toggle between available themes
        theme_manager.toggle_theme()
    """
    
    def __init__(self):
        """
        Initialize the theme manager with available themes.
        
        Sets up the theme registry with built-in themes and loads
        the user's saved theme preference from environment variables.
        """
        # Registry of available themes
        self.themes = {
            'light': ModernLightTheme(),
            'dark': ModernDarkTheme(),
        }
        
        # Default to light theme initially
        self.current_theme_name = 'light'
        self.current_theme = self.themes[self.current_theme_name]
        
        # Load user's saved theme preference from environment
        self._load_theme_preference()
    
    def _load_theme_preference(self):
        """
        Load user's theme preference from environment variables.
        
        Checks the UI_THEME environment variable and switches to the
        specified theme if it exists in the theme registry. Falls back
        to light theme if the preference is invalid or not set.
        
        Environment Variable:
            UI_THEME: 'light' or 'dark' (defaults to 'light')
        """
        # Read theme preference from environment (set by .env file or system)
        theme_pref = os.getenv('UI_THEME', 'light')
        
        # Validate and apply the theme preference
        if theme_pref in self.themes:
            self.current_theme_name = theme_pref
            self.current_theme = self.themes[theme_pref]
        # If invalid preference, stick with current default
    
    def switch_theme(self, theme_name: str) -> bool:
        """
        Switch to a specific theme by name.
        
        Args:
            theme_name (str): Name of the theme to switch to
            
        Returns:
            bool: True if theme was successfully switched, False if 
            theme name is invalid or doesn't exist.
            
        Note:
            This method only changes the active theme in memory.
            To persist the change across sessions, the caller should
            also update the UI_THEME environment variable.
        """
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            self.current_theme = self.themes[theme_name]
            return True
        return False
    
    def get_current_theme(self) -> Theme:
        """
        Get the currently active theme object.
        
        Returns:
            Theme: The active theme instance with colors, fonts, and styles
            
        This is the primary method used by UI components to access
        theme properties for styling themselves.
        """
        return self.current_theme
    
    def get_available_themes(self) -> list:
        """
        Get list of all available theme names.
        
        Returns:
            list: List of theme names that can be passed to switch_theme()
            
        Useful for building theme selection UI components or
        validating theme names.
        """
        return list(self.themes.keys())
    
    def toggle_theme(self) -> bool:
        """
        Toggle between light and dark themes.
        
        Returns:
            bool: True if toggle was successful
            
        This is a convenience method for quickly switching between
        the two main themes. If more than two themes exist, this
        method only toggles between 'light' and 'dark'.
        
        Useful for theme toggle buttons in the UI.
        """
        new_theme = 'dark' if self.current_theme_name == 'light' else 'light'
        return self.switch_theme(new_theme)

# Global theme manager instance - used throughout the application
# This singleton-like pattern ensures consistent theme access across all modules
theme_manager = ThemeManager()