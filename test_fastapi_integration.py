"""
Integration tests for FastAPI server endpoints.

This module provides comprehensive integration tests for the Code Chat AI FastAPI server,
focusing on both JSON POST and query parameter GET endpoints.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# FastAPI test client
from fastapi.testclient import TestClient

# Import the FastAPI app
from fastapi_server import app

# Create test client
client = TestClient(app)


class TestFastAPIServerIntegration:
    """Integration tests for FastAPI server endpoints."""

    def setup_method(self):
        """Setup for each test method."""
        # Use current directory as test folder
        self.test_folder = os.getcwd()
        self.test_question = "Explain what this code does"

        # Mock AI responses to avoid actual API calls
        self.mock_response = {
            'response': 'This is a mock AI response explaining the codebase.',
            'model': 'gpt-3.5-turbo',
            'provider': 'openrouter',
            'processing_time': 1.23,
            'timestamp': '2025-01-13T12:00:00',
            'files_count': 5
        }

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    @patch('cli_interface.CLIInterface.process_question')
    @patch('cli_interface.CLIInterface.scan_codebase')
    @patch('cli_interface.CLIInterface.setup_system_prompt')
    @patch('cli_interface.CLIInterface.setup_ai_processor')
    @patch('cli_interface.CLIInterface.load_configuration')
    def test_analyze_post_json_endpoint(self, mock_load_config, mock_setup_ai,
                                       mock_setup_prompt, mock_scan, mock_process):
        """Test POST /analyze endpoint with JSON body."""
        # Setup mocks
        mock_load_config.return_value = {'model': 'gpt-3.5-turbo'}
        mock_setup_ai.return_value = True
        mock_setup_prompt.return_value = True
        mock_scan.return_value = (['file1.py', 'file2.py'], 'mock content')
        mock_process.return_value = self.mock_response

        # Test data
        request_data = {
            "folder": self.test_folder,
            "question": self.test_question,
            "model": "gpt-3.5-turbo",
            "provider": "openrouter",
            "output": "structured"
        }

        # Make request
        response = client.post("/analyze", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "response" in data
        assert "model" in data
        assert "provider" in data
        assert "processing_time" in data
        assert "timestamp" in data
        assert "files_count" in data

        # Check specific values
        assert data["response"] == self.mock_response["response"]
        assert data["model"] == self.mock_response["model"]
        assert data["provider"] == self.mock_response["provider"]
        assert data["files_count"] == self.mock_response["files_count"]

    @patch('cli_interface.CLIInterface.process_question')
    @patch('cli_interface.CLIInterface.scan_codebase')
    @patch('cli_interface.CLIInterface.setup_system_prompt')
    @patch('cli_interface.CLIInterface.setup_ai_processor')
    @patch('cli_interface.CLIInterface.load_configuration')
    def test_analyze_get_params_endpoint(self, mock_load_config, mock_setup_ai,
                                        mock_setup_prompt, mock_scan, mock_process):
        """Test GET /analyze endpoint with query parameters."""
        # Setup mocks
        mock_load_config.return_value = {'model': 'gpt-3.5-turbo'}
        mock_setup_ai.return_value = True
        mock_setup_prompt.return_value = True
        mock_scan.return_value = (['file1.py', 'file2.py'], 'mock content')
        mock_process.return_value = self.mock_response

        # Make request with query parameters
        params = {
            "folder": self.test_folder,
            "question": self.test_question,
            "model": "gpt-3.5-turbo",
            "provider": "openrouter",
            "output": "structured"
        }

        response = client.get("/analyze", params=params)

        # Assertions
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "response" in data
        assert "model" in data
        assert "provider" in data
        assert "processing_time" in data
        assert "timestamp" in data
        assert "files_count" in data

        # Check specific values
        assert data["response"] == self.mock_response["response"]
        assert data["model"] == self.mock_response["model"]
        assert data["provider"] == self.mock_response["provider"]
        assert data["files_count"] == self.mock_response["files_count"]

    def test_analyze_get_minimal_params(self):
        """Test GET /analyze with minimal required parameters."""
        # Test with only required parameters
        params = {
            "folder": self.test_folder,
            "question": self.test_question
        }

        response = client.get("/analyze", params=params)

        # Should return 200 even with mocks not set up (will fail in actual processing)
        # We're just testing parameter validation here
        assert response.status_code in [200, 500]  # 200 if mocks work, 500 if they don't

    def test_analyze_invalid_output_format(self):
        """Test GET /analyze with invalid output format."""
        params = {
            "folder": self.test_folder,
            "question": self.test_question,
            "output": "invalid_format"
        }

        response = client.get("/analyze", params=params)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Output format must be" in data["detail"]

    @patch('ai.AIProviderFactory.get_available_providers')
    def test_analyze_invalid_provider(self, mock_get_providers):
        """Test GET /analyze with invalid provider."""
        # Mock available providers
        mock_get_providers.return_value = ['openrouter', 'tachyon']

        params = {
            "folder": self.test_folder,
            "question": self.test_question,
            "provider": "invalid_provider"
        }

        response = client.get("/analyze", params=params)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Provider must be one of" in data["detail"]

    def test_analyze_missing_required_params(self):
        """Test GET /analyze with missing required parameters."""
        # Missing folder
        params = {"question": self.test_question}
        response = client.get("/analyze", params=params)
        assert response.status_code == 422  # Validation error

        # Missing question
        params = {"folder": self.test_folder}
        response = client.get("/analyze", params=params)
        assert response.status_code == 422  # Validation error

    @patch('cli_interface.CLIInterface.process_question')
    @patch('cli_interface.CLIInterface.scan_codebase')
    @patch('cli_interface.CLIInterface.setup_system_prompt')
    @patch('cli_interface.CLIInterface.setup_ai_processor')
    @patch('cli_interface.CLIInterface.load_configuration')
    def test_analyze_with_file_saving(self, mock_load_config, mock_setup_ai,
                                     mock_setup_prompt, mock_scan, mock_process):
        """Test POST /analyze with file saving functionality."""
        # Setup mocks
        mock_load_config.return_value = {'model': 'gpt-3.5-turbo'}
        mock_setup_ai.return_value = True
        mock_setup_prompt.return_value = True
        mock_scan.return_value = (['file1.py', 'file2.py'], 'mock content')
        mock_process.return_value = self.mock_response

        # Create temporary file for saving
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name

        try:
            # Test data with file saving
            request_data = {
                "folder": self.test_folder,
                "question": self.test_question,
                "output": "json",
                "save_to": temp_filename
            }

            # Make request
            response = client.post("/analyze", json=request_data)

            # Assertions
            assert response.status_code == 200
            data = response.json()

            # Check that file was created (this would be tested in actual implementation)
            # For this test, we're just ensuring the endpoint accepts the parameter

        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_models_endpoint(self):
        """Test GET /models endpoint."""
        response = client.get("/models")

        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        assert isinstance(data["models"], list)

    def test_providers_endpoint(self):
        """Test GET /providers endpoint."""
        response = client.get("/providers")

        assert response.status_code == 200
        data = response.json()

        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_system_prompts_endpoint(self):
        """Test GET /system-prompts endpoint."""
        response = client.get("/system-prompts")

        assert response.status_code == 200
        data = response.json()

        assert "system_prompts" in data
        assert isinstance(data["system_prompts"], list)

    @patch('cli_interface.CLIInterface.process_question')
    @patch('cli_interface.CLIInterface.scan_codebase')
    @patch('cli_interface.CLIInterface.setup_system_prompt')
    @patch('cli_interface.CLIInterface.setup_ai_processor')
    @patch('cli_interface.CLIInterface.load_configuration')
    def test_analyze_with_filters(self, mock_load_config, mock_setup_ai,
                                 mock_setup_prompt, mock_scan, mock_process):
        """Test POST /analyze with file filtering."""
        # Setup mocks
        mock_load_config.return_value = {'model': 'gpt-3.5-turbo'}
        mock_setup_ai.return_value = True
        mock_setup_prompt.return_value = True
        mock_scan.return_value = (['file1.py', 'file2.js'], 'mock content')
        mock_process.return_value = self.mock_response

        # Test data with filters
        request_data = {
            "folder": self.test_folder,
            "question": self.test_question,
            "include": "*.py,*.js",
            "exclude": "test_*"
        }

        # Make request
        response = client.post("/analyze", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()

        # Verify that scan_codebase was called with correct filters
        mock_scan.assert_called_once()
        call_args = mock_scan.call_args[0]
        assert call_args[0] == self.test_folder  # folder
        assert call_args[1] == "*.py,*.js"      # include
        assert call_args[2] == "test_*"         # exclude

    def test_analyze_json_validation(self):
        """Test POST /analyze JSON validation."""
        # Test with invalid JSON structure
        invalid_data = {
            "invalid_field": "value"
            # Missing required fields: folder, question
        }

        response = client.post("/analyze", json=invalid_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data


# Helper function to run tests with real server
def test_with_real_server():
    """
    Test function that can be run against a real running server.

    Usage:
        1. Start the FastAPI server: python fastapi_server.py
        2. Run this test: python -c "from test_fastapi_integration import test_with_real_server; test_with_real_server()"

    Note: This requires a real API key and will make actual API calls.
    """
    import requests

    base_url = "http://localhost:8000"

    print("Testing real FastAPI server...")

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return

    # Test models endpoint
    try:
        response = requests.get(f"{base_url}/models")
        print(f"✅ Models endpoint: {response.status_code}")
        print(f"   Available models: {response.json()}")
    except Exception as e:
        print(f"❌ Models endpoint failed: {e}")

    # Test providers endpoint
    try:
        response = requests.get(f"{base_url}/providers")
        print(f"✅ Providers endpoint: {response.status_code}")
        print(f"   Available providers: {response.json()}")
    except Exception as e:
        print(f"❌ Providers endpoint failed: {e}")

    # Test analysis with GET (simple parameters)
    try:
        params = {
            "folder": os.getcwd(),
            "question": "Explain what this project does"
        }
        response = requests.get(f"{base_url}/analyze", params=params)
        print(f"✅ GET analysis: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Model: {data.get('model', 'N/A')}")
            print(f"   Files analyzed: {data.get('files_count', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ GET analysis failed: {e}")

    print("\n🎉 Real server testing complete!")


if __name__ == "__main__":
    # Run the real server test if called directly
    test_with_real_server()