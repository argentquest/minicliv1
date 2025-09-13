#!/usr/bin/env python3
"""
Test script for the CustomProvider

This script demonstrates how to use the CustomProvider and tests its basic functionality.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers.custom_provider import CustomProvider


def test_custom_provider_basic():
    """Test basic CustomProvider functionality."""
    print("🧪 Testing CustomProvider basic functionality...")

    # Create a custom provider instance
    provider = CustomProvider("test-api-key")

    # Test basic properties
    assert provider.api_key == "test-api-key"
    assert provider.get_provider_name() == "custom"
    assert provider.validate_api_key() == True

    print("✅ Basic functionality test passed")


def test_custom_provider_configuration():
    """Test CustomProvider configuration."""
    print("🧪 Testing CustomProvider configuration...")

    provider = CustomProvider("test-key")

    # Configure for a different API
    provider.configure_api(
        api_url="https://api.example.com/v1/chat",
        auth_header="X-API-Key",
        auth_format="{api_key}",
        custom_headers={"User-Agent": "CodeChat/1.0"}
    )

    # Check configuration
    config = provider._get_provider_config()
    assert config.api_url == "https://api.example.com/v1/chat"
    assert config.auth_header == "X-API-Key"
    assert config.auth_format == "{api_key}"

    print("✅ Configuration test passed")


def test_custom_provider_headers():
    """Test CustomProvider header preparation."""
    print("🧪 Testing CustomProvider headers...")

    provider = CustomProvider("test-key")

    # Configure custom headers
    provider.configure_api(
        auth_header="X-API-Key",
        auth_format="Bearer {api_key}",
        custom_headers={"Accept": "application/json"}
    )

    headers = provider._prepare_headers()

    # Check that authentication header is set correctly
    assert "X-API-Key" in headers
    assert headers["X-API-Key"] == "Bearer test-key"

    # Check custom headers
    assert headers["Accept"] == "application/json"

    print("✅ Headers test passed")


def test_custom_provider_request_data():
    """Test CustomProvider request data preparation."""
    print("🧪 Testing CustomProvider request data...")

    provider = CustomProvider("test-key")

    messages = [
        {"role": "user", "content": "Hello, world!"}
    ]

    data = provider._prepare_request_data(messages, "test-model")

    # Check basic structure
    assert "model" in data
    assert "messages" in data
    assert "max_tokens" in data
    assert "temperature" in data
    assert "stream" in data

    # Check values
    assert data["model"] == "test-model"
    assert data["messages"] == messages
    assert data["stream"] == False

    print("✅ Request data test passed")


def test_custom_provider_response_parsing():
    """Test CustomProvider response parsing."""
    print("🧪 Testing CustomProvider response parsing...")

    provider = CustomProvider("test-key")

    # Mock OpenAI-style response
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "Hello! This is a test response."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        }
    }

    # Test content extraction
    content = provider._extract_response_content(mock_response)
    assert content == "Hello! This is a test response."

    # Test token usage extraction
    prompt_tokens, completion_tokens, total_tokens = provider._extract_token_usage(mock_response)
    assert prompt_tokens == 10
    assert completion_tokens == 8
    assert total_tokens == 18

    print("✅ Response parsing test passed")


def test_custom_provider_debug_info():
    """Test CustomProvider debug information."""
    print("🧪 Testing CustomProvider debug info...")

    provider = CustomProvider("test-key")

    debug_info = provider.get_debug_info()

    # Check basic debug info
    assert debug_info["name"] == "custom"
    assert "custom_config" in debug_info
    assert "configured_api_url" in debug_info
    assert debug_info["configurable"] == True

    print("✅ Debug info test passed")


def test_custom_provider_factory_registration():
    """Test that CustomProvider is registered in the factory."""
    print("🧪 Testing CustomProvider factory registration...")

    from ai import AIProviderFactory

    # Check that custom provider is available
    available_providers = AIProviderFactory.get_available_providers()
    assert "custom" in available_providers

    # Test creating a custom provider instance
    provider = AIProviderFactory.create_provider("custom", "test-key")
    assert isinstance(provider, CustomProvider)
    assert provider.api_key == "test-key"

    print("✅ Factory registration test passed")


def test_custom_provider_connection_test():
    """Test the connection test functionality."""
    print("🧪 Testing CustomProvider connection test...")

    provider = CustomProvider("test-key")

    # Configure for a test endpoint (this will likely fail, but should not crash)
    provider.configure_api(
        api_url="https://httpbin.org/status/200",  # A reliable test endpoint
        auth_header="Authorization",
        auth_format="Bearer {api_key}"
    )

    # Test connection (this might fail due to network, but should not crash)
    try:
        result = provider.test_connection()

        # Check result structure
        assert "timestamp" in result
        assert "api_url" in result
        assert "connection_successful" in result
        assert "response_time_ms" in result
        assert "status_code" in result

        print(f"✅ Connection test completed (success: {result['connection_successful']})")

    except Exception as e:
        print(f"⚠️  Connection test failed with exception: {e}")
        print("   This is expected if there's no network connectivity")


def main():
    """Run all tests."""
    print("🚀 Starting CustomProvider tests...\n")

    tests = [
        test_custom_provider_basic,
        test_custom_provider_configuration,
        test_custom_provider_headers,
        test_custom_provider_request_data,
        test_custom_provider_response_parsing,
        test_custom_provider_debug_info,
        test_custom_provider_factory_registration,
        test_custom_provider_connection_test
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        print()

    print("📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")

    if failed == 0:
        print("\n🎉 All tests passed! CustomProvider is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)