"""
Unit tests for the CLI interface.
"""
import pytest
import argparse
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from io import StringIO
import sys

from cli_interface import CLIInterface


class TestCLIInterface:
    """Test cases for CLIInterface class."""
    
    def test_init(self):
        """Test CLI interface initialization."""
        cli = CLIInterface()
        assert cli.scanner is not None
        assert cli.ai_processor is None
        assert cli.verbose is False
    
    def test_setup_argument_parser(self):
        """Test argument parser setup."""
        cli = CLIInterface()
        parser = cli.setup_argument_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        
        # Test parsing valid CLI arguments
        with patch('sys.argv', ['minicli.py', '--cli', '--folder', './src', '--question', 'test']):
            args = parser.parse_args(['--cli', '--folder', './src', '--question', 'test'])
            
            assert args.cli is True
            assert args.folder == './src'
            assert args.question == 'test'
            assert args.output == 'structured'  # default
            assert args.verbose is False
    
    def test_argument_parser_with_all_options(self):
        """Test argument parser with all options."""
        cli = CLIInterface()
        parser = cli.setup_argument_parser()
        
        args = parser.parse_args([
            '--cli',
            '--folder', './src',
            '--question', 'What does this code do?',
            '--api-key', 'sk-test123',
            '--model', 'gpt-4',
            '--provider', 'openrouter',
            '--system-prompt', 'security_expert',
            '--include', '*.py,*.js',
            '--exclude', 'test_*',
            '--output', 'json',
            '--save-to', 'output.json',
            '--verbose'
        ])
        
        assert args.cli is True
        assert args.folder == './src'
        assert args.question == 'What does this code do?'
        assert args.api_key == 'sk-test123'
        assert args.model == 'gpt-4'
        assert args.provider == 'openrouter'
        assert args.system_prompt == 'security_expert'
        assert args.include == '*.py,*.js'
        assert args.exclude == 'test_*'
        assert args.output == 'json'
        assert args.save_to == 'output.json'
        assert args.verbose is True
    
    def test_log_verbose_mode(self, capsys):
        """Test logging in verbose mode."""
        cli = CLIInterface()
        cli.verbose = True
        
        cli.log("Test message")
        captured = capsys.readouterr()
        assert "[CLI] Test message" in captured.err
    
    def test_log_quiet_mode(self, capsys):
        """Test logging in quiet mode."""
        cli = CLIInterface()
        cli.verbose = False
        
        cli.log("Test message")
        captured = capsys.readouterr()
        assert captured.err == ""
    
    def test_log_force_message(self, capsys):
        """Test forced logging regardless of verbose mode."""
        cli = CLIInterface()
        cli.verbose = False
        
        cli.log("Forced message", force=True)
        captured = capsys.readouterr()
        assert "[CLI] Forced message" in captured.err
    
    @patch.dict('os.environ', {
        'API_KEY': 'sk-env123',
        'PROVIDER': 'tachyon',
        'DEFAULT_MODEL': 'gpt-3.5-turbo',
        'MODELS': 'model1,model2,model3'
    })
    def test_load_configuration_from_env(self):
        """Test loading configuration from environment."""
        cli = CLIInterface()
        
        # Mock args with no CLI overrides
        args = Mock()
        args.api_key = None
        args.provider = None
        args.model = None
        
        config = cli.load_configuration(args)
        
        assert config['api_key'] == 'sk-env123'
        assert config['provider'] == 'tachyon'
        assert config['model'] == 'gpt-3.5-turbo'
        assert 'model1' in config['models']
        assert 'model2' in config['models']
    
    def test_load_configuration_cli_overrides(self):
        """Test CLI arguments overriding environment variables."""
        cli = CLIInterface()
        
        # Mock args with CLI overrides
        args = Mock()
        args.api_key = 'sk-cli456'
        args.provider = 'openrouter'
        args.model = 'gpt-4'
        
        with patch.dict('os.environ', {
            'API_KEY': 'sk-env123',
            'PROVIDER': 'tachyon',
            'DEFAULT_MODEL': 'gpt-3.5-turbo'
        }):
            config = cli.load_configuration(args)
        
        assert config['api_key'] == 'sk-cli456'  # CLI override
        assert config['provider'] == 'openrouter'  # CLI override
        assert config['model'] == 'gpt-4'  # CLI override
    
    def test_setup_ai_processor_success(self):
        """Test successful AI processor setup."""
        cli = CLIInterface()
        
        config = {
            'api_key': 'sk-test123',
            'provider': 'openrouter'
        }
        
        with patch('cli_interface.AIProcessor') as mock_ai_processor_class:
            mock_processor = Mock()
            mock_processor.validate_api_key.return_value = True
            mock_ai_processor_class.return_value = mock_processor
            
            result = cli.setup_ai_processor(config)
            
            assert result is True
            assert cli.ai_processor == mock_processor
            mock_ai_processor_class.assert_called_once_with('sk-test123', 'openrouter')
    
    def test_setup_ai_processor_invalid_key(self, capsys):
        """Test AI processor setup with invalid API key."""
        cli = CLIInterface()
        
        config = {
            'api_key': '',
            'provider': 'openrouter'
        }
        
        with patch('cli_interface.AIProcessor') as mock_ai_processor_class:
            mock_processor = Mock()
            mock_processor.validate_api_key.return_value = False
            mock_ai_processor_class.return_value = mock_processor
            
            result = cli.setup_ai_processor(config)
            
            assert result is False
            captured = capsys.readouterr()
            assert "No API key configured" in captured.err
    
    def test_setup_system_prompt_default(self):
        """Test setup with default system prompt."""
        cli = CLIInterface()
        
        result = cli.setup_system_prompt(None)
        assert result is True
    
    def test_setup_system_prompt_custom(self):
        """Test setup with custom system prompt."""
        cli = CLIInterface()
        
        with patch('os.path.exists', return_value=True):
            with patch('cli_interface.system_message_manager') as mock_manager:
                mock_manager.set_current_system_message_file.return_value = True
                
                result = cli.setup_system_prompt('security_expert')
                
                assert result is True
                mock_manager.set_current_system_message_file.assert_called_once_with('systemmessage_security_expert.txt')
    
    def test_setup_system_prompt_file_not_found(self, capsys):
        """Test setup with non-existent system prompt file."""
        cli = CLIInterface()
        
        with patch('os.path.exists', return_value=False):
            result = cli.setup_system_prompt('nonexistent')
            
            assert result is False
            captured = capsys.readouterr()
            assert "not found" in captured.err
    
    def test_apply_file_filters_include_only(self):
        """Test file filtering with include patterns only."""
        cli = CLIInterface()
        
        files = [
            '/path/main.py',
            '/path/utils.js',
            '/path/test_main.py',
            '/path/config.json'
        ]
        
        filtered = cli.apply_file_filters(files, '*.py', None)
        
        # Should include both .py files
        assert len(filtered) == 2
        assert any('main.py' in f for f in filtered)
        assert any('test_main.py' in f for f in filtered)
        assert not any('.js' in f for f in filtered)
    
    def test_apply_file_filters_exclude_only(self):
        """Test file filtering with exclude patterns only."""
        cli = CLIInterface()
        
        files = [
            '/path/main.py',
            '/path/test_main.py',
            '/path/test_utils.py',
            '/path/utils.py'
        ]
        
        filtered = cli.apply_file_filters(files, None, 'test_*')
        
        # Should exclude test files
        assert len(filtered) == 2
        assert any('main.py' in f for f in filtered)
        assert any('utils.py' in f for f in filtered)
        assert not any('test_' in f for f in filtered)
    
    def test_apply_file_filters_include_and_exclude(self):
        """Test file filtering with both include and exclude patterns."""
        cli = CLIInterface()
        
        files = [
            '/path/main.py',
            '/path/test_main.py',
            '/path/utils.js',
            '/path/config.json'
        ]
        
        filtered = cli.apply_file_filters(files, '*.py,*.js', 'test_*')
        
        # Should include .py and .js files but exclude test files
        assert len(filtered) == 2
        assert any('main.py' in f for f in filtered)
        assert any('utils.js' in f for f in filtered)
        assert not any('test_main.py' in f for f in filtered)
        assert not any('config.json' in f for f in filtered)
    
    def test_scan_codebase_success(self, temp_dir):
        """Test successful codebase scanning."""
        cli = CLIInterface()
        
        # Create test files
        test_file = Path(temp_dir) / "main.py"
        test_file.write_text("print('Hello, World!')")
        
        with patch.object(cli.scanner, 'validate_directory', return_value=(True, "")):
            with patch.object(cli.scanner, 'scan_directory', return_value=[str(test_file)]):
                with patch.object(cli.scanner, 'get_codebase_content', return_value="# Test content"):
                    
                    files, content = cli.scan_codebase(temp_dir, None, None)
                    
                    assert len(files) == 1
                    assert str(test_file) in files
                    assert content == "# Test content"
    
    def test_scan_codebase_invalid_directory(self, capsys):
        """Test scanning invalid directory."""
        cli = CLIInterface()
        
        with patch.object(cli.scanner, 'validate_directory', return_value=(False, "Directory not found")):
            files, content = cli.scan_codebase('/invalid/path', None, None)
            
            assert files == []
            assert content == ""
            captured = capsys.readouterr()
            assert "Directory not found" in captured.err
    
    def test_process_question_success(self):
        """Test successful question processing."""
        cli = CLIInterface()
        
        # Mock AI processor
        mock_processor = Mock()
        mock_processor.process_question.return_value = "AI response content"
        mock_processor.provider = "openrouter"
        cli.ai_processor = mock_processor
        
        with patch('time.time', side_effect=[100.0, 102.5]):  # Mock timing
            with patch('time.strftime', return_value='2023-01-01 12:00:00'):
                result = cli.process_question("Test question", "Test codebase", "gpt-4")
        
        assert result is not None
        assert result['response'] == "AI response content"
        assert result['model'] == "gpt-4"
        assert result['provider'] == "openrouter"
        assert result['processing_time'] == 2.5
        assert result['timestamp'] == '2023-01-01 12:00:00'
    
    def test_process_question_failure(self, capsys):
        """Test question processing failure."""
        cli = CLIInterface()
        
        # Mock AI processor that raises exception
        mock_processor = Mock()
        mock_processor.process_question.side_effect = Exception("API error")
        cli.ai_processor = mock_processor
        
        result = cli.process_question("Test question", "Test codebase", "gpt-4")
        
        assert result is None
        captured = capsys.readouterr()
        assert "Failed to process question" in captured.err
    
    def test_format_output_structured(self):
        """Test structured output formatting."""
        cli = CLIInterface()
        
        result = {
            'response': 'Test AI response',
            'model': 'gpt-4',
            'provider': 'openrouter',
            'processing_time': 2.5,
            'timestamp': '2023-01-01 12:00:00'
        }
        
        output = cli.format_output(result, 'structured')
        
        assert 'Model: gpt-4' in output
        assert 'Provider: openrouter' in output
        assert 'Time: 2.50s' in output
        assert 'Response:' in output
        assert 'Test AI response' in output
    
    def test_format_output_json(self):
        """Test JSON output formatting."""
        cli = CLIInterface()
        
        result = {
            'response': 'Test AI response',
            'model': 'gpt-4',
            'provider': 'openrouter',
            'processing_time': 2.5,
            'timestamp': '2023-01-01 12:00:00'
        }
        
        output = cli.format_output(result, 'json')
        
        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed['response'] == 'Test AI response'
        assert parsed['model'] == 'gpt-4'
        assert parsed['processing_time'] == 2.5
    
    def test_save_output_success(self, temp_dir):
        """Test successful output saving."""
        cli = CLIInterface()
        
        output_file = Path(temp_dir) / "output.txt"
        result = cli.save_output("Test output content", str(output_file))
        
        assert result is True
        assert output_file.exists()
        assert output_file.read_text() == "Test output content"
    
    def test_save_output_failure(self, capsys):
        """Test output saving failure."""
        cli = CLIInterface()
        
        # Try to save to invalid path
        result = cli.save_output("Test content", "/invalid/path/output.txt")
        
        assert result is False
        captured = capsys.readouterr()
        assert "Failed to save output" in captured.err


