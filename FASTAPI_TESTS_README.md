# FastAPI Integration Tests

This directory contains comprehensive integration tests for the Code Chat AI FastAPI server.

## 📋 Overview

The test suite includes:
- **Unit-style tests** with mocked dependencies (no external API calls)
- **Real server tests** that can test against a running FastAPI server
- **Parameter validation tests** for both JSON and query parameter endpoints
- **Error handling tests** for various failure scenarios

## 🧪 Test Files

### `test_fastapi_integration.py`
Main test suite containing:
- Health endpoint tests
- POST `/analyze` (JSON body) tests
- GET `/analyze` (query parameters) tests
- Parameter validation tests
- Error handling tests
- File filtering and saving tests

### `run_fastapi_tests.py`
Test runner script with:
- Easy command-line interface
- Options for different test modes
- Test summary and help

## 🚀 Quick Start

### Run All Tests (Mocked)
```bash
python run_fastapi_tests.py
```

### Run Only Unit Tests
```bash
python run_fastapi_tests.py --unit-only
```

### Test Against Real Server
```bash
# First, start the FastAPI server in another terminal
python fastapi_server.py

# Then run real server tests
python run_fastapi_tests.py --real-server
```

### Show Test Summary
```bash
python run_fastapi_tests.py --summary
```

## 📖 Test Examples

### Basic Analysis Test
The tests focus on the default folder (current working directory) with an "explain" question:

```python
# Test data used in tests
test_folder = os.getcwd()  # Current directory
test_question = "Explain what this code does"
```

### JSON POST Endpoint Test
```python
request_data = {
    "folder": test_folder,
    "question": test_question,
    "model": "gpt-3.5-turbo",
    "provider": "openrouter",
    "output": "structured"
}
```

### Query Parameters GET Endpoint Test
```python
params = {
    "folder": test_folder,
    "question": test_question,
    "model": "gpt-3.5-turbo",
    "provider": "openrouter",
    "output": "structured"
}
```

## 🛠️ Test Configuration

### Mocked Tests
- Use `unittest.mock` to mock CLI interface methods
- No external API calls required
- Fast execution
- Safe for CI/CD pipelines

### Real Server Tests
- Require running FastAPI server on `http://localhost:8000`
- Make actual HTTP requests
- Test real functionality
- Require valid API keys

## 📊 Test Coverage

The test suite covers:

### Endpoints Tested
- ✅ `GET /health` - Health check
- ✅ `POST /analyze` - JSON body analysis
- ✅ `GET /analyze` - Query parameter analysis
- ✅ `GET /models` - Available models
- ✅ `GET /providers` - Available providers
- ✅ `GET /system-prompts` - System prompts

### Parameter Validation
- ✅ Required parameters (`folder`, `question`)
- ✅ Optional parameters (`model`, `provider`, `api_key`, etc.)
- ✅ Provider validation against available providers
- ✅ Output format validation (`structured` or `json`)
- ✅ File filtering parameters (`include`, `exclude`)

### Error Handling
- ✅ Missing required parameters
- ✅ Invalid parameter values
- ✅ Provider validation errors
- ✅ File operation errors
- ✅ API processing errors

### Features Tested
- ✅ File filtering with include/exclude patterns
- ✅ File saving functionality
- ✅ Verbose logging
- ✅ Different output formats
- ✅ System prompt selection

## 🔧 Running Tests Manually

### Using pytest directly
```bash
# Run all tests
python -m pytest test_fastapi_integration.py -v

# Run specific test class
python -m pytest test_fastapi_integration.py::TestFastAPIServerIntegration -v

# Run specific test method
python -m pytest test_fastapi_integration.py::TestFastAPIServerIntegration::test_health_endpoint -v
```

### Using the test runner
```bash
# All tests
python run_fastapi_tests.py

# Unit tests only
python run_fastapi_tests.py --unit-only

# Real server tests
python run_fastapi_tests.py --real-server
```

## 🌐 Testing Real Server

To test against a real running server:

1. **Start the FastAPI server:**
   ```bash
   python fastapi_server.py
   ```

2. **Configure environment variables:**
   ```bash
   export API_KEY="your-api-key-here"
   export PROVIDER="openrouter"
   export DEFAULT_MODEL="gpt-3.5-turbo"
   ```

3. **Run real server tests:**
   ```bash
   python run_fastapi_tests.py --real-server
   ```

## 📈 Test Results

### Expected Mocked Test Results
```
🧪 Running FastAPI Integration Tests (Mocked)
==================================================
test_analyze_get_minimal_params ... ok
test_analyze_invalid_output_format ... ok
test_analyze_invalid_provider ... ok
test_analyze_missing_required_params ... ok
test_analyze_post_json_endpoint ... ok
test_analyze_get_params_endpoint ... ok
test_analyze_with_file_saving ... ok
test_analyze_with_filters ... ok
test_analyze_json_validation ... ok
test_health_endpoint ... ok
test_models_endpoint ... ok
test_providers_endpoint ... ok
test_system_prompts_endpoint ... ok

======================== 13 passed in 0.45s ========================
```

### Expected Real Server Test Results
```
🌐 Testing Real FastAPI Server
==================================================
✅ Health check: 200
✅ Models endpoint: 200
✅ Providers endpoint: 200
✅ GET analysis: 200

🎉 Real server testing complete!
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the correct directory
   cd /path/to/minicli

   # Activate virtual environment
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. **Mock Errors**
   - Ensure all required dependencies are installed
   - Check that the FastAPI server imports work correctly

3. **Real Server Connection Errors**
   - Verify the server is running on `http://localhost:8000`
   - Check firewall settings
   - Ensure API keys are properly configured

4. **Test Timeouts**
   - Increase timeout values in test configuration
   - Check network connectivity for real server tests

## 📝 Adding New Tests

### Adding Unit Tests
```python
def test_new_feature(self):
    """Test description."""
    # Setup mocks
    # Make request
    # Assert response
```

### Adding Real Server Tests
```python
def test_real_server_feature():
    """Test against real server."""
    import requests
    # Make real HTTP request
    # Assert response
```

## 🎯 Best Practices

1. **Use descriptive test names** that explain what they're testing
2. **Mock external dependencies** to avoid flaky tests
3. **Test both success and error cases**
4. **Use appropriate assertions** for different response types
5. **Keep tests independent** and isolated
6. **Document test requirements** and setup steps

## 📞 Support

For issues with the test suite:
1. Check the troubleshooting section above
2. Verify your environment setup
3. Review the test output for specific error messages
4. Ensure all dependencies are properly installed

---

**Happy Testing! 🧪✨**