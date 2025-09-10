"""
AI processing utilities for the Code Chat application.
"""
import requests
import time
from typing import List, Dict, Any, Callable, Optional, Union
from system_message_manager import system_message_manager

class AIProviderConfig:
    """Configuration for different AI providers."""
    
    PROVIDERS = {
        "openrouter": {
            "api_url": "https://openrouter.ai/api/v1/chat/completions",
            "headers": {
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yourusername/code-chat-ai",
                "X-Title": "Code Chat with AI"
            },
            "auth_header": "Authorization",
            "auth_format": "Bearer {api_key}",
            "supports_tokens": True,
            "response_path": {
                "content": ["choices", 0, "message", "content"],
                "tokens": {
                    "prompt": ["usage", "prompt_tokens"],
                    "completion": ["usage", "completion_tokens"],
                    "total": ["usage", "total_tokens"]
                }
            }
        },
        "tachyon": {
            "api_url": "https://api.tachyon.ai/v1/chat/completions",  # Update with actual Tachyon URL
            "headers": {
                "Content-Type": "application/json"
            },
            "auth_header": "Authorization",
            "auth_format": "Bearer {api_key}",
            "supports_tokens": True,
            "response_path": {
                "content": ["choices", 0, "message", "content"],
                "tokens": {
                    "prompt": ["usage", "prompt_tokens"],
                    "completion": ["usage", "completion_tokens"],
                    "total": ["usage", "total_tokens"]
                }
            }
        }
    }

