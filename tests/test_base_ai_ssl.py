"""
Unit tests for SSL verification in BaseAIProvider.
Tests that the VALIDATE_SSL environment variable controls SSL verification in API calls.
"""

import os
import pytest
from unittest.mock import patch, Mock
from common.base_ai import BaseAIProvider, AIProviderConfig


class MockProvider(BaseAIProvider):
    """Minimal mock provider for testing BaseAIProvider functionality."""

    def _get_provider_config(self) -> AIProviderConfig:
        return AIProviderConfig(name="mock", api_url="https://mock.api", supports_tokens=True)

    def _prepare_headers(self) -> dict:
        return {"Content-Type": "application/json"}

    def _prepare_request_data(self, messages, model) -> dict:
        return {"model": model, "messages": messages}

    def _extract_response_content(self, response_data) -> str:
        return "mock response"

    def _extract_token_usage(self, response_data) -> tuple:
        return 0, 0, 0

    def _handle_api_error(self, status_code, response_text) -> str:
        return f"Mock error: {status_code}"


@pytest.fixture
def mock_provider():
    return MockProvider(api_key="mock_key")


def test_ssl_validation_true(mock_provider):
    """Test that VALIDATE_SSL=true uses verify=True in requests.post."""
    with patch.dict(os.environ, {"VALIDATE_SSL": "true"}), \
         patch("requests.post") as mock_post:

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
        mock_post.return_value = mock_response

        mock_provider.process_question("test question", [], "", "mock_model")

        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        assert call_args["verify"] is True


def test_ssl_validation_false(mock_provider):
    """Test that VALIDATE_SSL=false uses verify=False in requests.post."""
    with patch.dict(os.environ, {"VALIDATE_SSL": "false"}), \
         patch("requests.post") as mock_post:

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
        mock_post.return_value = mock_response

        mock_provider.process_question("test question", [], "", "mock_model")

        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        assert call_args["verify"] is False


def test_ssl_validation_default_true(mock_provider):
    """Test that default (no VALIDATE_SSL) uses verify=True."""
    with patch.dict(os.environ, clear=True), \
         patch("requests.post") as mock_post:

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
        mock_post.return_value = mock_response

        mock_provider.process_question("test question", [], "", "mock_model")

        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        assert call_args["verify"] is True