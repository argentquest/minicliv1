"""
Pytest configuration and fixtures for WhisperCode Web2 Backend tests.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_defaults():
    """Mock environment defaults for testing."""
    return ("test_api_key", "openrouter", ["gpt-4", "claude-3"], "gpt-4")


@pytest.fixture
def mock_conversation_session():
    """Create a mock conversation session."""
    session = Mock()
    session.session_id = "test-session-123"
    session.get_summary.return_value.conversation_history = []
    session.get_summary.return_value.selected_model = "gpt-4"
    session.get_summary.return_value.provider = "openrouter"
    session.get_summary.return_value.selected_files = []
    session.get_summary.return_value.persistent_files = []
    return session


@pytest.fixture
def mock_ai_response():
    """Create a mock AI response."""
    response = Mock()
    response.response = "This is a test AI response."
    response.tokens_used = 25
    response.processing_time = 1.5
    response.timestamp = "2025-09-27T00:00:00Z"
    return response


@pytest.fixture
def sample_code_content():
    """Sample content with various code blocks."""
    return '''
Here are some code examples:

```python
def hello_world():
    print("Hello, World!")
    return True
```

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
    return name.toUpperCase();
}
```

```sql
SELECT id, name, email 
FROM users 
WHERE created_at > '2025-01-01';
```

Some inline code: `print("test")` and `npm install react`.
'''


@pytest.fixture
def sample_mermaid_content():
    """Sample Mermaid diagram content."""
    return '''
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process A]
    B -->|No| D[Process B]
    C --> E[End]
    D --> E
'''


@pytest.fixture
def mock_file_service():
    """Mock the file service."""
    with patch('api.file_service') as mock_service:
        mock_service.read_file_content.return_value = "def sample_function(): pass"
        yield mock_service


@pytest.fixture
def mock_conversation_manager():
    """Mock the conversation manager."""
    with patch('api.conversation_manager') as mock_manager:
        # Setup default behavior
        mock_manager.get_session.return_value = None
        mock_manager.create_conversation.return_value = Mock()
        mock_manager.ask_question.return_value = Mock()
        mock_manager.update_selected_files.return_value = None
        mock_manager._sessions = {}
        yield mock_manager


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup any temporary files created during tests."""
    yield
    # Cleanup logic here if needed
    pass


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")