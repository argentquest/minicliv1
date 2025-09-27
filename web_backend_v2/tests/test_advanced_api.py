"""
Advanced tests to increase coverage for WhisperCode Web2 Backend.

These tests cover edge cases, error conditions, and less common code paths.
"""

import pytest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app, _load_env_defaults, _session_summary_model, _conversation_state_response

client = TestClient(app)


class TestLoadEnvDefaults:
    """Test environment defaults loading."""
    
    @patch('api.env_manager')
    def test_load_env_defaults_with_values(self, mock_env_manager):
        """Test loading environment defaults with all values set."""
        mock_env_manager.load_env_file.return_value = {
            "PROVIDER": "anthropic",
            "MODELS": "claude-3-sonnet,claude-3-haiku,gpt-4",
            "DEFAULT_MODEL": "claude-3-sonnet",
            "API_KEY": "test-api-key-123"
        }
        
        api_key, provider, models, default_model = _load_env_defaults()
        
        assert api_key == "test-api-key-123"
        assert provider == "anthropic"
        assert models == ["claude-3-sonnet", "claude-3-haiku", "gpt-4"]
        assert default_model == "claude-3-sonnet"
    
    @patch('api.env_manager')
    def test_load_env_defaults_fallbacks(self, mock_env_manager):
        """Test loading environment defaults with fallback values."""
        mock_env_manager.load_env_file.return_value = {}
        
        api_key, provider, models, default_model = _load_env_defaults()
        
        assert api_key == ""
        assert provider == "openrouter"
        assert "openai/gpt-3.5-turbo" in models
        assert "anthropic/claude-3-haiku" in models
        assert default_model in models


class TestUtilityFunctions:
    """Test utility functions."""
    
    @patch('api.conversation_manager')
    def test_session_summary_model(self, mock_conversation_manager):
        """Test session summary model creation."""
        # Create a mock session with summary
        mock_session = Mock()
        mock_summary = Mock()
        mock_summary.conversation_id = "test-conv-123"
        mock_summary.provider = "openrouter"
        mock_summary.selected_model = "gpt-4"
        mock_summary.selected_directory = "/test/dir"
        mock_summary.selected_files = ["file1.py", "file2.js"]
        mock_summary.persistent_files = ["persistent.txt"]
        mock_summary.question_history = []
        mock_summary.conversation_history = []
        
        mock_session.get_summary.return_value = mock_summary
        
        result = _session_summary_model(mock_session)
        
        assert result.conversation_id == "test-conv-123"
        assert result.provider == "openrouter"
        assert result.selected_model == "gpt-4"
        assert result.selected_directory == "/test/dir"
        assert result.selected_files == ["file1.py", "file2.js"]
    
    @patch('api.conversation_manager')
    @patch('api.env_manager')
    def test_conversation_state_response(self, mock_env_manager, mock_conversation_manager):
        """Test conversation state response creation."""
        # Mock environment loading
        mock_env_manager.load_env_file.return_value = {
            "PROVIDER": "anthropic",
            "MODELS": "claude-3-sonnet,claude-3-haiku",
            "DEFAULT_MODEL": "claude-3-sonnet",
            "API_KEY": "test-key"
        }
        
        # Create a mock session
        mock_session = Mock()
        mock_session.session_id = "test-session-456"
        mock_session.provider = "anthropic"
        mock_session.available_models = ["claude-3-sonnet", "claude-3-haiku"]
        
        mock_summary = Mock()
        mock_summary.conversation_id = "test-conv-456"
        mock_summary.provider = "anthropic"
        mock_summary.selected_model = "claude-3"
        mock_summary.selected_directory = "/src"
        mock_summary.selected_files = ["main.py"]
        mock_summary.persistent_files = []
        mock_summary.question_history = []
        mock_summary.conversation_history = []
        
        mock_session.get_summary.return_value = mock_summary
        
        result = _conversation_state_response(mock_session)
        
        assert result.conversation_id == "test-session-456"
        assert result.summary.conversation_id == "test-conv-456"