class AIProcessor:
    """Handles AI request processing and API communication."""
    
    def __init__(self, api_key: str = "", provider: str = "openrouter"):
        self.api_key = api_key
        self.provider = provider
        self._validate_provider()
        
    def _validate_provider(self):
        """Validate that the provider is supported."""
        if self.provider not in AIProviderConfig.PROVIDERS:
            available = ", ".join(AIProviderConfig.PROVIDERS.keys())
            raise ValueError(f"Unsupported provider '{self.provider}'. Available: {available}")
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get configuration for the current provider."""
        return AIProviderConfig.PROVIDERS[self.provider]
        
    def set_api_key(self, api_key: str):
        """Set the API key."""
        self.api_key = api_key
    
    def set_provider(self, provider: str):
        """Set the AI provider."""
        self.provider = provider
        self._validate_provider()
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        return list(AIProviderConfig.PROVIDERS.keys())
    
    def get_provider_info(self, provider: str = None) -> Dict[str, Any]:
        """Get information about a specific provider or current provider."""
        if provider is None:
            provider = self.provider
        
        if provider not in AIProviderConfig.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = AIProviderConfig.PROVIDERS[provider]
        return {
            "name": provider,
            "api_url": config["api_url"],
            "supports_tokens": config["supports_tokens"],
            "auth_header": config["auth_header"]
        }
    
    def get_provider_debug_info(self) -> Dict[str, Any]:
        """Get detailed debug information for the current provider."""
        config = self.get_provider_config()
        debug_info = {
            "provider": self.provider,
            "api_url": config["api_url"],
            "auth_header": config["auth_header"],
            "supports_tokens": config["supports_tokens"],
            "has_api_key": bool(self.api_key),
        }
        
        # Provider-specific debug info
        if self.provider == "openrouter":
            debug_info.update({
                "openrouter_headers": ["HTTP-Referer", "X-Title"],
                "streaming_disabled": True,
                "routing_enabled": True
            })
        elif self.provider == "tachyon":
            debug_info.update({
                "tachyon_user_agent": "CodeChatAI/1.0",
                "streaming_disabled": True,
                "priority_queue_support": True
            })
        
        return debug_info
        
    def validate_api_key(self) -> bool:
        """Validate that the API key is set."""
        return bool(self.api_key)
    
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
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for the current provider."""
        config = self.get_provider_config()
        headers = config["headers"].copy()
        
        # Add authentication header
        auth_header = config["auth_header"]
        auth_format = config["auth_format"]
        headers[auth_header] = auth_format.format(api_key=self.api_key)
        
        # Provider-specific header customizations
        if self.provider == "openrouter":
            # OpenRouter specific headers
            headers["HTTP-Referer"] = headers.get("HTTP-Referer", "https://github.com/yourusername/code-chat-ai")
            headers["X-Title"] = headers.get("X-Title", "Code Chat with AI")
            # Could add OpenRouter-specific rate limiting or other headers here
            
        elif self.provider == "tachyon":
            # Tachyon specific headers
            headers["User-Agent"] = "CodeChatAI/1.0"
            # Add any Tachyon-specific headers here
            # headers["X-Tachyon-Client"] = "code-chat-ai"
            # headers["X-Request-ID"] = str(uuid.uuid4())  # if needed
        
        return headers
    
    def _prepare_request_data(self, messages: List[Dict], model: str) -> Dict[str, Any]:
        """Prepare request data for the current provider."""
        # Base OpenAI-compatible format for both providers
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 10000,
            "temperature": 0.1
        }
        
        # Provider-specific request data customizations
        if self.provider == "openrouter":
            # OpenRouter specific parameters
            data["stream"] = False  # Ensure no streaming for OpenRouter
            # Could add OpenRouter-specific parameters here:
            # data["top_p"] = 1.0
            # data["frequency_penalty"] = 0.0
            # data["presence_penalty"] = 0.0
            # data["route"] = "fallback"  # OpenRouter routing options
            
        elif self.provider == "tachyon":
            # Tachyon specific parameters
            data["stream"] = False  # Ensure no streaming for Tachyon
            # Could add Tachyon-specific parameters here:
            # data["response_format"] = {"type": "text"}
            # data["tachyon_mode"] = "standard"  # if Tachyon has specific modes
            # data["priority"] = "normal"  # if Tachyon supports priority queues
        
        return data
    
    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """Extract response content using provider-specific path."""
        config = self.get_provider_config()
        content_path = config["response_path"]["content"]
        
        try:
            # Provider-specific response content extraction
            if self.provider == "openrouter":
                # OpenRouter might have additional response fields or metadata
                result = response_data
                for key in content_path:
                    result = result[key]
                
                # OpenRouter might include model info or routing details
                if "model" in response_data:
                    actual_model = response_data.get("model", "unknown")
                    # Could log or use this info if needed
                
                return result
                
            elif self.provider == "tachyon":
                # Tachyon might have different response structure
                result = response_data
                for key in content_path:
                    result = result[key]
                
                # Tachyon might include processing time or other metadata
                if "tachyon_metadata" in response_data:
                    # Could handle Tachyon-specific metadata here
                    pass
                
                return result
            
            else:
                # Fallback to standard extraction
                result = response_data
                for key in content_path:
                    result = result[key]
                return result
                
        except (KeyError, IndexError, TypeError) as e:
            # Provider-specific error handling
            if self.provider == "openrouter":
                raise Exception(f"Failed to extract OpenRouter response content: {str(e)}")
            elif self.provider == "tachyon":
                raise Exception(f"Failed to extract Tachyon response content: {str(e)}")
            else:
                raise Exception(f"Failed to extract response content: {str(e)}")
    
    def _extract_token_usage(self, response_data: Dict[str, Any]) -> tuple[int, int, int]:
        """Extract token usage information with provider-specific handling."""
        config = self.get_provider_config()
        
        if not config["supports_tokens"] or not config["response_path"]["tokens"]:
            return 0, 0, 0
        
        token_paths = config["response_path"]["tokens"]
        
        try:
            # Provider-specific token extraction
            if self.provider == "openrouter":
                # OpenRouter standard token extraction
                prompt_tokens = self._extract_nested_value(response_data, token_paths["prompt"], 0)
                completion_tokens = self._extract_nested_value(response_data, token_paths["completion"], 0)
                total_tokens = self._extract_nested_value(response_data, token_paths["total"], 0)
                
                # OpenRouter might have additional billing info
                if "usage" in response_data and "cost" in response_data["usage"]:
                    # Could store cost information if needed
                    pass
                
                # If total not provided, calculate
                if total_tokens == 0:
                    total_tokens = prompt_tokens + completion_tokens
                
                return prompt_tokens, completion_tokens, total_tokens
                
            elif self.provider == "tachyon":
                # Tachyon might use different token field names or structure
                prompt_tokens = self._extract_nested_value(response_data, token_paths["prompt"], 0)
                completion_tokens = self._extract_nested_value(response_data, token_paths["completion"], 0)
                total_tokens = self._extract_nested_value(response_data, token_paths["total"], 0)
                
                # Tachyon might have processing efficiency metrics
                if "tachyon_metrics" in response_data:
                    # Could extract processing time, efficiency, etc.
                    pass
                
                # If total not provided, calculate
                if total_tokens == 0:
                    total_tokens = prompt_tokens + completion_tokens
                
                return prompt_tokens, completion_tokens, total_tokens
            
            else:
                # Fallback standard extraction
                prompt_tokens = self._extract_nested_value(response_data, token_paths["prompt"], 0)
                completion_tokens = self._extract_nested_value(response_data, token_paths["completion"], 0)
                total_tokens = self._extract_nested_value(response_data, token_paths["total"], 0)
                
                if total_tokens == 0:
                    total_tokens = prompt_tokens + completion_tokens
                
                return prompt_tokens, completion_tokens, total_tokens
            
        except (KeyError, IndexError, TypeError):
            return 0, 0, 0
    
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
            config = self.get_provider_config()
            headers = self._prepare_headers()
            data = self._prepare_request_data(messages, model)
            
            # Start timing the API call
            start_time = time.time()
            
            # Make API call
            response = requests.post(config["api_url"], headers=headers, json=data)
            
            if response.status_code != 200:
                # Provider-specific error messages
                if self.provider == "openrouter":
                    if response.status_code == 401:
                        raise Exception("OpenRouter API key is invalid or expired")
                    elif response.status_code == 429:
                        raise Exception("OpenRouter rate limit exceeded. Please try again later")
                    elif response.status_code == 502:
                        raise Exception("OpenRouter service temporarily unavailable")
                    else:
                        raise Exception(f"OpenRouter API request failed: {response.status_code} - {response.text}")
                        
                elif self.provider == "tachyon":
                    if response.status_code == 401:
                        raise Exception("Tachyon API key is invalid or expired")
                    elif response.status_code == 429:
                        raise Exception("Tachyon rate limit exceeded. Please try again later")
                    elif response.status_code == 503:
                        raise Exception("Tachyon service temporarily unavailable")
                    else:
                        raise Exception(f"Tachyon API request failed: {response.status_code} - {response.text}")
                        
                else:
                    raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            response_data = response.json()
            
            # Calculate execution time
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Extract AI response using provider-specific method
            ai_response = self._extract_response_content(response_data)
            
            # Extract token usage information using provider-specific method
            prompt_tokens, completion_tokens, total_tokens = self._extract_token_usage(response_data)
            
            # Update UI if callback provided
            if update_callback:
                if config["supports_tokens"] and total_tokens > 0:
                    status_msg = f"Ready • {self.provider.title()} • Input: {prompt_tokens} tokens • Output: {completion_tokens} tokens • Total: {total_tokens} • Time: {execution_time:.2f}s"
                else:
                    status_msg = f"Ready • {self.provider.title()} • Time: {execution_time:.2f}s"
                update_callback(ai_response, status_msg)
            
            return ai_response
            
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error. Please check your internet connection."
            if update_callback:
                update_callback(f"Error: {error_msg}", error_msg)
            raise Exception(error_msg)
        except requests.exceptions.Timeout:
            error_msg = "Request timed out. Please try again."
            if update_callback:
                update_callback(f"Error: {error_msg}", error_msg)
            raise Exception(error_msg)
        except KeyError as e:
            error_msg = f"Invalid API response format: {str(e)}"
            if update_callback:
                update_callback(f"Error: {error_msg}", error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = str(e)
            if update_callback:
                update_callback(f"Error: {error_msg}", error_msg)
            raise
    
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