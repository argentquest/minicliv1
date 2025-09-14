"""
Integration tests for end-to-end workflows.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from models import AppState, ConversationMessage
from file_scanner import CodebaseScanner  
from ai import AIProcessor
from env_manager import EnvManager


class TestEndToEndWorkflows:
    """Integration tests for complete application workflows."""
    
    @pytest.mark.integration
    def test_complete_file_scanning_to_ai_workflow(self, temp_dir, mock_requests_post):
        """Test complete workflow from file scanning to AI processing."""
        # Step 1: Set up test codebase
        test_files = {
            "main.py": "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
            "utils.py": "def helper(x):\n    return x * 2",
            "config.py": "DEBUG = True\nAPI_KEY = 'test'",
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        # Step 2: Scan files
        scanner = CodebaseScanner()
        found_files = scanner.scan_directory(temp_dir)
        
        # Verify files were found
        assert len(found_files) == 3
        assert any('main.py' in f for f in found_files)
        assert any('utils.py' in f for f in found_files)
        
        # Step 3: Get codebase content
        codebase_content = scanner.get_codebase_content(found_files)
        assert "def main():" in codebase_content
        assert "def helper(x):" in codebase_content
        assert "=== File:" in codebase_content  # File separators
        
        # Step 4: Process with AI
        with patch('system_message_manager.system_message_manager') as mock_manager:
            mock_manager.get_system_message.return_value = "You are a helpful assistant."

            from ai import AIProviderFactory
            factory = AIProviderFactory()
            provider = factory.create_provider("openrouter", "test-key")
            processor = AIProcessor(provider)
            
            result = processor.process_question(
                question="Explain what this code does",
                conversation_history=[],
                codebase_content=codebase_content,
                model="gpt-3.5-turbo"
            )
            
            # Verify AI processing worked
            assert result == "Mocked AI response content"
            mock_requests_post.assert_called_once()
    
    @pytest.mark.integration
    def test_conversation_history_persistence_workflow(self, temp_dir):
        """Test saving and loading conversation history."""
        # Step 1: Create conversation history
        app_state = AppState()
        messages = [
            ConversationMessage(role="system", content="You are a helpful assistant."),
            ConversationMessage(role="user", content="What is Python?"),
            ConversationMessage(role="assistant", content="Python is a programming language."),
        ]
        
        for msg in messages:
            app_state.conversation_history.append(msg)
        
        # Step 2: Save history to file
        history_file = Path(temp_dir) / "conversation_history.json"
        history_data = app_state.get_conversation_dict()
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        
        # Step 3: Load history from file
        with open(history_file, 'r', encoding='utf-8') as f:
            loaded_history = json.load(f)
        
        # Step 4: Recreate conversation messages
        loaded_messages = [
            ConversationMessage(role=msg["role"], content=msg["content"])
            for msg in loaded_history
        ]
        
        # Verify history persistence worked
        assert len(loaded_messages) == 3
        assert loaded_messages[0].role == "system"
        assert loaded_messages[1].content == "What is Python?"
        assert loaded_messages[2].role == "assistant"
    
    @pytest.mark.integration
    def test_environment_configuration_workflow(self, temp_dir):
        """Test environment variable configuration and loading."""
        # Step 1: Create .env file
        env_file = Path(temp_dir) / ".env"
        env_content = """# Test environment configuration
