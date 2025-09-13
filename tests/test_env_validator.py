"""
Unit tests for environment variable validation.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from env_validator import EnvValidator, ValidationResult, ValidationRule, env_validator


class TestValidationRule:
    """Test cases for ValidationRule dataclass."""
    
    def test_validation_rule_creation(self):
        """Test ValidationRule creation."""
        def dummy_validator(value):
            return True, ""
        
        rule = ValidationRule(
            validator=dummy_validator,
            description="Test rule",
            category="test",
            required=True
        )
        
        assert rule.validator == dummy_validator
        assert rule.description == "Test rule"
        assert rule.category == "test"
        assert rule.required is True


class TestValidationResult:
    """Test cases for ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(
            is_valid=False,
            error_message="Test error",
            warning_message="Test warning",
            suggestion="Test suggestion",
            category="test"
        )
        
        assert result.is_valid is False
        assert result.error_message == "Test error"
        assert result.warning_message == "Test warning"
        assert result.suggestion == "Test suggestion"
        assert result.category == "test"


class TestEnvValidator:
    """Test cases for EnvValidator class."""
    
    def test_initialization(self):
        """Test validator initialization."""
        validator = EnvValidator()
        
        assert len(validator.rules) > 0
        assert len(validator.categories) > 0
        assert 'API_KEY' in validator.rules
        assert 'api' in validator.categories
    
    def test_add_custom_rule(self):
        """Test adding custom validation rules."""
        validator = EnvValidator()
        
        def custom_validator(value):
            return value == "test", "Value must be 'test'"
        
        validator.add_rule("CUSTOM_VAR", custom_validator, "Custom test variable", "custom")
        
        assert "CUSTOM_VAR" in validator.rules
        assert "custom" in validator.categories
        
        # Test the custom rule
        result = validator.validate("CUSTOM_VAR", "test")
        assert result.is_valid is True
        
        result = validator.validate("CUSTOM_VAR", "wrong")
        assert result.is_valid is False
        assert result.error_message == "Value must be 'test'"
    
    def test_validate_unknown_variable(self):
        """Test validation of unknown environment variable."""
        validator = EnvValidator()
        
        result = validator.validate("UNKNOWN_VAR", "some_value")
        
        assert result.is_valid is True  # Unknown vars are allowed with warning
        assert "Unknown environment variable" in result.warning_message
    
    def test_validate_required_empty(self):
        """Test validation of required but empty variables."""
        validator = EnvValidator()
        
        result = validator.validate("API_KEY", "")
        
        assert result.is_valid is False
        assert "required but empty" in result.error_message
        assert result.suggestion
    
    def test_validate_optional_empty(self):
        """Test validation of optional empty variables."""
        validator = EnvValidator()
        
        result = validator.validate("TEMPERATURE", "")
        
        assert result.is_valid is True  # Optional variables can be empty
    
    def test_api_key_validation(self):
        """Test API key validation."""
        validator = EnvValidator()
        
        # Valid key
        result = validator.validate("API_KEY", "sk-abc123def456ghi789")
        assert result.is_valid is True
        
        # Too short
        result = validator.validate("API_KEY", "short")
        assert result.is_valid is False
        assert "too short" in result.error_message
        
        # Placeholder
        result = validator.validate("API_KEY", "test")
        assert result.is_valid is False
        assert "Please replace placeholder" in result.error_message
    
    def test_openrouter_key_validation(self):
        """Test OpenRouter specific key validation."""
        validator = EnvValidator()
        
        # Valid OpenRouter key
        result = validator.validate("OPENROUTER_API_KEY", "sk-or-abc123def456789")
        assert result.is_valid is True
        
        # Wrong prefix
        result = validator.validate("OPENROUTER_API_KEY", "sk-abc123def456")
        assert result.is_valid is False
        assert "sk-or-" in result.error_message
        
        # Empty (optional)
        result = validator.validate("OPENROUTER_API_KEY", "")
        assert result.is_valid is True
    
    def test_model_name_validation(self):
        """Test AI model name validation."""
        validator = EnvValidator()
        
        # Valid model
        result = validator.validate("DEFAULT_MODEL", "openai/gpt-4")
        assert result.is_valid is True
        
        # Missing provider
        result = validator.validate("DEFAULT_MODEL", "gpt-4")
        assert result.is_valid is False
        assert "provider" in result.error_message
        
        # Invalid format
        result = validator.validate("DEFAULT_MODEL", "openai/")
        assert result.is_valid is False
        assert "format" in result.error_message
    
    def test_model_list_validation(self):
        """Test model list validation."""
        validator = EnvValidator()
        
        # Valid list
        result = validator.validate("MODELS", "openai/gpt-3.5-turbo,openai/gpt-4,anthropic/claude-3-sonnet")
        assert result.is_valid is True
        
        # Empty list
        result = validator.validate("MODELS", "")
        assert result.is_valid is False
        assert "empty" in result.error_message
        
        # Invalid model in list
        result = validator.validate("MODELS", "openai/gpt-4,invalid-model")
        assert result.is_valid is False
        assert "invalid-model" in result.error_message
    
    def test_numeric_range_validation(self):
        """Test numeric range validation."""
        validator = EnvValidator()
        
        # Valid tokens
        result = validator.validate("MAX_TOKENS", "2000")
        assert result.is_valid is True
        
        # Too high
        result = validator.validate("MAX_TOKENS", "50000")
        assert result.is_valid is False
        assert "between" in result.error_message
        
        # Not a number
        result = validator.validate("MAX_TOKENS", "not_a_number")
        assert result.is_valid is False
        assert "integer" in result.error_message
        
        # Valid temperature
        result = validator.validate("TEMPERATURE", "0.7")
        assert result.is_valid is True
        
        # Out of range temperature
        result = validator.validate("TEMPERATURE", "2.5")
        assert result.is_valid is False
        assert "between" in result.error_message
    
    def test_enum_validation(self):
        """Test enum validation."""
        validator = EnvValidator()
        
        # Valid theme
        result = validator.validate("UI_THEME", "dark")
        assert result.is_valid is True
        
        result = validator.validate("UI_THEME", "light")
        assert result.is_valid is True
        
        result = validator.validate("UI_THEME", "auto")
        assert result.is_valid is True
        
        # Invalid theme
        result = validator.validate("UI_THEME", "purple")
        assert result.is_valid is False
        assert "one of" in result.error_message
    
    def test_window_size_validation(self):
        """Test window size validation."""
        validator = EnvValidator()
        
        # Valid size
        result = validator.validate("WINDOW_SIZE", "1200x800")
        assert result.is_valid is True
        
        # Invalid format
        result = validator.validate("WINDOW_SIZE", "1200-800")
        assert result.is_valid is False
        assert "format" in result.error_message
        
        # Too small
        result = validator.validate("WINDOW_SIZE", "50x50")
        assert result.is_valid is False
        assert "at least" in result.error_message
        
        # Empty (optional)
        result = validator.validate("WINDOW_SIZE", "")
        assert result.is_valid is True
    
    def test_folder_list_validation(self):
        """Test folder list validation."""
        validator = EnvValidator()
        
        # Valid folders
        result = validator.validate("IGNORE_FOLDERS", "venv,.venv,node_modules,__pycache__")
        assert result.is_valid is True
        
        # Invalid characters
        result = validator.validate("IGNORE_FOLDERS", "folder<with>bad:chars")
        assert result.is_valid is False
        assert "invalid characters" in result.error_message
        
        # Path traversal
        result = validator.validate("IGNORE_FOLDERS", "../evil_folder")
        assert result.is_valid is False
        assert "traversal" in result.error_message
    
    def test_extension_list_validation(self):
        """Test file extension list validation."""
        validator = EnvValidator()
        
        # Valid extensions
        result = validator.validate("SUPPORTED_EXTENSIONS", ".py,.js,.ts,.java")
        assert result.is_valid is True
        
        # Missing dot
        result = validator.validate("SUPPORTED_EXTENSIONS", "py,js")
        assert result.is_valid is False
        assert "start with a dot" in result.error_message
        
        # Invalid characters
        result = validator.validate("SUPPORTED_EXTENSIONS", ".py#$%")
        assert result.is_valid is False
        assert "invalid characters" in result.error_message
    
    def test_system_prompt_file_validation(self, temp_dir):
        """Test system prompt file validation."""
        validator = EnvValidator()
        
        # Create valid file
        prompt_file = Path(temp_dir) / "systemmessage_test.txt"
        prompt_file.write_text("You are a helpful assistant.")
        
        result = validator.validate("CURRENT_SYSTEM_PROMPT", str(prompt_file))
        assert result.is_valid is True
        
        # Non-existent file
        result = validator.validate("CURRENT_SYSTEM_PROMPT", "/nonexistent/file.txt")
        assert result.is_valid is False
        assert "not found" in result.error_message
        
        # Wrong extension
        wrong_ext_file = Path(temp_dir) / "systemmessage.json"
        wrong_ext_file.write_text("{}")
        
        result = validator.validate("CURRENT_SYSTEM_PROMPT", str(wrong_ext_file))
        assert result.is_valid is False
        assert ".txt extension" in result.error_message
    
    def test_tool_command_validation(self):
        """Test tool command validation."""
        validator = EnvValidator()
        
        # Valid command
        result = validator.validate("TOOL_LINT", "Please analyze this code for style issues and provide suggestions.")
        assert result.is_valid is True
        
        # Too short
        result = validator.validate("TOOL_LINT", "Lint")
        assert result.is_valid is False
        assert "too short" in result.error_message
        
        # Too long
        long_command = "Please " + "very " * 100 + "long command"
        result = validator.validate("TOOL_LINT", long_command)
        assert result.is_valid is False
        assert "very long" in result.error_message
        
        # Poor phrasing
        result = validator.validate("TOOL_LINT", "Code bad make good now")
        assert result.is_valid is False
        assert "request or instruction" in result.error_message
    
    def test_validate_all(self):
        """Test validation of all variables."""
        validator = EnvValidator()
        
        env_vars = {
            'API_KEY': 'sk-test123456789',
            'DEFAULT_MODEL': 'openai/gpt-4',
            'MAX_TOKENS': '2000',
            'TEMPERATURE': '0.7',
            'UI_THEME': 'dark',
            'MODELS': 'openai/gpt-3.5-turbo,openai/gpt-4'
        }
        
        results = validator.validate_all(env_vars)
        
        # All should be valid
        assert all(result.is_valid for result in results.values())
        assert len(results) == len(env_vars)
    
    def test_validate_all_with_missing_required(self):
        """Test validation with missing required variables."""
        validator = EnvValidator()
        
        env_vars = {
            'TEMPERATURE': '0.7',  # Missing required API_KEY and others
        }
        
        results = validator.validate_all(env_vars)
        
        # Should include results for missing required vars
        assert 'API_KEY' in results
        assert not results['API_KEY'].is_valid
        assert "missing" in results['API_KEY'].error_message
    
    def test_validation_summary(self):
        """Test validation summary generation."""
        validator = EnvValidator()
        
        env_vars = {
            'API_KEY': 'sk-test123456789',  # Valid
            'DEFAULT_MODEL': 'invalid-model',  # Invalid
            'MAX_TOKENS': 'not_a_number',  # Invalid
            'UNKNOWN_VAR': 'value'  # Warning
        }
        
        results = validator.validate_all(env_vars)
        summary = validator.get_validation_summary(results)
        
        assert summary['total_vars'] > 0
        assert summary['invalid_vars'] >= 2  # At least the 2 invalid ones
        assert summary['warnings'] >= 1  # Unknown variable
        assert len(summary['errors_by_category']) > 0
        assert 'DEFAULT_MODEL' in summary['critical_errors'] or 'MODELS' in summary['critical_errors']  # Invalid required vars
    
    def test_get_rules_by_category(self):
        """Test getting rules by category."""
        validator = EnvValidator()
        
        api_rules = validator.get_rules_by_category('api')
        assert 'API_KEY' in api_rules
        assert 'PROVIDER' in api_rules
        
        ui_rules = validator.get_rules_by_category('ui')
        assert 'UI_THEME' in ui_rules
        
        # Non-existent category
        empty_rules = validator.get_rules_by_category('nonexistent')
        assert len(empty_rules) == 0
    
    def test_get_categories(self):
        """Test getting all categories."""
        validator = EnvValidator()
        
        categories = validator.get_categories()
        
        assert isinstance(categories, list)
        assert 'api' in categories
        assert 'ui' in categories
        assert 'models' in categories
        assert len(categories) > 5
    
    def test_suggestion_generation(self):
        """Test suggestion generation for common errors."""
        validator = EnvValidator()
        
        # API key suggestion
        result = validator.validate("API_KEY", "")
        assert "OpenRouter" in result.suggestion
        
        # Model format suggestion
        result = validator.validate("DEFAULT_MODEL", "gpt-4")
        assert "provider/model" in result.suggestion
        
        # Temperature range suggestion
        result = validator.validate("TEMPERATURE", "5.0")
        assert ("range" in result.suggestion or "0.7 for balanced" in result.suggestion)


