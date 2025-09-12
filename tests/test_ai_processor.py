"""
Unit tests for the AI processor and provider system.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from ai import AIProcessor, AIProviderFactory
from base_ai import BaseAIProvider, AIProviderConfig
from openrouter_provider import OpenRouterProvider
from tachyon_provider import TachyonProvider


class TestAIProviderFactory:
    """Test cases for AIProviderFactory."""
    
    def test_get_available_providers(self):
        """Test getting list of available providers."""
        providers = AIProviderFactory.get_available_providers()
        assert "openrouter" in providers
        assert "tachyon" in providers
        assert len(providers) >= 2
    
    def test_create_provider_openrouter(self):
        """Test creating OpenRouter provider."""
        provider = AIProviderFactory.create_provider("openrouter", "test-key")
        assert isinstance(provider, OpenRouterProvider)
        assert provider.api_key == "test-key"
    
    def test_create_provider_tachyon(self):
        """Test creating Tachyon provider."""
        provider = AIProviderFactory.create_provider("tachyon", "test-key")
        assert isinstance(provider, TachyonProvider)
        assert provider.api_key == "test-key"
    
    def test_create_provider_invalid(self):
        """Test creating provider with invalid name."""
        with pytest.raises(ValueError) as exc_info:
            AIProviderFactory.create_provider("invalid_provider", "test-key")
        assert "Unsupported provider 'invalid_provider'" in str(exc_info.value)
    
    def test_register_provider(self):
        """Test registering a new provider."""
        class TestProvider(BaseAIProvider):
            def _get_provider_config(self):
                return AIProviderConfig("test", "http://test.com")
            def _prepare_headers(self):
                return {}
            def _prepare_request_data(self, messages, model):
                return {}
            def _extract_response_content(self, response_data):
                return "test"
            def _extract_token_usage(self, response_data):
                return 0, 0, 0
            def _handle_api_error(self, status_code, response_text):
                return "error"
        
        AIProviderFactory.register_provider("test", TestProvider)
        
        # Should now be able to create the test provider
        provider = AIProviderFactory.create_provider("test", "key")
        assert isinstance(provider, TestProvider)
        
        # Clean up
        del AIProviderFactory.PROVIDERS["test"]
    
    def test_register_provider_invalid_class(self):
        """Test registering provider with invalid class."""
        class InvalidProvider:
            pass
        
        with pytest.raises(ValueError) as exc_info:
            AIProviderFactory.register_provider("invalid", InvalidProvider)
        assert "Provider class must extend BaseAIProvider" in str(exc_info.value)


class TestAIProcessor:
    """Test cases for AIProcessor."""
    
    def test_init_default(self):
        """Test AIProcessor initialization with defaults."""
        processor = AIProcessor("test-key", "openrouter")
        assert processor.api_key == "test-key"
        assert processor.provider == "openrouter"
        assert isinstance(processor._provider, OpenRouterProvider)
    
    def test_set_api_key(self):
        """Test setting API key."""
        processor = AIProcessor("", "openrouter")
        processor.set_api_key("new-key")
        assert processor.api_key == "new-key"
        assert processor._provider.api_key == "new-key"
    
    def test_set_provider(self):
        """Test switching providers."""
        processor = AIProcessor("test-key", "openrouter")
        processor.set_provider("tachyon")
        
        assert processor.provider == "tachyon"
        assert isinstance(processor._provider, TachyonProvider)
        assert processor.api_key == "test-key"  # Should preserve API key
    
    def test_validate_api_key_valid(self):
        """Test API key validation with valid key."""
        processor = AIProcessor("test-key", "openrouter")
        assert processor.validate_api_key() is True
    
    def test_validate_api_key_empty(self):
        """Test API key validation with empty key."""
        processor = AIProcessor("", "openrouter")
        assert processor.validate_api_key() is False
    
    def test_get_provider_info(self):
        """Test getting provider information."""
        processor = AIProcessor("test-key", "openrouter")
        info = processor.get_provider_info()
        
        assert info["name"] == "openrouter"
        assert info["has_api_key"] is True
        assert "api_url" in info
        assert "supports_tokens" in info
    
    def test_get_provider_info_different_provider(self):
        """Test getting information for different provider."""
        processor = AIProcessor("test-key", "openrouter")
        info = processor.get_provider_info("tachyon")
        
        assert info["name"] == "tachyon"
    
    def test_create_system_message(self):
        """Test creating system message."""
        processor = AIProcessor("test-key", "openrouter")
        
        with patch('ai.system_message_manager') as mock_manager:
            mock_manager.get_system_message.return_value = "Test system message"
            
            message = processor.create_system_message("codebase content")
            
            assert message["role"] == "system"
            assert message["content"] == "Test system message"
            mock_manager.get_system_message.assert_called_once_with("codebase content")


class TestOpenRouterProvider:
    """Test cases for OpenRouterProvider."""
    
    def test_init(self):
        """Test OpenRouter provider initialization."""
        provider = OpenRouterProvider("test-key")
        assert provider.api_key == "test-key"
        assert provider.config.name == "openrouter"
        assert provider.config.supports_tokens is True
        assert "openrouter.ai" in provider.config.api_url
    
    def test_prepare_headers(self):
        """Test preparing OpenRouter-specific headers."""
        provider = OpenRouterProvider("test-key")
        headers = provider._prepare_headers()
        
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers
    
    def test_prepare_request_data(self):
        """Test preparing OpenRouter request data."""
        provider = OpenRouterProvider("test-key")
        messages = [{"role": "user", "content": "test message"}]
        
        data = provider._prepare_request_data(messages, "gpt-3.5-turbo")
        
        assert data["model"] == "gpt-3.5-turbo"
        assert data["messages"] == messages
        assert data["stream"] is False
        assert "max_tokens" in data
        assert "temperature" in data
    
    def test_extract_response_content_success(self):
        """Test extracting response content successfully."""
        provider = OpenRouterProvider("test-key")
        response_data = {
            "choices": [
                {"message": {"content": "Test response content"}}
            ]
        }
        
        content = provider._extract_response_content(response_data)
        assert content == "Test response content"
    
    def test_extract_response_content_error(self):
        """Test extracting response content with malformed response."""
        provider = OpenRouterProvider("test-key")
        response_data = {"invalid": "response"}
        
        with pytest.raises(Exception) as exc_info:
            provider._extract_response_content(response_data)
        assert "Failed to extract OpenRouter response content" in str(exc_info.value)
    
    def test_extract_token_usage_success(self):
        """Test extracting token usage successfully."""
        provider = OpenRouterProvider("test-key")
        response_data = {
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "total_tokens": 75
            }
        }
        
        prompt, completion, total = provider._extract_token_usage(response_data)
        assert prompt == 50
        assert completion == 25
        assert total == 75
    
    def test_extract_token_usage_missing(self):
        """Test extracting token usage with missing usage data."""
        provider = OpenRouterProvider("test-key")
        response_data = {}
        
        prompt, completion, total = provider._extract_token_usage(response_data)
        assert prompt == 0
        assert completion == 0
        assert total == 0
    
    def test_handle_api_error_401(self):
        """Test handling 401 API error."""
        provider = OpenRouterProvider("test-key")
        error_msg = provider._handle_api_error(401, "Unauthorized")
        assert "invalid or expired" in error_msg
    
    def test_handle_api_error_429(self):
        """Test handling 429 rate limit error."""
        provider = OpenRouterProvider("test-key")
        error_msg = provider._handle_api_error(429, "Rate limited")
        assert "rate limit exceeded" in error_msg
    
    def test_handle_api_error_generic(self):
        """Test handling generic API error."""
        provider = OpenRouterProvider("test-key")
        error_msg = provider._handle_api_error(500, "Internal server error")
        assert "500" in error_msg
        assert "Internal server error" in error_msg


class TestTachyonProvider:
    """Test cases for TachyonProvider."""
    
    def test_init(self):
        """Test Tachyon provider initialization."""
        provider = TachyonProvider("test-key")
        assert provider.api_key == "test-key"
        assert provider.config.name == "tachyon"
        assert provider.config.supports_tokens is True
    
    def test_prepare_headers(self):
        """Test preparing Tachyon-specific headers."""
        provider = TachyonProvider("test-key")
        headers = provider._prepare_headers()
        
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "CodeChatAI/1.0"


class TestBaseAIProviderIntegration:
    """Integration tests for BaseAIProvider functionality."""
    
    @patch('requests.post')
    def test_process_question_success(self, mock_post):
        """Test successful question processing."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response"}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
        }
        mock_post.return_value = mock_response
        
        processor = AIProcessor("test-key", "openrouter")
        
        with patch('ai.system_message_manager') as mock_manager:
            mock_manager.get_system_message.return_value = "System message"
            
            result = processor.process_question(
                question="Test question",
                conversation_history=[],
                codebase_content="test code",
                model="gpt-3.5-turbo"
            )
            
            assert result == "AI response"
            mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_process_question_api_error(self, mock_post):
        """Test question processing with API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        processor = AIProcessor("test-key", "openrouter")
        
        with pytest.raises(Exception) as exc_info:
            processor.process_question(
                question="Test question",
                conversation_history=[],
                codebase_content="test code",
                model="gpt-3.5-turbo"
            )
        
        assert "invalid or expired" in str(exc_info.value)
    
    @patch('requests.post')
    def test_process_question_connection_error(self, mock_post):
        """Test question processing with connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        processor = AIProcessor("test-key", "openrouter")
        
        with pytest.raises(Exception) as exc_info:
            processor.process_question(
                question="Test question",
                conversation_history=[],
                codebase_content="test code",
                model="gpt-3.5-turbo"
            )
        
        assert "Connection error" in str(exc_info.value)
    
    def test_process_question_no_api_key(self):
        """Test question processing without API key."""
        processor = AIProcessor("", "openrouter")
        
        with pytest.raises(Exception) as exc_info:
            processor.process_question(
                question="Test question",
                conversation_history=[],
                codebase_content="test code",
                model="gpt-3.5-turbo"
            )
        
        assert "API key is not configured" in str(exc_info.value)