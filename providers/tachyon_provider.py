"""
Tachyon AI provider implementation.
"""
from typing import Dict, Any, List, Tuple
from common.base_ai import BaseAIProvider, AIProviderConfig


class TachyonProvider(BaseAIProvider):
    """Tachyon-specific AI provider implementation."""
    
    def _get_provider_config(self) -> AIProviderConfig:
        """Get Tachyon-specific configuration."""
        config = AIProviderConfig(
            name="tachyon",
            api_url="https://api.tachyon.ai/v1/chat/completions",  # Update with actual Tachyon URL
            supports_tokens=True
        )
        
        return config
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare Tachyon-specific headers."""
        headers = self.config.headers.copy()
        
        # Add authentication header
        headers[self.config.auth_header] = self.config.auth_format.format(api_key=self.api_key)
        
        # Tachyon-specific headers
        headers["User-Agent"] = "CodeChatAI/1.0"
        
        # Add any additional Tachyon-specific headers here:
        # headers["X-Tachyon-Client"] = "code-chat-ai"
        # headers["X-Request-ID"] = str(uuid.uuid4())  # if needed
        
        return headers
    
    def _prepare_request_data(self, messages: List[Dict], model: str) -> Dict[str, Any]:
        """Prepare Tachyon-specific request data."""
        # Base OpenAI-compatible format
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 10000,
            "temperature": 0.1,
            "stream": False  # Ensure no streaming for Tachyon
        }
        
        # Tachyon-specific parameters can be added here:
        # data["response_format"] = {"type": "text"}
        # data["tachyon_mode"] = "standard"  # if Tachyon has specific modes
        # data["priority"] = "normal"  # if Tachyon supports priority queues
        
        return data
    
    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """Extract response content from Tachyon response."""
        try:
            # Standard OpenAI format path
            content = response_data["choices"][0]["message"]["content"]
            
            # Tachyon might include processing time or other metadata
            if "tachyon_metadata" in response_data:
                # Could handle Tachyon-specific metadata here
                metadata = response_data["tachyon_metadata"]
                # Example: processing_time = metadata.get("processing_time")
            
            return content
            
        except (KeyError, IndexError, TypeError) as e:
            raise Exception(f"Failed to extract Tachyon response content: {str(e)}")
    
    def _extract_token_usage(self, response_data: Dict[str, Any]) -> Tuple[int, int, int]:
        """Extract token usage information from Tachyon response."""
        try:
            usage = response_data.get("usage", {})
            
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # Tachyon might have processing efficiency metrics
            if "tachyon_metrics" in response_data:
                metrics = response_data["tachyon_metrics"]
                # Could extract processing time, efficiency, etc.
                # processing_time = metrics.get("processing_time")
                # efficiency_score = metrics.get("efficiency")
            
            # If total not provided, calculate
            if total_tokens == 0:
                total_tokens = prompt_tokens + completion_tokens
            
            return prompt_tokens, completion_tokens, total_tokens
            
        except (KeyError, IndexError, TypeError):
            return 0, 0, 0
    
    def _handle_api_error(self, status_code: int, response_text: str) -> str:
        """Handle Tachyon-specific API errors."""
        if status_code == 401:
            return "Tachyon API key is invalid or expired"
        elif status_code == 429:
            return "Tachyon rate limit exceeded. Please try again later"
        elif status_code == 503:
            return "Tachyon service temporarily unavailable"
        else:
            return f"Tachyon API request failed: {status_code} - {response_text}"
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get Tachyon-specific debug information."""
        base_info = self.get_provider_info()
        
        tachyon_info = {
            "tachyon_user_agent": "CodeChatAI/1.0",
            "streaming_disabled": True,
            "priority_queue_support": True,
            "custom_modes": ["standard", "fast", "accurate"],  # Example modes
            "efficiency_metrics": True
        }
        
        base_info.update(tachyon_info)
        return base_info