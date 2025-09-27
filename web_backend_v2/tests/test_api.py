"""
Comprehensive unit tests for WhisperCode Web2 Backend API.

Tests cover all endpoints including:
- AI chat integration
- Code extraction
- Mermaid rendering
- Core API functionality
"""

import pytest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the Python path to import the api module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from our API module
from api import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check(self):
        """Test basic health check functionality."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "WhisperCode Web2 Backend"
        assert data["version"] == "2.0.0"


class TestChatEndpoint:
    """Test the enhanced chat endpoint with AI integration."""
    
    @patch('api.conversation_manager')
    def test_chat_missing_message(self, mock_conversation_manager):
        """Test chat endpoint with missing message."""
        response = client.post("/api/chat", json={})
        assert response.status_code == 400
        assert "message is required" in response.json()["detail"]
    
    @patch('api.conversation_manager')
    @patch('api._load_env_defaults')
    def test_chat_new_conversation(self, mock_load_env, mock_conversation_manager):
        """Test chat with new conversation creation."""
        # Mock environment defaults
        mock_load_env.return_value = ("test_key", "openrouter", ["gpt-4"], "gpt-4")
        
        # Mock conversation manager
        mock_session = Mock()
        mock_session.session_id = "test-session-123"
        
        # Create a mock summary object
        mock_summary = Mock()
        mock_summary.conversation_history = []
        mock_summary.selected_model = "gpt-4"
        mock_summary.provider = "openrouter"
        
        mock_session.get_summary.return_value = mock_summary
        
        mock_conversation_manager.get_session.return_value = None
        mock_conversation_manager.create_conversation.return_value = mock_session
        
        # Mock AI response
        mock_response = Mock()
        mock_response.response = "Hello! I'm an AI assistant."
        mock_response.tokens_used = 10
        mock_response.processing_time = 1.5
        mock_response.timestamp = "2025-09-27T00:00:00Z"
        
        mock_conversation_manager.ask_question.return_value = mock_response
        
        # Test the endpoint
        response = client.post("/api/chat", json={
            "message": "Hello, how are you?",
            "conversationId": "new-conversation",
            "settings": {"model": "gpt-4"}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "message" in data["data"]
        assert data["data"]["message"]["role"] == "assistant"
        assert data["data"]["message"]["content"] == "Hello! I'm an AI assistant."
        assert data["data"]["conversationId"] == "test-session-123"
    
    @patch('api.conversation_manager')
    def test_chat_existing_conversation(self, mock_conversation_manager):
        """Test chat with existing conversation."""
        # Mock existing session
        mock_session = Mock()
        mock_session.session_id = "existing-session-456"
        
        # Create a mock summary object
        mock_summary = Mock()
        mock_summary.conversation_history = [Mock(role="user", content="Previous message")]
        mock_summary.selected_model = "claude-3"
        mock_summary.provider = "anthropic"
        
        mock_session.get_summary.return_value = mock_summary
        
        mock_conversation_manager.get_session.return_value = mock_session
        
        # Mock AI response
        mock_response = Mock()
        mock_response.response = "I understand your question about Python."
        mock_response.tokens_used = 25
        mock_response.processing_time = 2.1
        mock_response.timestamp = "2025-09-27T00:00:00Z"
        
        mock_conversation_manager.ask_question.return_value = mock_response
        
        # Test the endpoint
        response = client.post("/api/chat", json={
            "message": "Can you explain Python functions?",
            "conversationId": "existing-session-456"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["message"]["content"] == "I understand your question about Python."
        assert data["data"]["usage"]["completionTokens"] == 25
    
    @patch('api.conversation_manager')
    @patch('api.file_service')
    def test_chat_with_context_files(self, mock_file_service, mock_conversation_manager):
        """Test chat with context files."""
        # Mock file service
        mock_file_service.read_file_content.return_value = "def hello(): print('Hello World')"
        
        # Mock existing session
        mock_session = Mock()
        mock_session.session_id = "context-session-789"
        
        # Create a mock summary object
        mock_summary = Mock()
        mock_summary.conversation_history = []
        mock_summary.selected_model = "gpt-4"
        mock_summary.provider = "openai"
        
        mock_session.get_summary.return_value = mock_summary
        
        mock_conversation_manager.get_session.return_value = mock_session
        mock_conversation_manager.update_selected_files.return_value = None
        
        # Mock AI response
        mock_response = Mock()
        mock_response.response = "This Python function prints 'Hello World'."
        mock_response.tokens_used = 15
        mock_response.processing_time = 1.8
        mock_response.timestamp = "2025-09-27T00:00:00Z"
        
        mock_conversation_manager.ask_question.return_value = mock_response
        
        # Test the endpoint
        response = client.post("/api/chat", json={
            "message": "Explain this code",
            "conversationId": "context-session-789",
            "contextFiles": ["test.py", "utils.py"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "This Python function" in data["data"]["message"]["content"]
        
        # Verify file service was called
        mock_file_service.read_file_content.assert_called()


class TestCodeExtractionEndpoint:
    """Test the code extraction functionality."""
    
    def test_extract_code_missing_message_id(self):
        """Test code extraction with missing messageId."""
        response = client.post("/api/code/extract", json={})
        assert response.status_code == 400
        assert "messageId is required" in response.json()["detail"]
    
    def test_extract_code_with_content(self):
        """Test code extraction with provided content."""
        message_content = '''
Here's a Python function:

```python
def calculate_sum(a, b):
    return a + b
```

And some JavaScript:

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
}
```

Also some inline code: `print("hello")` and `npm install`.
'''
        
        response = client.post("/api/code/extract", json={
            "messageId": "test-message-123",
            "content": message_content
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) >= 2  # At least 2 fenced code blocks
        
        # Check Python code block
        python_block = next((block for block in data["data"] if block["language"] == "python"), None)
        assert python_block is not None
        assert "def calculate_sum" in python_block["code"]
        assert python_block["filename"].endswith(".py")
        
        # Check JavaScript code block
        js_block = next((block for block in data["data"] if block["language"] == "javascript"), None)
        assert js_block is not None
        assert "function greet" in js_block["code"]
        assert js_block["filename"].endswith(".js")
    
    @patch('api.conversation_manager')
    def test_extract_code_from_conversation(self, mock_conversation_manager):
        """Test code extraction from conversation history."""
        # Mock conversation with code in history
        mock_session = Mock()
        mock_entry = Mock()
        mock_entry.role = "assistant"
        mock_entry.content = '''Here's the solution:

```sql
SELECT name, age FROM users WHERE age > 18;
```
'''
        mock_session.get_summary.return_value.conversation_history = [mock_entry]
        
        mock_conversation_manager._sessions = {
            "test-session": mock_session
        }
        
        response = client.post("/api/code/extract", json={
            "messageId": "msg-test-session-1"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        sql_block = data["data"][0]
        assert sql_block["language"] == "sql"
        assert "SELECT name, age" in sql_block["code"]
    
    def test_extract_code_no_content_found(self):
        """Test code extraction when no content is found."""
        response = client.post("/api/code/extract", json={
            "messageId": "non-existent-message"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 0
        assert "No content found" in data["message"]


class TestMermaidRenderingEndpoint:
    """Test the Mermaid diagram rendering functionality."""
    
    def test_mermaid_missing_code(self):
        """Test Mermaid rendering with missing code."""
        response = client.post("/api/mermaid/render", json={})
        assert response.status_code == 400
        assert "mermaid code is required" in response.json()["detail"]
    
    @patch('api._render_with_mermaid_cli')
    def test_mermaid_successful_cli_render(self, mock_cli_render):
        """Test successful Mermaid rendering with CLI."""
        mock_cli_render.return_value = (True, "data:image/png;base64,fake_png_data")
        
        mermaid_code = '''
graph TD
    A[Start] --> B[Process]
    B --> C[End]
'''
        
        response = client.post("/api/mermaid/render", json={
            "code": mermaid_code,
            "title": "test_diagram"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data:image/png;base64," in data["data"]
        assert "rendered successfully" in data["message"]
        assert data["format"] == "png"
    
    @patch('api._render_with_mermaid_cli')
    @patch('api._render_with_puppeteer')
    def test_mermaid_fallback_to_puppeteer(self, mock_puppeteer, mock_cli):
        """Test Mermaid rendering fallback to Puppeteer."""
        mock_cli.return_value = (False, "")
        mock_puppeteer.return_value = (True, "data:image/png;base64,puppeteer_data")
        
        mermaid_code = "graph LR\n    A --> B"
        
        response = client.post("/api/mermaid/render", json={
            "code": mermaid_code
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "puppeteer_data" in data["data"]
    
    @patch('api._render_with_mermaid_cli')
    @patch('api._render_with_puppeteer')
    @patch('api._render_with_python_mermaid')
    def test_mermaid_fallback_to_python(self, mock_python, mock_puppeteer, mock_cli):
        """Test Mermaid rendering fallback to Python."""
        mock_cli.return_value = (False, "")
        mock_puppeteer.return_value = (False, "")
        mock_python.return_value = (True, "data:image/svg+xml;base64,svg_data")
        
        mermaid_code = "flowchart TD\n    Start --> End"
        
        response = client.post("/api/mermaid/render", json={
            "code": mermaid_code
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "svg_data" in data["data"]
    
    @patch('api._render_with_mermaid_cli')
    @patch('api._render_with_puppeteer')
    @patch('api._render_with_python_mermaid')
    def test_mermaid_client_side_fallback(self, mock_python, mock_puppeteer, mock_cli):
        """Test Mermaid rendering final fallback to client-side."""
        mock_cli.return_value = (False, "")
        mock_puppeteer.return_value = (False, "")
        mock_python.return_value = (False, "")
        
        mermaid_code = "graph TD\n    A --> B"
        
        response = client.post("/api/mermaid/render", json={
            "code": mermaid_code
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["fallback"] is True
        assert data["clientRender"] is True
        assert "data:text/plain;base64," in data["data"]


class TestCodeExtractionHelpers:
    """Test the helper functions for code extraction."""
    
    def test_detect_language_python(self):
        """Test Python language detection."""
        from api import _detect_language
        
        python_code = "def hello():\n    print('Hello')\n    import os"
        assert _detect_language(python_code) == "python"
    
    def test_detect_language_javascript(self):
        """Test JavaScript language detection."""
        from api import _detect_language
        
        js_code = "function test() {\n    console.log('test');\n    const x = 5;"
        assert _detect_language(js_code) == "javascript"
    
    def test_detect_language_sql(self):
        """Test SQL language detection."""
        from api import _detect_language
        
        sql_code = "SELECT * FROM users WHERE id = 1;"
        assert _detect_language(sql_code) == "sql"
    
    def test_detect_language_fallback(self):
        """Test language detection fallback to text."""
        from api import _detect_language
        
        unknown_code = "This is just plain text without any code indicators"
        assert _detect_language(unknown_code) == "text"
    
    def test_generate_filename(self):
        """Test filename generation."""
        from api import _generate_filename
        
        assert _generate_filename("python", 1) == "extracted_code_1.py"
        assert _generate_filename("javascript", 2) == "extracted_code_2.js"
        assert _generate_filename("unknown", 3) == "extracted_code_3.txt"


class TestMermaidRenderingHelpers:
    """Test the helper functions for Mermaid rendering."""
    
    def test_create_simple_flowchart_svg(self):
        """Test simple SVG flowchart creation."""
        from api import _create_simple_flowchart_svg
        
        mermaid_code = "graph TD\n    A --> B\n    B --> C"
        svg_content = _create_simple_flowchart_svg(mermaid_code)
        
        assert svg_content.startswith('<svg')
        assert 'Start' in svg_content
        assert 'Process' in svg_content
        assert 'End' in svg_content
        assert '</svg>' in svg_content


class TestErrorHandling:
    """Test error handling across all endpoints."""
    
    @patch('api.conversation_manager')
    def test_chat_error_handling(self, mock_conversation_manager):
        """Test chat endpoint error handling."""
        mock_conversation_manager.get_session.side_effect = Exception("Database error")
        
        response = client.post("/api/chat", json={
            "message": "Test message"
        })
        
        assert response.status_code == 500
        assert "Failed to process message" in response.json()["detail"]
    
    def test_code_extraction_error_handling(self):
        """Test code extraction error handling."""
        # Test with invalid JSON that would cause an error
        with patch('api.conversation_manager._sessions', side_effect=Exception("Error")):
            response = client.post("/api/code/extract", json={
                "messageId": "test-id"
            })
            
            # The endpoint should handle errors gracefully
            assert response.status_code in [200, 500]  # Either handles gracefully or returns 500
    
    def test_mermaid_error_handling(self):
        """Test Mermaid rendering error handling."""
        # Test with very large code that might cause memory issues
        large_code = "graph TD\n" + "\n".join([f"    A{i} --> A{i+1}" for i in range(1000)])
        
        response = client.post("/api/mermaid/render", json={
            "code": large_code
        })
        
        # Should either succeed or handle error gracefully
        assert response.status_code in [200, 500]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])