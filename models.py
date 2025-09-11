"""
Data models and constants for the Code Chat application.
"""
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AppConfig:
    """Application configuration."""
    available_models: List[str]
    default_model: str
    default_max_tokens: int
    default_temperature: float
    window_geometry: str
    
    @classmethod
    def get_default(cls) -> 'AppConfig':
        return cls(
            available_models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            default_model="gpt-3.5-turbo",
            default_max_tokens=2000,
            default_temperature=0.7,
            window_geometry="1000x700"
        )

@dataclass
class ConversationMessage:
    """Represents a single message in the conversation."""
    role: str  # "user", "assistant", or "system"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

class AppState:
    """Manages the application state."""
    
    def __init__(self):
        self.conversation_history: List[ConversationMessage] = []
        self.selected_directory: str = ""
        self.codebase_files: List[str] = []
        self.persistent_selected_files: List[str] = []  # Files selected in first turn
        self.api_key: str = ""
        self.selected_model: str = AppConfig.get_default().default_model
        
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        message = ConversationMessage(role=role, content=content)
        self.conversation_history.append(message)
        
    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []
        self.persistent_selected_files = []  # Also clear persistent files when conversation is cleared
        
    def set_persistent_files(self, selected_files: List[str]):
        """Set the files that should persist across turns."""
        self.persistent_selected_files = selected_files.copy()
        
    def get_persistent_files(self) -> List[str]:
        """Get the files that should persist across turns."""
        return self.persistent_selected_files.copy()
        
    def get_conversation_dict(self) -> List[Dict[str, str]]:
        """Get conversation history as list of dicts for API calls."""
        return [msg.to_dict() for msg in self.conversation_history]