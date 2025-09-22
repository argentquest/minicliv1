"""
Custom AI Provider Implementation

This module implements a customizable AI provider for the Code Chat application.
It can be configured to work with various AI APIs by modifying the configuration
parameters. This provider serves as a template for integrating new AI services.

Key Features:
- Highly configurable API endpoints and headers
- Flexible request/response format handling
- Customizable authentication methods
- Extensible error handling
- Debug information for troubleshooting

Configuration Options:
- API URL: Customizable endpoint URL
- Authentication: Bearer token, API key, or custom headers
- Request format: JSON, form data, or custom formats
- Response parsing: Flexible JSON path extraction
- Token usage: Configurable token counting
- Error handling: Custom error message mapping

Usage:
    provider = CustomProvider(api_key="your_api_key")
    # Configure the provider for your specific API
    provider.configure_api(
        api_url="https://your-api.com/v1/chat",
        auth_header="X-API-Key",
        auth_format="{api_key}"
    )

Error Handling:
- Configurable error codes and messages
- Network error handling with retries
- API-specific error format parsing

This provider is designed to be easily extended and customized for different
AI services while maintaining compatibility with the BaseAIProvider interface.
"""
import os
from typing import Dict, Any, List, Tuple
from common.base_ai import BaseAIProvider, AIProviderConfig


class CustomProvider(BaseAIProvider):
    """Customizable AI provider implementation."""

    def __init__(self, api_key: str = ""):
        # Use the same configuration as OpenRouter provider
        import os
        self.custom_config = {
            "api_url": os.getenv("API_URL", "https://openrouter.ai/api/v1/chat/completions"),
            "auth_header": "Authorization",
            "auth_format": "Bearer {api_key}",
            "model_param": "model",
            "messages_param": "messages",
            "max_tokens_param": "max_tokens",
            "temperature_param": "temperature",
            "stream_param": "stream",
            "response_content_path": ["choices", 0, "message", "content"],
            "response_usage_path": "usage",
            "supports_tokens": True,
            "custom_headers": {
                "HTTP-Referer": "https://github.com/yourusername/code-chat-ai",
                "X-Title": "Code Chat with AI"
            },
            "request_timeout": 30
        }
        super().__init__(api_key)

    def configure_api(self,
                     api_url: str = None,
                     auth_header: str = None,
                     auth_format: str = None,
                     **kwargs):
        """Configure the API parameters for this custom provider."""
        if api_url:
            self.custom_config["api_url"] = api_url
        if auth_header:
            self.custom_config["auth_header"] = auth_header
        if auth_format:
            self.custom_config["auth_format"] = auth_format

        # Update any additional configuration
        self.custom_config.update(kwargs)

        # Re-initialize config to apply changes
        self.config = self._get_provider_config()

    def _get_provider_config(self) -> AIProviderConfig:
        """Get custom provider configuration."""
        config = AIProviderConfig(
            name="custom",
            api_url=self.custom_config["api_url"],
            supports_tokens=self.custom_config["supports_tokens"]
        )

        # Set custom authentication
        config.auth_header = self.custom_config["auth_header"]
        config.auth_format = self.custom_config["auth_format"]

        # Add custom headers
        config.headers.update(self.custom_config["custom_headers"])

        return config

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare custom headers."""
        headers = self.config.headers.copy()

        # Add authentication header
        headers[self.config.auth_header] = self.config.auth_format.format(api_key=self.api_key)

        return headers

    def _prepare_request_data(self, messages: List[Dict], model: str) -> Dict[str, Any]:
        """Prepare custom request data."""
        data = {
            self.custom_config["model_param"]: model,
            self.custom_config["messages_param"]: messages,
            self.custom_config["max_tokens_param"]: 10000,
            self.custom_config["temperature_param"]: 0.1,
            self.custom_config["stream_param"]: False
        }

        return data

    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """Extract response content using configurable path."""
        try:
            content = response_data
            for key in self.custom_config["response_content_path"]:
                if isinstance(key, str):
                    content = content[key]
                elif isinstance(key, int):
                    content = content[key]

            return str(content)

        except (KeyError, IndexError, TypeError) as e:
            raise Exception(f"Failed to extract custom provider response content: {str(e)}")

    def _extract_token_usage(self, response_data: Dict[str, Any]) -> Tuple[int, int, int]:
        """Extract token usage information."""
        try:
            usage_path = self.custom_config["response_usage_path"]
            if isinstance(usage_path, str):
                usage = response_data.get(usage_path, {})
            else:
                usage = response_data
                for key in usage_path:
                    usage = usage[key]

            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # If total not provided, calculate
            if total_tokens == 0:
                total_tokens = prompt_tokens + completion_tokens

            return prompt_tokens, completion_tokens, total_tokens

        except (KeyError, IndexError, TypeError):
            return 0, 0, 0

    def _handle_api_error(self, status_code: int, response_text: str) -> str:
        """Handle custom API errors."""
        error_messages = {
            400: "Bad request - check your parameters",
            401: "Authentication failed - check your API key",
            403: "Access forbidden - check your permissions",
            404: "API endpoint not found",
            429: "Rate limit exceeded - please try again later",
            500: "Internal server error",
            502: "Bad gateway - service temporarily unavailable",
            503: "Service unavailable",
            504: "Gateway timeout"
        }

        if status_code in error_messages:
            return f"Custom API error ({status_code}): {error_messages[status_code]}"
        else:
            return f"Custom API request failed: {status_code} - {response_text}"

    def get_debug_info(self) -> Dict[str, Any]:
        """Get custom provider debug information."""
        base_info = self.get_provider_info()

        custom_info = {
            "custom_config": self.custom_config.copy(),
            "configured_api_url": self.custom_config["api_url"],
            "auth_method": self.custom_config["auth_header"],
            "response_content_path": self.custom_config["response_content_path"],
            "supports_custom_configuration": True,
            "configurable": True
        }

        base_info.update(custom_info)
        return base_info

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the configured API endpoint."""
        import requests
        from datetime import datetime

        test_result = {
            "timestamp": datetime.now().isoformat(),
            "api_url": self.custom_config["api_url"],
            "connection_successful": False,
            "response_time_ms": None,
            "status_code": None,
            "error_message": None
        }

        try:
            headers = self._prepare_headers()
            start_time = datetime.now()

            # Make a simple test request (you might need to adjust this based on the API)
            verify_ssl = os.getenv('VALIDATE_SSL', 'true').lower() == 'true'
            response = requests.get(
                self.custom_config["api_url"].replace("/chat/completions", "/models"),
                headers=headers,
                timeout=self.custom_config["request_timeout"],
                verify=verify_ssl
            )

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000

            test_result.update({
                "connection_successful": response.status_code == 200,
                "response_time_ms": round(response_time, 2),
                "status_code": response.status_code
            })

        except requests.exceptions.RequestException as e:
            test_result["error_message"] = str(e)
        except Exception as e:
            test_result["error_message"] = f"Unexpected error: {str(e)}"

        return test_result