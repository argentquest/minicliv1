"""
Pytest configuration and shared fixtures for the test suite.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from models import AppConfig, AppState, ConversationMessage
from file_scanner import CodebaseScanner
from ai import AIProcessor
from env_manager import EnvManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_py_files(temp_dir):
    """Create sample Python files for testing file scanner."""
    files = {
        "main.py": "# Main application\nprint('Hello, World!')",
        "utils.py": "def helper_function():\n    pass",
        "tests/test_main.py": "import unittest\n\nclass TestMain(unittest.TestCase):\n    pass",
        ".env": "API_KEY=test_key_123\nDEBUG=True"
    }
    
    created_files = []
    for filename, content in files.items():
        filepath = Path(temp_dir) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)
        created_files.append(str(filepath))
    
    return created_files


@pytest.fixture
def mock_env_file(temp_dir):
    """Create a mock .env file for testing."""
    env_path = Path(temp_dir) / ".env"
    env_content = """# Test environment file
API_KEY=sk-test123
OPENROUTER_API_KEY=sk-or-test456
DEFAULT_MODEL=openai/gpt-3.5-turbo
UI_THEME=light
MODELS=openai/gpt-3.5-turbo,openai/gpt-4
TOOL_LINT=pylint --disable=all
TOOL_TEST=pytest -v
"""
    env_path.write_text(env_content)
    return str(env_path)


@pytest.fixture
def app_config():
    """Create a test app configuration."""
    return AppConfig.get_default()


@pytest.fixture
def app_state():
    """Create a test app state."""
    return AppState()


@pytest.fixture
def conversation_messages():
    """Create sample conversation messages for testing."""
    return [
        ConversationMessage(role="system", content="You are a helpful assistant."),
        ConversationMessage(role="user", content="What is Python?"),
        ConversationMessage(role="assistant", content="Python is a programming language."),
        ConversationMessage(role="user", content="How do I write a function?"),
        ConversationMessage(role="assistant", content="Use the 'def' keyword to define a function.")
    ]


@pytest.fixture
def mock_ai_response():
    """Mock AI API response for testing."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a test AI response with code suggestions."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for AI API calls."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Mocked AI response content"
                }
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 25,
            "total_tokens": 75
        }
    }
    
    with patch('requests.post', return_value=mock_response) as mock_post:
        yield mock_post


@pytest.fixture
def codebase_scanner():
    """Create a CodebaseScanner instance for testing."""
    return CodebaseScanner()


@pytest.fixture
def ai_processor():
    """Create an AIProcessor instance for testing."""
    return AIProcessor(api_key="test-key", provider="openrouter")


@pytest.fixture
def env_manager():
    """Create an EnvManager instance for testing."""
    return EnvManager()


@pytest.fixture
def mock_system_message_manager():
    """Mock the system message manager."""
    mock_manager = Mock()
    mock_manager.get_system_message.return_value = "You are a helpful coding assistant."
    mock_manager.has_custom_system_message.return_value = True
    mock_manager.get_current_system_message_file.return_value = "systemmessage_default.txt"
    return mock_manager


# Test data constants
SAMPLE_CODE_CONTENT = '''
"""
Sample Python module for testing.
"""

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

def process_data(data: list) -> dict:
    """Process a list of data and return statistics."""
    if not data:
        return {"count": 0, "sum": 0, "avg": 0}
    
    return {
        "count": len(data),
        "sum": sum(data),
        "avg": sum(data) / len(data)
    }

class DataProcessor:
    """Example class for data processing."""
    
    def __init__(self, name: str):
        self.name = name
        self.processed_count = 0
    
    def process_item(self, item):
        """Process a single item."""
        self.processed_count += 1
        return f"Processed {item} by {self.name}"
'''

SAMPLE_CODEBASE_FILES = {
    "main.py": SAMPLE_CODE_CONTENT,
    "utils.py": """
def helper_function(x):
    return x * 2

def format_output(data):
    return json.dumps(data, indent=2)
""",
    "config.py": """
import os
from dataclasses import dataclass

@dataclass
class Config:
    api_key: str = os.getenv("API_KEY", "")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
""",
    "tests/test_utils.py": """
import unittest
from utils import helper_function

class TestUtils(unittest.TestCase):
    def test_helper_function(self):
        self.assertEqual(helper_function(5), 10)
"""
}