class TestCLIIntegration:
    """Integration tests for CLI interface."""
    
    @pytest.mark.integration
    def test_full_cli_workflow_success(self, temp_dir, mock_requests_post):
        """Test complete CLI workflow from start to finish."""
        # Create test files
        test_file = Path(temp_dir) / "main.py"
        test_file.write_text("def hello():\n    return 'Hello, World!'")
        
        # Create system prompt file
        system_prompt_file = Path.cwd() / "systemmessage_test.txt"
        system_prompt_file.write_text("You are a helpful assistant.")
        
        try:
            cli = CLIInterface()
            
            # Mock arguments
            args = Mock()
            args.folder = str(temp_dir)
            args.question = "What does this code do?"
            args.api_key = "sk-test123"
            args.provider = "openrouter"
            args.model = "gpt-4"
            args.system_prompt = "test"
            args.include = None
            args.exclude = None
            args.output = "structured"
            args.save_to = None
            args.verbose = False
            
            # Mock system message manager
            with patch('cli_interface.system_message_manager') as mock_manager:
                mock_manager.set_current_system_message_file.return_value = True
                
                with patch('os.path.exists', return_value=True):
                    exit_code = cli.run_cli(args)
            
            assert exit_code == 0
            
        finally:
            # Cleanup
            if system_prompt_file.exists():
                system_prompt_file.unlink()
    
    def test_cli_workflow_missing_api_key(self, temp_dir, capsys):
        """Test CLI workflow with missing API key."""
        # Create test files
        test_file = Path(temp_dir) / "main.py"
        test_file.write_text("def hello():\n    return 'Hello, World!'")
        
        cli = CLIInterface()
        
        # Mock arguments with no API key
        args = Mock()
        args.folder = str(temp_dir)
        args.question = "What does this code do?"
        args.api_key = None
        args.provider = None
        args.model = None
        args.system_prompt = None
        args.include = None
        args.exclude = None
        args.output = "structured"
        args.save_to = None
        args.verbose = False
        
        with patch.dict('os.environ', {}, clear=True):  # No env variables
            with patch('cli_interface.load_dotenv'):  # Prevent loading .env file
                exit_code = cli.run_cli(args)
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "No API key configured" in captured.err
    
    def test_cli_workflow_invalid_directory(self, capsys):
        """Test CLI workflow with invalid directory."""
        cli = CLIInterface()
        
        args = Mock()
        args.folder = "/nonexistent/directory"
        args.question = "What does this code do?"
        args.api_key = "sk-test123"
        args.provider = "openrouter"
        args.model = "gpt-4"
        args.system_prompt = None
        args.include = None
        args.exclude = None
        args.output = "structured"
        args.save_to = None
        args.verbose = False
        
        exit_code = cli.run_cli(args)
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "does not exist" in captured.err