"""
OpenRouter AI Provider Implementation

This module implements the OpenRouter AI provider for the Code Chat application.
OpenRouter is a unified API that provides access to multiple AI models from
different providers (OpenAI, Anthropic, Google, etc.) through a single interface.

Key Features:
- Unified access to multiple AI providers through OpenRouter API
- Automatic model routing and fallback capabilities
- Cost tracking and billing information
- Standard OpenAI-compatible API format
- Custom headers for attribution and branding

OpenRouter-Specific Configuration:
- API URL: https://openrouter.ai/api/v1/chat/completions
- Supports token usage tracking
- Custom HTTP-Referer and X-Title headers for attribution
- Automatic model routing based on availability and cost
- Fallback routing for high availability

Usage:
    provider = OpenRouterProvider(api_key="your_openrouter_key")
    response = provider.process_question(
        question="Explain this code",
        conversation_history=[],
        codebase_content="...",
        model="openai/gpt-4"
    )

Error Handling:
- 401: Invalid or expired API key
- 429: Rate limit exceeded
- 502: Service temporarily unavailable
- Generic API errors with status code and response details

The provider implements all abstract methods from BaseAIProvider and handles
OpenRouter-specific response formats, token usage extraction, and error
handling while maintaining compatibility with the standard AI provider interface.
"""
from typing import Dict, Any, List, Tuple
from common.base_ai import BaseAIProvider, AIProviderConfig


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter-specific AI provider implementation."""
    
    def _get_provider_config(self) -> AIProviderConfig:
        """Get OpenRouter-specific configuration."""
        config = AIProviderConfig(
            name="openrouter",
            api_url="https://openrouter.ai/api/v1/chat/completions",
            supports_tokens=True
        )
        
        # OpenRouter-specific headers
        config.headers.update({
            "HTTP-Referer": "https://github.com/yourusername/code-chat-ai",
            "X-Title": "Code Chat with AI"
        })
        
        return config
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare OpenRouter-specific headers."""
        headers = self.config.headers.copy()
        
        # Add authentication header
        headers[self.config.auth_header] = self.config.auth_format.format(api_key=self.api_key)
        
        # OpenRouter-specific headers
        headers["HTTP-Referer"] = headers.get("HTTP-Referer", "https://github.com/yourusername/code-chat-ai")
        headers["X-Title"] = headers.get("X-Title", "Code Chat with AI")
        
        return headers
    
    def _prepare_request_data(self, messages: List[Dict], model: str) -> Dict[str, Any]:
        """Prepare OpenRouter-specific request data."""
        # Base OpenAI-compatible format
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 10000,
            "temperature": 0.1,
            "stream": False  # Ensure no streaming for OpenRouter
        }
        
        # OpenRouter-specific parameters can be added here:
        # data["top_p"] = 1.0
        # data["frequency_penalty"] = 0.0
        # data["presence_penalty"] = 0.0
        # data["route"] = "fallback"  # OpenRouter routing options
        
        return data
    
    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """Extract response content from OpenRouter response."""
        try:
            # Standard OpenAI format path
            content = response_data["choices"][0]["message"]["content"]
            
            # OpenRouter might include model info or routing details
            if "model" in response_data:
                actual_model = response_data.get("model", "unknown")
                # Could log or use this info if needed in the future
            
            return content
            
        except (KeyError, IndexError, TypeError) as e:
            raise Exception(f"Failed to extract OpenRouter response content: {str(e)}")
    
    def _extract_token_usage(self, response_data: Dict[str, Any]) -> Tuple[int, int, int]:
        """Extract token usage information from OpenRouter response."""
        try:
            usage = response_data.get("usage", {})
            
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # OpenRouter might have additional billing info
            if "cost" in usage:
                # Could store cost information if needed in the future
                pass
            
            # If total not provided, calculate
            if total_tokens == 0:
                total_tokens = prompt_tokens + completion_tokens
            
            return prompt_tokens, completion_tokens, total_tokens
            
        except (KeyError, IndexError, TypeError):
            return 0, 0, 0
    
    def _handle_api_error(self, status_code: int, response_text: str) -> str:
        """Handle OpenRouter-specific API errors."""
        if status_code == 401:
            return "OpenRouter API key is invalid or expired"
        elif status_code == 429:
            return "OpenRouter rate limit exceeded. Please try again later"
        elif status_code == 502:
            return "OpenRouter service temporarily unavailable"
        else:
            return f"OpenRouter API request failed: {status_code} - {response_text}"
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get OpenRouter-specific debug information."""
        base_info = self.get_provider_info()
        
        openrouter_info = {
            "openrouter_headers": ["HTTP-Referer", "X-Title"],
            "streaming_disabled": True,
            "routing_enabled": True,
            "supports_fallback": True,
            "model_routing": "automatic"
        }
        
        base_info.update(openrouter_info)
        return base_info