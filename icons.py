"""
Icon system for the Code Chat application using Unicode symbols and emojis.
"""
from typing import Dict, Optional
import os

class IconSet:
    """Icon set with Unicode symbols and emojis."""
    
    def __init__(self):
        # File type icons
        self.file_types = {
            '.py': '🐍',      # Python files
            '.js': '📜',      # JavaScript
            '.ts': '📘',      # TypeScript
            '.html': '🌐',    # HTML
            '.css': '🎨',     # CSS
            '.json': '📋',    # JSON
            '.md': '📝',      # Markdown
            '.txt': '📄',     # Text
            '.yml': '⚙️',     # YAML
            '.yaml': '⚙️',    # YAML
            '.xml': '📄',     # XML
            '.env': '🔧',     # Environment
            '.gitignore': '🚫', # Git ignore
            '.dockerfile': '🐳', # Docker
            'default': '📄',   # Default file
        }
        
        # Action icons
        self.actions = {
            'folder': '📁',
            'refresh': '🔄',
            'settings': '⚙️',
            'send': '📤',
            'save': '💾',
            'load': '📂',
            'clear': '🗑️',
            'new': '✨',
            'copy': '📋',
            'export': '📤',
            'import': '📥',
            'edit': '✏️',
            'delete': '🗑️',
            'search': '🔍',
            'filter': '🔽',
            'sort': '🔄',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'loading': '⏳',
            'play': '▶️',
            'pause': '⏸️',
            'stop': '⏹️',
            'close': '❌',
            'minimize': '➖',
            'maximize': '🔲',
            'theme_light': '☀️',
            'theme_dark': '🌙',
            'theme_toggle': '🌓',
        }
        
        # Status icons
        self.status = {
            'ready': '🟢',
            'processing': '🟡',
            'error': '🔴',
            'warning': '🟠',
            'info': '🔵',
            'success': '🟢',
        }
        
        # Selection icons
        self.selection = {
            'checked': '☑️',
            'unchecked': '☐',
            'select_all': '📋',
            'select_none': '📄',
            'selected': '✓',
            'unselected': '○',
        }
        
        # Navigation icons
        self.navigation = {
            'up': '⬆️',
            'down': '⬇️',
            'left': '⬅️',
            'right': '➡️',
            'expand': '🔽',
            'collapse': '🔼',
            'home': '🏠',
            'back': '⬅️',
            'forward': '➡️',
        }
        
        # AI/Chat icons
        self.chat = {
            'ai': '🤖',
            'user': '👤',
            'message': '💬',
            'thinking': '🤔',
            'response': '💭',
            'conversation': '💬',
            'history': '📚',
        }

class IconManager:
    """Manages icons and provides easy access."""
    
    def __init__(self):
        self.icons = IconSet()
        
    def get_file_icon(self, filename: str) -> str:
        """Get icon for a file based on its extension."""
        if not filename:
            return self.icons.file_types['default']
        
        # Handle special filenames
        special_files = {
            '.env': self.icons.file_types['.env'],
            '.gitignore': self.icons.file_types['.gitignore'],
            'dockerfile': self.icons.file_types['.dockerfile'],
            'docker-compose.yml': self.icons.file_types['.yml'],
            'requirements.txt': '📦',
            'package.json': '📦',
            'readme.md': '📖',
            'license': '📜',
        }
        
        filename_lower = filename.lower()
        if filename_lower in special_files:
            return special_files[filename_lower]
        
        # Get extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        return self.icons.file_types.get(ext, self.icons.file_types['default'])
    
    def get_action_icon(self, action: str) -> str:
        """Get icon for an action."""
        return self.icons.actions.get(action, '')
    
    def get_status_icon(self, status: str) -> str:
        """Get icon for a status."""
        return self.icons.status.get(status, '')
    
    def get_selection_icon(self, selected: bool) -> str:
        """Get icon for selection state."""
        return self.icons.selection['checked'] if selected else self.icons.selection['unchecked']
    
    def get_chat_icon(self, role: str) -> str:
        """Get icon for chat role."""
        return self.icons.chat.get(role, self.icons.chat['message'])
    
    def format_with_icon(self, text: str, icon_type: str, icon_key: str) -> str:
        """Format text with an icon."""
        icon_dict = getattr(self.icons, icon_type, {})
        icon = icon_dict.get(icon_key, '')
        return f"{icon} {text}" if icon else text
    
    def format_button_text(self, text: str, action: str) -> str:
        """Format button text with appropriate icon."""
        icon = self.get_action_icon(action)
        return f"{icon} {text}" if icon else text
    
    def format_file_text(self, filename: str) -> str:
        """Format filename with file type icon."""
        icon = self.get_file_icon(filename)
        return f"{icon} {filename}"
    
    def format_status_text(self, text: str, status: str) -> str:
        """Format status text with status icon."""
        icon = self.get_status_icon(status)
        return f"{icon} {text}" if icon else text

# Global icon manager instance
icon_manager = IconManager()