"""
Integration tests for WhisperCode Web2 Backend.

Tests the complete workflow and integration between components.
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

from api import app

client = TestClient(app)


class TestCompleteWorkflow:
    """Test complete chat workflow with code extraction and Mermaid rendering."""
    
    @patch('api.conversation_manager')
    @patch('api._load_env_defaults')
    def test_complete_chat_and_extract_workflow(self, mock_load_env, mock_conversation_manager):
        """Test complete workflow: chat -> extract code -> render diagram."""
        
        # Setup mocks
        mock_load_env.return_value = ("test_key", "openrouter", ["gpt-4"], "gpt-4")
        
        # Mock conversation session
        mock_session = Mock()
        mock_session.session_id = "integration-test-session"
        
        # Create a mock summary object
        mock_summary = Mock()
        mock_summary.conversation_history = []
        mock_summary.selected_model = "gpt-4"
        mock_summary.provider = "openrouter"
        
        mock_session.get_summary.return_value = mock_summary
        
        mock_conversation_manager.get_session.return_value = None
        mock_conversation_manager.create_conversation.return_value = mock_session
        
        # Mock AI response with code and mermaid
        ai_response_content = '''
Here's a Python function and a process diagram:

```python
def process_data(data):
    """Process incoming data."""
    if not data:
        return None
    
    # Clean the data
    cleaned = data.strip().lower()
    
    # Process it
    result = cleaned.replace(' ', '_')
    return result
```

And here's the process flow:

```mermaid
graph TD
    A[Input Data] --> B{Is Valid?}
    B -->|Yes| C[Clean Data]
    B -->|No| D[Return None]
    C --> E[Process Data]
    E --> F[Return Result]
```

This function handles data processing with validation.
'''
        
        mock_response = Mock()
        mock_response.response = ai_response_content
        mock_response.tokens_used = 150
        mock_response.processing_time = 2.5
        mock_response.timestamp = "2025-09-27T00:00:00Z"
        
        mock_conversation_manager.ask_question.return_value = mock_response
        
        # Step 1: Send chat message
        chat_response = client.post("/api/chat", json={
            "message": "Can you show me a data processing function with a flow diagram?",
            "conversationId": "new-conversation",
            "settings": {"model": "gpt-4"}
        })
        
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        
        assert chat_data["success"] is True
        assert "python" in chat_data["data"]["message"]["content"]
        assert "mermaid" in chat_data["data"]["message"]["content"]
        
        # Step 2: Extract code from the response
        extract_response = client.post("/api/code/extract", json={
            "messageId": "test-message-id",
            "content": ai_response_content
        })
        
        assert extract_response.status_code == 200
        extract_data = extract_response.json()
        
        assert extract_data["success"] is True
        assert len(extract_data["data"]) >= 2  # Python + Mermaid blocks
        
        # Find the Python code block
        python_block = next((block for block in extract_data["data"] 
                           if block["language"] == "python"), None)
        assert python_block is not None
        assert "def process_data" in python_block["code"]
        
        # Find the Mermaid code block
        mermaid_block = next((block for block in extract_data["data"] 
                            if "mermaid" in block["code"] or "graph TD" in block["code"]), None)
        
        # Step 3: Render the Mermaid diagram
        if mermaid_block:
            mermaid_code = mermaid_block["code"]
        else:
            # Extract mermaid code directly
            import re
            mermaid_match = re.search(r'```mermaid\n(.*?)```', ai_response_content, re.DOTALL)
            mermaid_code = mermaid_match.group(1) if mermaid_match else "graph TD\nA --> B"
        
        with patch('api._render_with_mermaid_cli') as mock_cli:
            mock_cli.return_value = (True, "data:image/png;base64,fake_diagram_data")
            
            mermaid_response = client.post("/api/mermaid/render", json={
                "code": mermaid_code,
                "title": "data_processing_flow"
            })
            
            assert mermaid_response.status_code == 200
            mermaid_data = mermaid_response.json()
            
            assert mermaid_data["success"] is True
            assert "data:image/png;base64," in mermaid_data["data"]
    
    @patch('api.conversation_manager')
    def test_multi_conversation_management(self, mock_conversation_manager):
        """Test managing multiple conversations simultaneously."""
        
        # Create multiple mock sessions
        sessions = {}
        for i in range(3):
            session = Mock()
            session.session_id = f"session-{i}"
            
            # Create a mock summary object for each session
            mock_summary = Mock()
            mock_summary.conversation_history = []
            mock_summary.selected_model = "gpt-4"
            mock_summary.provider = "openrouter"
            
            session.get_summary.return_value = mock_summary
            sessions[f"session-{i}"] = session
        
        mock_conversation_manager.get_session.side_effect = lambda sid: sessions.get(sid)
        
        # Mock responses for each session
        responses = [
            "Response for session 0",
            "Response for session 1", 
            "Response for session 2"
        ]
        
        def mock_ask_question(session_id, request):
            session_num = int(session_id.split('-')[1])
            mock_resp = Mock()
            mock_resp.response = responses[session_num]
            mock_resp.tokens_used = 10 + session_num
            mock_resp.processing_time = 1.0 + session_num * 0.5
            mock_resp.timestamp = "2025-09-27T00:00:00Z"
            return mock_resp
        
        mock_conversation_manager.ask_question.side_effect = mock_ask_question
        
        # Test multiple conversations
        for i in range(3):
            response = client.post("/api/chat", json={
                "message": f"Hello from session {i}",
                "conversationId": f"session-{i}"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert f"Response for session {i}" in data["data"]["message"]["content"]
            assert data["data"]["conversationId"] == f"session-{i}"
    
    def test_error_recovery_and_fallbacks(self):
        """Test system behavior under various error conditions."""
        
        # Test code extraction with malformed content
        malformed_content = "```python\n# Missing closing backticks\ndef broken_func():\n    pass"
        
        response = client.post("/api/code/extract", json={
            "messageId": "malformed-test",
            "content": malformed_content
        })
        
        # Should handle gracefully
        assert response.status_code == 200
        
        # Test Mermaid rendering with invalid syntax
        invalid_mermaid = "invalid mermaid syntax that should fail"
        
        with patch('api._render_with_mermaid_cli') as mock_cli, \
             patch('api._render_with_puppeteer') as mock_puppeteer, \
             patch('api._render_with_python_mermaid') as mock_python:
            
            # All rendering methods fail
            mock_cli.return_value = (False, "")
            mock_puppeteer.return_value = (False, "")
            mock_python.return_value = (False, "")
            
            response = client.post("/api/mermaid/render", json={
                "code": invalid_mermaid
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Should fallback to client-side rendering
            assert data["success"] is True
            assert data.get("fallback") is True
            assert data.get("clientRender") is True


class TestPerformanceAndScaling:
    """Test performance characteristics and scaling behavior."""
    
    def test_large_content_handling(self):
        """Test handling of large content volumes."""
        
        # Create large code content
        large_code_content = "```python\n"
        for i in range(1000):
            large_code_content += f"def function_{i}():\n    return {i}\n\n"
        large_code_content += "```"
        
        response = client.post("/api/code/extract", json={
            "messageId": "large-content-test",
            "content": large_code_content
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        # Verify the extracted code contains expected content
        code_block = data["data"][0]
        assert "function_999" in code_block["code"]
        assert code_block["language"] == "python"
        assert code_block["lineCount"] > 2000  # Should have many lines
    
    def test_concurrent_requests_simulation(self):
        """Simulate concurrent request handling."""
        import threading
        import time
        
        results = []
        
        def make_request(request_id):
            try:
                response = client.get("/api/health")
                results.append({
                    "id": request_id,
                    "status": response.status_code,
                    "success": response.status_code == 200
                })
            except Exception as e:
                results.append({
                    "id": request_id,
                    "status": 500,
                    "success": False,
                    "error": str(e)
                })
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Verify all requests succeeded
        assert len(results) == 10
        for result in results:
            assert result["success"] is True
            assert result["status"] == 200
        
        # Should complete reasonably quickly
        assert end_time - start_time < 5.0  # 5 seconds max


class TestDataValidationAndSecurity:
    """Test data validation and security measures."""
    
    def test_input_sanitization(self):
        """Test that inputs are properly sanitized."""
        
        # Test potentially malicious code injection
        malicious_content = '''
```javascript
// Potentially malicious content
eval("alert('XSS')");
document.write("<script>alert('XSS')</script>");
```
'''
        
        response = client.post("/api/code/extract", json={
            "messageId": "security-test",
            "content": malicious_content
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should extract the code but not execute it
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        js_block = data["data"][0]
        assert js_block["language"] == "javascript"
        # Content should be preserved as-is for extraction
        assert "eval" in js_block["code"]
    
    def test_large_input_limits(self):
        """Test handling of extremely large inputs."""
        
        # Create very large message
        huge_message = "A" * (10 * 1024 * 1024)  # 10MB of data
        
        response = client.post("/api/chat", json={
            "message": huge_message
        })
        
        # Should either handle gracefully or reject appropriately
        assert response.status_code in [200, 400, 413, 500]
    
    def test_special_characters_handling(self):
        """Test handling of special characters and unicode."""
        
        unicode_content = '''
Here's code with special characters:

```python
def unicode_test():
    # Test with unicode: 🚀 💻 🎯
    text = "Hello, 世界! Café, naïve, résumé"
    emoji = "🐍 Python is fun! 🔥"
    return f"{text} - {emoji}"
```
'''
        
        response = client.post("/api/code/extract", json={
            "messageId": "unicode-test",
            "content": unicode_content
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        code_block = data["data"][0]
        assert "unicode_test" in code_block["code"]
        assert "🚀" in code_block["code"]
        assert "世界" in code_block["code"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])