API_KEY=sk-test123456
OPENROUTER_API_KEY=sk-or-test789
DEFAULT_MODEL=openai/gpt-4
UI_THEME=dark
MODELS=openai/gpt-3.5-turbo,openai/gpt-4,anthropic/claude-3-sonnet
IGNORE_FOLDERS=venv,node_modules,__pycache__
TOOL_LINT=pylint --disable=all --enable=unused-import
TOOL_TEST=pytest -v --tb=short
"""
        env_file.write_text(env_content)
        
        # Step 2: Load environment variables
        with patch('env_manager.env_manager.load_env_file') as mock_load_env:
            mock_load_env.return_value = {
                'API_KEY': 'sk-test123456',
                'DEFAULT_MODEL': 'openai/gpt-4',
                'UI_THEME': 'dark',
                'MODELS': 'openai/gpt-3.5-turbo,openai/gpt-4,anthropic/claude-3-sonnet',
                'IGNORE_FOLDERS': 'venv,node_modules,__pycache__',
                'TOOL_LINT': 'pylint --disable=all --enable=unused-import',
            }

            with patch('os.getenv') as mock_getenv:
                # Mock environment variable access
                env_vars = {
                    'API_KEY': 'sk-test123456',
                    'DEFAULT_MODEL': 'openai/gpt-4',
                    'UI_THEME': 'dark',
                    'MODELS': 'openai/gpt-3.5-turbo,openai/gpt-4,anthropic/claude-3-sonnet',
                    'IGNORE_FOLDERS': 'venv,node_modules,__pycache__',
                    'TOOL_LINT': 'pylint --disable=all --enable=unused-import',
                }

                def mock_getenv_func(key, default=""):
                    return env_vars.get(key, default)

                mock_getenv.side_effect = mock_getenv_func

                # Step 3: Initialize components with environment config
                scanner = CodebaseScanner()
                from ai import AIProviderFactory
                factory = AIProviderFactory()
                provider = factory.create_provider("openrouter", env_vars['API_KEY'])
                processor = AIProcessor(provider)

                # Verify configuration was applied
                assert processor.api_key == 'sk-test123456'
                assert 'venv' in scanner.ignore_folders
                assert 'node_modules' in scanner.ignore_folders
    
    @pytest.mark.integration
    def test_multi_turn_conversation_workflow(self, mock_requests_post):
        """Test multi-turn conversation maintaining context."""
        # Mock different responses for each turn
        responses = [
            "Python is a high-level programming language.",
            "You can create a function using the 'def' keyword.",
            "Here's an example: def my_function(): pass"
        ]
        
        def mock_response_generator():
            for response in responses:
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "choices": [{"message": {"content": response}}],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
                }
                yield mock_resp
        
        response_iter = iter(mock_response_generator())
        mock_requests_post.side_effect = lambda *args, **kwargs: next(response_iter)
        
        with patch('system_message_manager.system_message_manager') as mock_manager:
            mock_manager.get_system_message.return_value = "You are a helpful assistant."

            from ai import AIProviderFactory
            factory = AIProviderFactory()
            provider = factory.create_provider("openrouter", "test-key")
            processor = AIProcessor(provider)
            app_state = AppState()
            
            # First turn - with codebase context
            result1 = processor.process_question(
                question="What is Python?",
                conversation_history=[msg.to_dict() for msg in app_state.conversation_history],
                codebase_content="# Sample Python code\nprint('Hello')",
                model="gpt-3.5-turbo"
            )
            
            # Add messages to history
            app_state.conversation_history.append(ConversationMessage(role="user", content="What is Python?"))
            app_state.conversation_history.append(ConversationMessage(role="assistant", content=result1))
            
            # Second turn - without codebase context (follow-up)
            result2 = processor.process_question(
                question="How do I create a function?",
                conversation_history=[msg.to_dict() for msg in app_state.conversation_history],
                codebase_content="",  # No new codebase context
                model="gpt-3.5-turbo"
            )
            
            # Add to history
            app_state.conversation_history.append(ConversationMessage(role="user", content="How do I create a function?"))
            app_state.conversation_history.append(ConversationMessage(role="assistant", content=result2))
            
            # Third turn - follow-up question
            result3 = processor.process_question(
                question="Can you show an example?",
                conversation_history=[msg.to_dict() for msg in app_state.conversation_history],
                codebase_content="",
                model="gpt-3.5-turbo"
            )

            # Add third turn to history
            app_state.conversation_history.append(ConversationMessage(role="user", content="Can you show an example?"))
            app_state.conversation_history.append(ConversationMessage(role="assistant", content=result3))

            # Verify all turns worked
            assert result1 == "Python is a high-level programming language."
            assert result2 == "You can create a function using the 'def' keyword."
            assert result3 == "Here's an example: def my_function(): pass"

            # Verify conversation history grew correctly
            assert len(app_state.conversation_history) == 6  # 3 user + 3 assistant messages
    
    @pytest.mark.integration
    def test_provider_switching_workflow(self, mock_requests_post):
        """Test switching between AI providers."""
        from ai import AIProviderFactory
        factory = AIProviderFactory()
        provider = factory.create_provider("openrouter", "test-key")
        processor = AIProcessor(provider)
        
        # Verify initial provider
        assert processor.provider == "openrouter"
        info = processor.get_provider_info()
        assert info["name"] == "openrouter"
        
        # Switch to Tachyon
        processor.set_provider("tachyon")
        assert processor.provider == "tachyon"
        
        # Verify API key was preserved
        assert processor.api_key == "test-key"
        
        # Verify provider info changed
        info = processor.get_provider_info()
        assert info["name"] == "tachyon"
        
        # Test processing with new provider
        with patch('system_message_manager.system_message_manager') as mock_manager:
            mock_manager.get_system_message.return_value = "System message"

            result = processor.process_question(
                question="Test question",
                conversation_history=[],
                codebase_content="test code",
                model="test-model"
            )

            assert result == "Mocked AI response content"
    
    @pytest.mark.integration  
    def test_error_recovery_workflow(self):
        """Test error handling and recovery in various scenarios."""
        # Test 1: Invalid directory handling
        scanner = CodebaseScanner()
        is_valid, error_msg = scanner.validate_directory("/nonexistent/path")
        assert not is_valid
        assert "does not exist" in error_msg
        
        # Test 2: Missing API key handling
        from ai import AIProviderFactory
        factory = AIProviderFactory()
        provider = factory.create_provider("openrouter", "")
        processor = AIProcessor(provider)

        with pytest.raises(Exception) as exc_info:
            processor.process_question(
                question="Test question",
                conversation_history=[],
                codebase_content="test code",
                model="gpt-3.5-turbo"
            )
        assert "API key is not configured" in str(exc_info.value)

        # Test 3: Invalid provider handling
        with pytest.raises(ValueError) as exc_info:
            factory.create_provider("invalid_provider", "test-key")
        assert "Unsupported provider" in str(exc_info.value)
        
        # Test 4: File reading error recovery
        content = scanner.read_file_content("/nonexistent/file.py")
        assert "Error reading file" in content
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_codebase_performance(self, temp_dir):
        """Test performance with larger codebase (marked as slow test)."""
        # Create a moderately large test codebase
        num_files = 50
        file_size_lines = 100
        
        for i in range(num_files):
            file_path = Path(temp_dir) / f"module_{i:02d}.py"
            content_lines = [f"# Module {i} - Line {j}" for j in range(file_size_lines)]
            content_lines.append(f"def function_{i}():")
            content_lines.append(f"    '''Function {i} documentation'''")
            content_lines.append(f"    return {i}")
            
            file_path.write_text("\n".join(content_lines))
        
        # Test file scanning performance
        scanner = CodebaseScanner()
        import time
        
        start_time = time.time()
        found_files = scanner.scan_directory(temp_dir)
        scan_time = time.time() - start_time
        
        # Should find all files relatively quickly
        assert len(found_files) == num_files
        assert scan_time < 5.0  # Should complete within 5 seconds
        
        # Test content reading performance
        start_time = time.time()
        codebase_content = scanner.get_codebase_content(found_files[:10])  # Test with subset
        read_time = time.time() - start_time
        
        # Should read and combine content efficiently
        assert len(codebase_content) > 0
        assert read_time < 2.0  # Should complete within 2 seconds
        assert codebase_content.count("=== File:") == 10  # Should have file separators