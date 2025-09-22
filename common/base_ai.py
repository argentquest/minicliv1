"""
Base AI Provider Classes and Interfaces

This module defines the abstract base classes and interfaces for AI providers
in the Code Chat application. It implements a provider pattern that allows
different AI services (OpenAI, Anthropic, etc.) to be integrated through
a consistent interface.

Architecture Overview:
- AIProviderConfig: Configuration class for provider settings
- BaseAIProvider: Abstract base class defining the provider interface
- Provider implementations: Concrete classes extending BaseAIProvider

Key Features:
- Abstract interface for AI provider implementations
- Standardized request/response handling
- Token usage tracking and reporting
- Secure API key management and validation
- Comprehensive error handling with retry logic
- Asynchronous processing support
- Debug information with sensitive data masking

The BaseAIProvider class defines the contract that all AI providers must
implement, ensuring consistent behavior across different AI services while
allowing for provider-specific optimizations and configurations.

Error Handling:
- Network timeout and connection error handling
- Automatic retry with exponential backoff
- Provider-specific error message formatting
- Secure error logging without exposing sensitive data

Security:
- API key validation and format checking
- Sensitive data masking in debug output
- Secure error message sanitization
- Provider-specific authentication handling
"""
import os
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional, Tuple
from .system_message_manager import system_message_manager
from security_utils import SecurityUtils


