"""
Data models and constants for the Code Chat application.

This module defines the core data structures used throughout the application:
- AppConfig: Application configuration and defaults
- ConversationMessage: Individual chat messages
- AppState: Application runtime state management

The models follow a clean architecture pattern with clear separation of concerns
between configuration, data transfer objects, and state management.
"""
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AppConfig:
    """
    Application configuration dataclass containing default settings.
    
    This immutable configuration object holds all the default values
    for the application's operation, including AI model settings,
    UI preferences, and API parameters.
    
    Attributes:
        available_models (List[str]): List of available AI models for selection
        default_model (str): The default AI model to use on startup
        default_max_tokens (int): Default maximum tokens for AI responses
        default_temperature (float): Default temperature for AI creativity (0.0-1.0)
        window_geometry (str): Default window size in "widthxheight" format
    """
    available_models: List[str]
    default_model: str
    default_max_tokens: int
    default_temperature: float
    window_geometry: str
    
    @classmethod
    def get_default(cls) -> 'AppConfig':
        """
        Create a default application configuration.
        
        Returns:
            AppConfig: Configuration object with sensible defaults for
            a new installation or when no custom config is available.
            
        Note:
            These defaults prioritize stability and broad compatibility
            over cutting-edge features.
        """
        return cls(
            available_models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            default_model="gpt-3.5-turbo",  # Most stable and cost-effective
            default_max_tokens=2000,        # Balance between response length and speed
            default_temperature=0.7,        # Good balance of creativity and consistency
            window_geometry="1000x700"      # Reasonable default window size
        )

@dataclass
class ConversationMessage:
    """
    Represents a single message in the conversation history.
    
    This data transfer object encapsulates a single turn in the conversation,
    storing both the role (who sent the message) and the content (what was said).
    It's designed to be easily serializable for API calls and storage.
    
    Attributes:
        role (str): The message sender - "user", "assistant", or "system"
        content (str): The actual message content/text
        
    Note:
        The role field follows OpenAI API conventions where:
        - "user" = messages from the human user
        - "assistant" = responses from the AI
        - "system" = system prompts and instructions
    """
    role: str  
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert message to dictionary format for API calls.
        
        Returns:
            Dict[str, str]: Dictionary with 'role' and 'content' keys,
            compatible with OpenAI API message format.
        """
        return {"role": self.role, "content": self.content}

@dataclass  
class QuestionStatus:
    """
    Represents a question with its current processing status.
    
    This tracks individual questions through their lifecycle from
    submission through processing to completion.
    
    Attributes:
        question (str): The question text
        status (str): Current status - "working", "completed", "error"
        response (str): AI response (empty until completed)
        timestamp (str): When the question was submitted
        tokens_used (int): Total tokens used in the API call
        processing_time (float): Time taken to process the question in seconds
        model_used (str): AI model used for processing
    """
    question: str
    status: str = "working"  # working, completed, error
    response: str = ""
    timestamp: str = ""
    tokens_used: int = 0
    processing_time: float = 0.0
    model_used: str = ""

class AppState:
    """
    Manages the runtime application state and user session data.
    
    This mutable state object tracks all the dynamic information during
    a user session, including conversation history, file selections,
    API configuration, and user preferences. It provides methods for
    managing persistent file context across conversation turns.
    
    Key Features:
    - Conversation history management
    - File selection persistence for multi-turn conversations
    - API key and model selection tracking
    - Clean state reset capabilities
    """
    
    def __init__(self):
        """
        Initialize application state with empty defaults.
        
        Sets up empty containers for conversation history, file selections,
        and initializes API configuration to safe defaults.
        """
        # Conversation tracking
        self.conversation_history: List[ConversationMessage] = []
        
        # Question history tracking for new UI
        self.question_history: List[QuestionStatus] = []
        
        # File and directory management
        self.selected_directory: str = ""
        self.codebase_files: List[str] = []
        
        # Persistent file context - maintains file selection across conversation turns
        # This allows users to select files once and continue the conversation
        # without re-selecting files for each subsequent question
        self.persistent_selected_files: List[str] = []
        
        # API configuration
        self.api_key: str = ""
        self.selected_model: str = AppConfig.get_default().default_model
        
    def add_message(self, role: str, content: str):
        """
        Add a new message to the conversation history.
        
        Args:
            role (str): The message sender ("user", "assistant", or "system")
            content (str): The message content
            
        Note:
            This is a convenience method that automatically creates a
            ConversationMessage object and appends it to the history.
        """
        message = ConversationMessage(role=role, content=content)
        self.conversation_history.append(message)
        
    def clear_conversation(self):
        """
        Clear the conversation history and reset persistent state.
        
        This method performs a complete conversation reset:
        1. Clears all conversation history
        2. Resets persistent file selections
        3. Clears question history
        
        Used when starting a new conversation or switching system prompts.
        """
        self.conversation_history = []
        self.persistent_selected_files = []  # Reset file context for clean start
        self.question_history = []  # Reset question history for clean start
        
    def add_question(self, question: str) -> QuestionStatus:
        """
        Add a new question to the question history with working status.
        
        Args:
            question (str): The question text
            
        Returns:
            QuestionStatus: The created question status object
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        question_status = QuestionStatus(question=question, timestamp=timestamp)
        self.question_history.append(question_status)
        return question_status
        
    def update_question_status(self, question_index: int, status: str, response: str = "", 
                             tokens_used: int = 0, processing_time: float = 0.0, model_used: str = ""):
        """
        Update the status of a question in the history.
        
        Args:
            question_index (int): Index of the question in the history
            status (str): New status ("working", "completed", "error")
            response (str): AI response (optional)
            tokens_used (int): Total tokens used in the API call
            processing_time (float): Time taken to process the question in seconds
            model_used (str): AI model used for processing
        """
        if 0 <= question_index < len(self.question_history):
            question_status = self.question_history[question_index]
            question_status.status = status
            if response:
                question_status.response = response
            if tokens_used > 0:
                question_status.tokens_used = tokens_used
            if processing_time > 0:
                question_status.processing_time = processing_time
            if model_used:
                question_status.model_used = model_used
        
    def set_persistent_files(self, selected_files: List[str]):
        """
        Set the files that should persist across conversation turns.
        
        Args:
            selected_files (List[str]): List of file paths to persist
            
        Note:
            Creates a copy of the input list to prevent external mutations.
            These files will be automatically used for subsequent AI requests
            until the conversation is cleared or files are changed.
        """
        self.persistent_selected_files = selected_files.copy()
        
    def get_persistent_files(self) -> List[str]:
        """
        Get the files that should persist across conversation turns.
        
        Returns:
            List[str]: Copy of the persistent file paths list
            
        Note:
            Returns a copy to prevent external code from modifying
            the internal state accidentally.
        """
        return self.persistent_selected_files.copy()
        
    def get_conversation_dict(self) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for API calls.
        
        Returns:
            List[Dict[str, str]]: List of message dictionaries with
            'role' and 'content' keys, ready for OpenAI API consumption.
            
        This method is used when preparing the conversation context
        for AI API requests, converting internal objects to the
        expected API format.
        """
        return [msg.to_dict() for msg in self.conversation_history]