class TestAdvancedCodeExtraction:
    """Test advanced code extraction scenarios."""
    
    def test_extract_code_html_fallback(self):
        """Test HTML code block extraction fallback."""
        html_content = '''
        <p>Here's some code:</p>
        <pre><code class="language-python">
def hello_world():
    print("Hello from HTML!")
    return "success"
</code></pre>
        
        <pre><code class="language-javascript">
console.log("JavaScript from HTML");
const result = calculate(5, 10);
</code></pre>
        '''
        
        response = client.post("/api/code/extract", json={
            "messageId": "html-test-123",
            "content": html_content
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) >= 2
        
        # Check Python block
        python_block = next((block for block in data["data"] if block["language"] == "python"), None)
        assert python_block is not None
        assert "hello_world" in python_block["code"]
        assert python_block["source"] == "html"
        
        # Check JavaScript block  
        js_block = next((block for block in data["data"] if block["language"] == "javascript"), None)
        assert js_block is not None
        assert "console.log" in js_block["code"]
    
    def test_extract_code_html_entities(self):
        """Test HTML entity cleanup in code extraction."""
        html_with_entities = '''
        <pre><code class="language-xml">
&lt;configuration&gt;
    &lt;setting name=&quot;debug&quot;&gt;true&lt;/setting&gt;
    &lt;api-key&gt;secret&amp;key&lt;/api-key&gt;
&lt;/configuration&gt;
</code></pre>
        '''
        
        response = client.post("/api/code/extract", json={
            "messageId": "entities-test",
            "content": html_with_entities
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) >= 1
        xml_block = data["data"][0]
        
        # Verify HTML entities were cleaned up
        assert "<configuration>" in xml_block["code"]
        assert "\"debug\"" in xml_block["code"]
        assert "secret&key" in xml_block["code"]
    
    def test_extract_code_no_language_specified(self):
        """Test code extraction when no language is specified."""
        content_no_lang = '''
Here's some code without language specification:

```
function mystery() {
    return "What language am I?";
}
```

```
SELECT * FROM unknown_table;
```
        '''
        
        response = client.post("/api/code/extract", json={
            "messageId": "no-lang-test",
            "content": content_no_lang
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) >= 2
        
        # Check that language detection worked
        for block in data["data"]:
            assert block["language"] in ["javascript", "sql", "text"]
    
    def test_extract_code_empty_blocks(self):
        """Test extraction ignores empty code blocks."""
        content_with_empty = '''Valid code:
```python
print("Hello")
```

Empty block:
```javascript

```

Another empty:
```

```

More valid code:
```sql
SELECT 1;
```'''
        
        response = client.post("/api/code/extract", json={
            "messageId": "empty-test",
            "content": content_with_empty
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only extract non-empty blocks
        assert len(data["data"]) == 2
        
        # Verify only valid blocks are included
        languages = [block["language"] for block in data["data"]]
        assert "python" in languages
        assert "sql" in languages


class TestAdvancedMermaidRendering:
    """Test advanced Mermaid rendering scenarios."""
    
    def test_mermaid_svg_format(self):
        """Test Mermaid rendering with SVG format."""
        with patch('api._render_with_mermaid_cli') as mock_cli:
            mock_cli.return_value = (True, "data:image/svg+xml;base64,fake_svg_data")
            
            response = client.post("/api/mermaid/render", json={
                "code": "graph LR\nA --> B",
                "format": "svg"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "data:image/svg+xml;base64," in data["data"]
            assert data["format"] == "svg"
    
    def test_mermaid_complex_diagram(self):
        """Test Mermaid rendering with complex diagram."""
        complex_diagram = '''
        flowchart TD
            A[Start] --> B{Decision}
            B -->|Yes| C[Process A]
            B -->|No| D[Process B]
            C --> E[Subprocess]
            E --> F[End]
            D --> F
            
            subgraph "Error Handling"
                G[Error] --> H[Log]
                H --> I[Retry]
                I --> B
            end
        '''
        
        with patch('api._render_with_python_mermaid') as mock_python:
            mock_python.return_value = (True, "data:image/svg+xml;base64,complex_diagram")
            
            response = client.post("/api/mermaid/render", json={
                "code": complex_diagram,
                "title": "complex_workflow"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "complex_diagram" in data["data"]
    
    def test_mermaid_all_methods_fail(self):
        """Test Mermaid rendering when all methods fail."""
        with patch('api._render_with_mermaid_cli') as mock_cli, \
             patch('api._render_with_puppeteer') as mock_puppeteer, \
             patch('api._render_with_python_mermaid') as mock_python:
            
            # All methods fail
            mock_cli.return_value = (False, "")
            mock_puppeteer.return_value = (False, "")
            mock_python.return_value = (False, "")
            
            response = client.post("/api/mermaid/render", json={
                "code": "graph TD\nA --> B"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Should fallback to client-side rendering
            assert data["success"] is True
            assert data["fallback"] is True
            assert data["clientRender"] is True
            assert "data:text/plain;base64," in data["data"]


class TestRootEndpoint:
    """Test the root endpoint and other basic endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "WhisperCode Web2" in data["message"]
    
    def test_docs_endpoints(self):
        """Test documentation endpoints are accessible."""
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200
        
        redoc_response = client.get("/redoc")
        assert redoc_response.status_code == 200


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_extract_code_malformed_json_request(self):
        """Test code extraction with malformed request."""
        # Test with missing messageId but valid content
        response = client.post("/api/code/extract", json={
            "content": "```python\nprint('test')\n```"
        })
        
        assert response.status_code == 400
        assert "messageId is required" in response.json()["detail"]
    
    def test_mermaid_empty_code(self):
        """Test Mermaid rendering with empty code."""
        response = client.post("/api/mermaid/render", json={
            "code": "",
            "title": "empty"
        })
        
        assert response.status_code == 400
        assert "mermaid code is required" in response.json()["detail"]
    
    def test_chat_very_long_message(self):
        """Test chat with very long message."""
        long_message = "A" * 10000  # 10KB message
        
        # This should be handled gracefully
        response = client.post("/api/chat", json={
            "message": long_message
        })
        
        # Either processes successfully or rejects appropriately
        assert response.status_code in [200, 400, 413, 500]
    
    def test_code_extraction_unicode_content(self):
        """Test code extraction with Unicode content."""
        unicode_content = '''
Here's code with Unicode:

```python
def unicode_test():
    # Unicode comments: 🚀 💻 🎯
    text = "Hello, 世界! Café, naïve"
    emoji = "🐍 Python rocks! 🔥"
    return f"Result: {text} {emoji}"
```

```javascript
const greet = (name) => {
    // Emoji in JavaScript: ✨
    return `Hello ${name}! 👋 Welcome to JavaScript! 🎉`;
};
```
        '''
        
        response = client.post("/api/code/extract", json={
            "messageId": "unicode-test-456",
            "content": unicode_content
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) >= 2
        
        # Verify Unicode is preserved
        for block in data["data"]:
            if block["language"] == "python":
                assert "🚀" in block["code"]
                assert "世界" in block["code"]
            elif block["language"] == "javascript":
                assert "✨" in block["code"]
                assert "👋" in block["code"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])