class AIProviderConfig:
    """Base configuration class for AI providers."""
    
    def __init__(self, name: str, api_url: str, supports_tokens: bool = True):
        self.name = name
        self.api_url = api_url
        self.supports_tokens = supports_tokens
        self.headers = {"Content-Type": "application/json"}
        self.auth_header = "Authorization"
        self.auth_format = "Bearer {api_key}"


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.config = self._get_provider_config()
        self._last_token_usage = 0  # Store last API call token usage
        
    @abstractmethod
    def _get_provider_config(self) -> AIProviderConfig:
        """Get provider-specific configuration."""
        pass
    
    @abstractmethod
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare provider-specific headers."""
        pass
    
    @abstractmethod
    def _prepare_request_data(self, messages: List[Dict], model: str) -> Dict[str, Any]:
        """Prepare provider-specific request data."""
        pass
    
    @abstractmethod
    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """Extract response content from provider response."""
        pass
    
    @abstractmethod
    def _extract_token_usage(self, response_data: Dict[str, Any]) -> Tuple[int, int, int]:
        """Extract token usage information (prompt_tokens, completion_tokens, total_tokens)."""
        pass
    
    @abstractmethod
    def _handle_api_error(self, status_code: int, response_text: str) -> str:
        """Handle provider-specific API errors."""
        pass
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.config.name
    
    def set_api_key(self, api_key: str):
        """Set the API key."""
        self.api_key = api_key
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is set."""
        return bool(self.api_key)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this provider."""
        return {
            "name": self.config.name,
            "api_url": self.config.api_url,
            "supports_tokens": self.config.supports_tokens,
            "auth_header": self.config.auth_header,
            "has_api_key": bool(self.api_key)
        }
    
    def get_secure_debug_info(self) -> Dict[str, Any]:
        """Get debug information with sensitive data masked for safe logging."""
        debug_info = {
            "name": self.config.name,
            "api_url": self.config.api_url,
            "supports_tokens": self.config.supports_tokens,
            "auth_header": self.config.auth_header,
            "has_api_key": bool(self.api_key),
            "api_key": SecurityUtils.mask_api_key(self.api_key) if self.api_key else None,
            "api_key_valid": SecurityUtils.validate_api_key_format(self.api_key, self.config.name)
        }
        
        return SecurityUtils.safe_debug_info(debug_info)
    
    def create_system_message(self, codebase_content: str) -> Dict[str, str]:
        """
        Create system message with codebase content.
        Uses custom system message from systemmessage.txt if available, otherwise default.
        
        Args:
            codebase_content: Combined content from all codebase files
            
        Returns:
            System message dictionary
        """
        content = system_message_manager.get_system_message(codebase_content)
        return {"role": "system", "content": content}
    
    def _extract_nested_value(self, data: Dict[str, Any], path: List[str], default: Any) -> Any:
        """Helper method to extract nested values safely."""
        if not path:
            return default
        
        try:
            result = data
            for key in path:
                result = result[key]
            return result
        except (KeyError, IndexError, TypeError):
            return default
    
    def process_question(
        self,
        question: str,
        conversation_history: List[Dict[str, str]],
        codebase_content: str,
        model: str,
        update_callback: Optional[Callable[[str, str], None]] = None
    ) -> str:
        """
        Process a question using AI API.
        
        Args:
            question: User's question
            conversation_history: Previous conversation messages (without system message)
            codebase_content: Combined codebase content (only used for first message)
            model: AI model to use
            update_callback: Callback for UI updates (response, status)
            
        Returns:
            AI response content
            
        Raises:
            Exception: If API call fails or API key is invalid
        """
        import requests
        
        try:
            if not self.validate_api_key():
                raise Exception("API key is not configured")
            
            # Create user message
            user_message = {"role": "user", "content": question}
            
            # Determine if this is the first message in conversation
            is_first_message = len(conversation_history) == 0
            
            # Include codebase context if this is first message OR if codebase_content is provided (tool commands)
            if is_first_message or (codebase_content and codebase_content.strip()):
                # Include system message with codebase content
                system_message = self.create_system_message(codebase_content)
                if is_first_message:
                    # First message: just system + user message
                    messages = [system_message, user_message]
                else:
                    # Tool command: system + conversation history + user message
                    messages = [system_message] + conversation_history + [user_message]
            else:
                # Follow-up messages: use existing conversation without recreating system message
                # The conversation_history should already include the original system message
                messages = conversation_history + [user_message]
            
            # Prepare provider-specific API request
            headers = self._prepare_headers()
            data = self._prepare_request_data(messages, model)
            
            # Start timing the API call
            start_time = time.time()
            
            # Make API call with timeout and retry logic
            timeout = (30, 120)  # (connect timeout, read timeout) in seconds
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    verify_ssl = os.getenv('VALIDATE_SSL', 'true').lower() == 'true'
                    response = requests.post(
                        self.config.api_url,
                        headers=headers,
                        json=data,
                        timeout=timeout,
                        verify=verify_ssl
                    )
                    
                    if response.status_code != 200:
                        error_msg = self._handle_api_error(response.status_code, response.text)
                        
                        # Retry on server errors (5xx), but not client errors (4xx)
                        if response.status_code >= 500 and retry_count < max_retries - 1:
                            retry_count += 1
                            time.sleep(min(2 ** retry_count, 10))  # Exponential backoff, max 10s
                            continue
                        
                        raise Exception(error_msg)
                    
                    break  # Success, exit retry loop
                    
                except requests.exceptions.Timeout as e:
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        time.sleep(min(2 ** retry_count, 10))  # Exponential backoff
                        continue
                    else:
                        raise Exception("Request timed out after multiple retries. Please check your network connection and try again.")
                        
                except requests.exceptions.ConnectionError as e:
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        time.sleep(min(2 ** retry_count, 10))  # Exponential backoff
                        continue
                    else:
                        raise Exception("Connection failed after multiple retries. Please check your internet connection.")
            
            response_data = response.json()
            
            # Calculate execution time
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Extract AI response using provider-specific method
            ai_response = self._extract_response_content(response_data)
            
            # Extract token usage information using provider-specific method
            prompt_tokens, completion_tokens, total_tokens = self._extract_token_usage(response_data)
            
            # Store token usage for statistics
            self._last_token_usage = total_tokens
            
            # Update UI if callback provided
            if update_callback:
                if self.config.supports_tokens and total_tokens > 0:
                    status_msg = f"Ready • {self.config.name.title()} • Input: {prompt_tokens} tokens • Output: {completion_tokens} tokens • Total: {total_tokens} • Time: {execution_time:.2f}s"
                else:
                    status_msg = f"Ready • {self.config.name.title()} • Time: {execution_time:.2f}s"
                update_callback(ai_response, status_msg)
            
            return ai_response
            
        except requests.exceptions.RequestException as e:
            # This catches all requests exceptions not handled above
            error_msg = f"Network request failed: {str(e)}"
            if update_callback:
                update_callback(f"Error: {error_msg}", error_msg)
            raise Exception(error_msg)
        except ValueError as e:
            # JSON parsing errors
            error_msg = f"Invalid API response format - could not parse JSON: {str(e)}"
            if update_callback:
                update_callback(f"Error: {error_msg}", error_msg)
            raise Exception(error_msg)
        except KeyError as e:
            error_msg = f"Invalid API response structure - missing field: {str(e)}"
            if update_callback:
                update_callback(f"Error: {error_msg}", error_msg)
            raise Exception(error_msg)
        except Exception as e:
            # Sanitize error message to avoid leaking sensitive information
            from security_utils import SecurityUtils
            sanitized_msg = SecurityUtils.sanitize_log_message(str(e))
            if update_callback:
                update_callback(f"Error: {sanitized_msg}", sanitized_msg)
            raise Exception(sanitized_msg)
    
    def process_question_async(
        self,
        question: str,
        conversation_history: List[Dict[str, str]],
        codebase_content: str,
        model: str,
        success_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        ui_update_callback: Optional[Callable[[str, str], None]] = None
    ):
        """
        Process question asynchronously with callbacks.
        
        Args:
            question: User's question
            conversation_history: Previous conversation messages
            codebase_content: Combined codebase content
            model: AI model to use
            success_callback: Called with AI response on success
            error_callback: Called with error message on failure
            ui_update_callback: Called for UI updates (response, status)
        """
        try:
            response = self.process_question(
                question, conversation_history, codebase_content, model, ui_update_callback
            )
            
            if success_callback:
                success_callback(response)
                
        except Exception as e:
            error_msg = str(e)
            if error_callback:
                error_callback(error_msg)
            if ui_update_callback:
                ui_update_callback(f"Error: {error_msg}", error_msg)