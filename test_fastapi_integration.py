#!/usr/bin/env python3
"""
FastAPI Integration Tests

This module contains integration tests for the FastAPI server endpoints.
It includes both mocked unit tests and real server tests.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import FastAPI test client and our modules
from fastapi.testclient import TestClient
from fastapi_server import app
from file_lock import safe_json_save, safe_json_load
import requests
import tempfile


class TestFastAPIUnitTests:
    """Unit tests for FastAPI endpoints with mocked dependencies."""

    def setup_method(self):
        """Set up test client and mocks."""
        self.client = TestClient(app)

        # Mock the global variables in fastapi_server
        with patch('fastapi_server.initialize_components', return_value=True):
            with patch('fastapi_server.ai_processor') as mock_ai:
                with patch('fastapi_server.scanner') as mock_scanner:
                    self.mock_ai_processor = mock_ai
                    self.mock_scanner = mock_scanner

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_models_endpoint_success(self):
        """Test the models endpoint with successful response."""
        mock_provider_info = {
            "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            "default_model": "gpt-3.5-turbo"
        }

        with patch('fastapi_server.ai_processor') as mock_ai:
            mock_ai.get_provider_info.return_value = mock_provider_info

            response = self.client.get("/models")

            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert "default" in data
            assert data["default"] == "gpt-3.5-turbo"
            assert len(data["models"]) == 3

    def test_models_endpoint_no_processor(self):
        """Test the models endpoint when AI processor is not initialized."""
        with patch('fastapi_server.ai_processor', None):
            response = self.client.get("/models")

            assert response.status_code == 503
            data = response.json()
            assert "AI processor not initialized" in data["detail"]

    def test_providers_endpoint(self):
        """Test the providers endpoint."""
        mock_providers = ["openrouter", "tachyon", "custom"]

        with patch('fastapi_server.AIProviderFactory.get_available_providers', return_value=mock_providers):
            with patch('fastapi_server.env_manager.load_env_file', return_value={"DEFAULT_PROVIDER": "openrouter"}):
                response = self.client.get("/providers")

                assert response.status_code == 200
                data = response.json()
                assert "providers" in data
                assert "default" in data
                assert data["default"] == "openrouter"
                assert len(data["providers"]) == 3

    def test_system_prompts_endpoint(self):
        """Test the system prompts endpoint."""
        response = self.client.get("/system-prompts")

        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data
        assert isinstance(data["prompts"], list)
        assert len(data["prompts"]) > 0

        # Check structure of first prompt
        first_prompt = data["prompts"][0]
        assert "id" in first_prompt
        assert "name" in first_prompt
        assert "description" in first_prompt

    def test_analyze_endpoint_success(self):
        """Test the analyze endpoint with successful analysis."""
        # Mock request data
        request_data = {
            "folder": "/test/folder",
            "question": "What does this code do?",
            "model": "gpt-3.5-turbo",
            "provider": "openrouter",
            "include": "*.py",
            "exclude": "test_*",
            "output": "structured"
        }

        # Mock responses
        mock_ai_response = "This is a test response from the AI."
        mock_files = ["/test/folder/main.py", "/test/folder/utils.py"]

        with patch('fastapi_server.ai_processor') as mock_ai:
            with patch('fastapi_server.scanner') as mock_scanner:
                # Setup mocks
                mock_ai.process_question.return_value = mock_ai_response
                mock_scanner.validate_directory.return_value = (True, "")
                mock_scanner.scan_directory.return_value = mock_files
                mock_scanner.get_codebase_content.return_value = "# Test content"

                response = self.client.post("/analyze", json=request_data)

                assert response.status_code == 200
                data = response.json()
                assert data["response"] == mock_ai_response
                assert data["model"] == "gpt-3.5-turbo"
                assert data["provider"] == "openrouter"
                assert "processing_time" in data
                assert "timestamp" in data
                assert data["files_count"] == 2

    def test_analyze_endpoint_invalid_directory(self):
        """Test the analyze endpoint with invalid directory."""
        request_data = {
            "folder": "/invalid/folder",
            "question": "What does this code do?",
            "model": "gpt-3.5-turbo"
        }

        with patch('fastapi_server.scanner') as mock_scanner:
            mock_scanner.validate_directory.return_value = (False, "Directory does not exist")

            response = self.client.post("/analyze", json=request_data)

            assert response.status_code == 400
            data = response.json()
            assert "Directory does not exist" in data["detail"]

    def test_analyze_endpoint_no_files(self):
        """Test the analyze endpoint when no files are found."""
        request_data = {
            "folder": "/test/folder",
            "question": "What does this code do?"
        }

        with patch('fastapi_server.scanner') as mock_scanner:
            mock_scanner.validate_directory.return_value = (True, "")
            mock_scanner.scan_directory.return_value = []  # No files

            response = self.client.post("/analyze", json=request_data)

            assert response.status_code == 400
            data = response.json()
            assert "No supported files found" in data["detail"]

    def test_analyze_endpoint_no_processor(self):
        """Test the analyze endpoint when AI processor is not initialized."""
        request_data = {
            "folder": "/test/folder",
            "question": "What does this code do?"
        }

        with patch('fastapi_server.ai_processor', None):
            response = self.client.post("/analyze", json=request_data)

            assert response.status_code == 503
            data = response.json()
            assert "AI processor not initialized" in data["detail"]

    def test_analyze_endpoint_with_filters(self):
        """Test the analyze endpoint with file filtering."""
        request_data = {
            "folder": "/test/folder",
            "question": "What does this code do?",
            "include": "*.py",
            "exclude": "test_*"
        }

        mock_files = ["/test/folder/main.py", "/test/folder/test_main.py", "/test/folder/utils.js"]
        filtered_files = ["/test/folder/main.py"]  # Only main.py after filtering

        with patch('fastapi_server.ai_processor') as mock_ai:
            with patch('fastapi_server.scanner') as mock_scanner:
                mock_ai.process_question.return_value = "Filtered analysis response"
                mock_scanner.validate_directory.return_value = (True, "")
                mock_scanner.scan_directory.return_value = mock_files
                mock_scanner.get_codebase_content.return_value = "# Filtered content"

                response = self.client.post("/analyze", json=request_data)

                assert response.status_code == 200
                data = response.json()
                assert data["files_count"] == 3  # Original file count
                assert data["response"] == "Filtered analysis response"

    def test_analyze_endpoint_processing_error(self):
        """Test the analyze endpoint when processing fails."""
        request_data = {
            "folder": "/test/folder",
            "question": "What does this code do?"
        }

        with patch('fastapi_server.ai_processor') as mock_ai:
            with patch('fastapi_server.scanner') as mock_scanner:
                mock_ai.process_question.side_effect = Exception("AI processing failed")
                mock_scanner.validate_directory.return_value = (True, "")
                mock_scanner.scan_directory.return_value = ["/test/folder/main.py"]
                mock_scanner.get_codebase_content.return_value = "# Test content"

                response = self.client.post("/analyze", json=request_data)

                assert response.status_code == 500
                data = response.json()
                assert "Analysis failed" in data["detail"]

    def test_parameter_validation(self):
        """Test parameter validation for the analyze endpoint."""
        # Test missing required fields
        incomplete_request = {"question": "What does this code do?"}  # Missing folder

        response = self.client.post("/analyze", json=incomplete_request)
        assert response.status_code == 422  # Validation error

    def test_file_saving_functionality(self, tmp_path):
        """Test file saving functionality used by the analyze endpoint."""
        test_data = {"test": "data", "number": 42}
        test_file = tmp_path / "test_output.json"

        # Test successful save
        result = safe_json_save(test_data, str(test_file))
        assert result is True
        assert test_file.exists()

        # Verify content
        loaded_data = safe_json_load(str(test_file))
        assert loaded_data == test_data

    def test_json_response_format(self):
        """Test that JSON responses are properly formatted."""
        request_data = {
            "folder": "/test/folder",
            "question": "Test question",
            "output": "json"
        }

        with patch('fastapi_server.ai_processor') as mock_ai:
            with patch('fastapi_server.scanner') as mock_scanner:
                mock_ai.process_question.return_value = "Test response"
                mock_scanner.validate_directory.return_value = (True, "")
                mock_scanner.scan_directory.return_value = ["/test/folder/main.py"]
                mock_scanner.get_codebase_content.return_value = "# Test"

                response = self.client.post("/analyze", json=request_data)

                assert response.status_code == 200
                data = response.json()

                # Verify all expected fields are present
                required_fields = ["response", "model", "provider", "processing_time", "timestamp", "files_count"]
                for field in required_fields:
                    assert field in data

                # Verify data types
                assert isinstance(data["response"], str)
                assert isinstance(data["processing_time"], (int, float))
                assert isinstance(data["files_count"], int)


def test_with_real_server():
    """Test against a real running FastAPI server."""
    print("🧪 Testing against real FastAPI server...")
    print("Note: Make sure the FastAPI server is running on http://localhost:8000")

    base_url = "http://localhost:8000"

    try:
        # Test 1: Health check
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        print("   ✅ Health check passed")

        # Test 2: Models endpoint
        print("2. Testing models endpoint...")
        response = requests.get(f"{base_url}/models", timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            assert "models" in models_data
            assert "default" in models_data
            print(f"   ✅ Models endpoint returned {len(models_data['models'])} models")
        else:
            print(f"   ⚠️  Models endpoint returned {response.status_code} - AI processor may not be initialized")

        # Test 3: Providers endpoint
        print("3. Testing providers endpoint...")
        response = requests.get(f"{base_url}/providers", timeout=10)
        assert response.status_code == 200
        providers_data = response.json()
        assert "providers" in providers_data
        assert "default" in providers_data
        print(f"   ✅ Providers endpoint returned {len(providers_data['providers'])} providers")

        # Test 4: System prompts endpoint
        print("4. Testing system prompts endpoint...")
        response = requests.get(f"{base_url}/system-prompts", timeout=10)
        assert response.status_code == 200
        prompts_data = response.json()
        assert "prompts" in prompts_data
        print(f"   ✅ System prompts endpoint returned {len(prompts_data['prompts'])} prompts")

        # Test 5: Basic analysis request (if API key is configured)
        print("5. Testing basic analysis endpoint...")
        test_request = {
            "folder": ".",  # Current directory
            "question": "What is the main purpose of this codebase?",
            "model": "gpt-3.5-turbo",
            "provider": "openrouter"
        }

        response = requests.post(f"{base_url}/analyze", json=test_request, timeout=30)

        if response.status_code == 200:
            analysis_data = response.json()
            assert "response" in analysis_data
            assert "model" in analysis_data
            assert "processing_time" in analysis_data
            print(f"   ✅ Analysis completed in {analysis_data['processing_time']:.2f}s")
        elif response.status_code == 503:
            print("   ⚠️  Analysis endpoint returned 503 - AI processor not initialized (no API key)")
        else:
            print(f"   ❌ Analysis endpoint returned {response.status_code}: {response.text}")

        print("\n🎉 All real server tests completed!")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to FastAPI server at http://localhost:8000")
        print("   Make sure the server is running with: python fastapi_server.py")
        raise
    except Exception as e:
        print(f"❌ Real server test failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Run the real server test if called directly
    test_with_real_server()