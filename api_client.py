"""
OpenAI API client for the Code Chat application.
"""
import openai
from typing import List, Dict, Any, Callable, Optional
from models import ConversationMessage, AppConfig

class OpenAIClient:
    """Handles OpenAI API communication."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.config = AppConfig.get_default()
        self._client = None
        
    def set_api_key(self, api_key: str):
        """Set the OpenAI API key."""
        self.api_key = api_key
        self._client = None  # Reset client to pick up new key
        
    def _get_client(self) -> openai.OpenAI:
        """Get or create OpenAI client instance."""
        if not self._client or not self.api_key:
            if not self.api_key:
                raise ValueError("API key is required")
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is set and working."""
        return bool(self.api_key)
    
    def create_system_message(self, codebase_content: str) -> ConversationMessage:
        """
        Create system message with codebase content.
        
        Args:
            codebase_content: Combined content from all codebase files
            
        Returns:
            ConversationMessage with system role
        """
        content = (
            "You are a helpful AI assistant that helps with code analysis. "
            f"The user has provided the following codebase:\n\n{codebase_content}"
        )
        return ConversationMessage(role="system", content=content)
    
    def send_chat_request(
        self,
        conversation_history: List[ConversationMessage],
        codebase_content: str,
        model: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> str:
        """
        Send chat request to OpenAI API.
        
        Args:
            conversation_history: List of conversation messages
            codebase_content: Combined codebase content for system message
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens for response
            temperature: Temperature for response generation
            
        Returns:
            AI response content
            
        Raises:
            Exception: If API call fails or API key is invalid
        """
        if not self.validate_api_key():
            raise Exception("API key is not configured")
        
        try:
            client = self._get_client()
            
            # Prepare messages
            system_message = self.create_system_message(codebase_content)
            messages = [system_message.to_dict()]
            messages.extend([msg.to_dict() for msg in conversation_history])
            
            # Use provided parameters or defaults
            model = model or self.config.default_model
            max_tokens = max_tokens or self.config.default_max_tokens
            temperature = temperature or self.config.default_temperature
            
            # Make API call
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except openai.AuthenticationError:
            raise Exception("Invalid API key. Please check your OpenAI API key.")
        except openai.RateLimitError:
            raise Exception("Rate limit exceeded. Please try again later.")
        except openai.APITimeoutError:
            raise Exception("Request timed out. Please try again.")
        except openai.APIConnectionError:
            raise Exception("Connection error. Please check your internet connection.")
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")
    
    async def send_chat_request_async(
        self,
        conversation_history: List[ConversationMessage],
        codebase_content: str,
        model: str = None,
        max_tokens: int = None,
        temperature: float = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Async version of send_chat_request.
        
        This is a placeholder for potential future async implementation.
        Currently just calls the synchronous version.
        """
        result = self.send_chat_request(
            conversation_history, codebase_content, model, max_tokens, temperature
        )
        if callback:
            callback(result)
        return result