class TestGlobalValidator:
    """Test cases for the global validator instance."""
    
    def test_global_instance_available(self):
        """Test that global validator instance is available."""
        assert env_validator is not None
        assert isinstance(env_validator, EnvValidator)
        assert len(env_validator.rules) > 0
    
    def test_global_instance_functionality(self):
        """Test basic functionality of global validator."""
        result = env_validator.validate("API_KEY", "sk-test123456789")
        assert isinstance(result, ValidationResult)
        
        results = env_validator.validate_all({'API_KEY': 'sk-test123'})
        assert isinstance(results, dict)
        assert 'API_KEY' in results


class TestValidationIntegration:
    """Integration tests for environment validation."""
    
    def test_complete_env_validation_workflow(self, temp_dir):
        """Test complete validation workflow."""
        validator = EnvValidator()
        
        # Create system prompt file for testing
        prompt_file = Path(temp_dir) / "systemmessage_security.txt"
        prompt_file.write_text("You are a security expert.")
        
        # Test environment variables
        env_vars = {
            'API_KEY': 'sk-or-1234567890abcdef',
            'OPENROUTER_API_KEY': 'sk-or-abcdef1234567890123',
            'PROVIDER': 'openrouter',
            'DEFAULT_MODEL': 'openai/gpt-4',
            'MODELS': 'openai/gpt-3.5-turbo,openai/gpt-4,anthropic/claude-3-sonnet',
            'MAX_TOKENS': '4000',
            'TEMPERATURE': '0.7',
            'TOP_P': '0.9',
            'UI_THEME': 'dark',
            'WINDOW_SIZE': '1200x800',
            'IGNORE_FOLDERS': 'venv,.venv,node_modules,__pycache__',
            'SUPPORTED_EXTENSIONS': '.py,.js,.ts,.java,.cpp',
            'CURRENT_SYSTEM_PROMPT': str(prompt_file),
            'LOG_LEVEL': 'INFO',
            'CACHE_SIZE': '100',
            'REQUEST_TIMEOUT': '30',
            'TOOL_LINT': 'Please analyze this code for style issues.',
            'TOOL_SECURITY': 'Please review this code for security vulnerabilities.'
        }
        
        # Validate all variables
        results = validator.validate_all(env_vars)
        
        # Check that all are valid
        invalid_results = {k: v for k, v in results.items() if not v.is_valid}
        assert len(invalid_results) == 0, f"Invalid results: {invalid_results}"
        
        # Get summary
        summary = validator.get_validation_summary(results)
        assert summary['invalid_vars'] == 0
        assert summary['total_vars'] > 15
        assert len(summary['errors_by_category']) == 0
    
    def test_validation_with_multiple_errors(self):
        """Test validation with multiple error types."""
        validator = EnvValidator()
        
        problematic_env_vars = {
            'API_KEY': 'test',  # Placeholder
            'DEFAULT_MODEL': 'gpt-4',  # Missing provider
            'MAX_TOKENS': 'unlimited',  # Not a number
            'TEMPERATURE': '5.0',  # Out of range
            'UI_THEME': 'rainbow',  # Invalid option
            'WINDOW_SIZE': '50x50',  # Too small
            'IGNORE_FOLDERS': '../evil',  # Path traversal
            'SUPPORTED_EXTENSIONS': 'py,js',  # Missing dots
            'TOOL_LINT': 'Fix',  # Too short
            'UNKNOWN_SETTING': 'value'  # Unknown variable
        }
        
        results = validator.validate_all(problematic_env_vars)
        summary = validator.get_validation_summary(results)
        
        # Should have multiple errors across categories
        assert summary['invalid_vars'] > 5
        assert len(summary['errors_by_category']) > 3
        assert len(summary['suggestions']) > 5
        assert summary['warnings'] >= 1  # Unknown variable
    
    def test_performance_with_large_env_set(self):
        """Test validator performance with large environment set."""
        validator = EnvValidator()
        
        # Create large environment variable set
        large_env_vars = {}
        
        # Add many tool commands
        for i in range(50):
            large_env_vars[f'TOOL_CUSTOM_{i}'] = f'Please analyze this code for issue type {i}.'
        
        # Add other variables
        large_env_vars.update({
            'API_KEY': 'sk-test123456789',
            'DEFAULT_MODEL': 'openai/gpt-4',
            'MODELS': ','.join([f'provider{i}/model{j}' for i in range(3) for j in range(5)]),
            'MAX_TOKENS': '2000',
            'TEMPERATURE': '0.7'
        })
        
        # Validate all (should be reasonably fast)
        import time
        start_time = time.time()
        results = validator.validate_all(large_env_vars)
        end_time = time.time()
        
        # Should complete quickly (within 1 second)
        assert end_time - start_time < 1.0
        assert len(results) >= 55  # All variables processed
    
    def test_custom_rule_integration(self):
        """Test integration of custom validation rules."""
        validator = EnvValidator()
        
        # Add custom rule for database URL
        def validate_db_url(value):
            if not value.startswith(('postgresql://', 'mysql://', 'sqlite://')):
                return False, "Database URL must start with postgresql://, mysql://, or sqlite://"
            return True, ""
        
        validator.add_rule('DATABASE_URL', validate_db_url, 
                         "Database connection URL", "database", required=False)
        
        # Test custom rule
        result = validator.validate('DATABASE_URL', 'postgresql://user:pass@localhost/db')
        assert result.is_valid is True
        
        result = validator.validate('DATABASE_URL', 'invalid://url')
        assert result.is_valid is False
        assert "postgresql" in result.error_message
        
        # Verify it's included in category listing
        db_rules = validator.get_rules_by_category('database')
        assert 'DATABASE_URL' in db_rules
        assert 'database' in validator.get_categories()