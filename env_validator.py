"""
Environment variable validation utilities.
Provides comprehensive validation for configuration values with detailed error messages.
"""
import re
import os
from typing import Dict, List, Tuple, Set, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path
import requests


@dataclass
class ValidationRule:
    """Represents a validation rule for environment variables."""
    validator: Callable[[str], Tuple[bool, str]]
    description: str
    category: str = "general"
    required: bool = False


@dataclass
class ValidationResult:
    """Result of environment variable validation."""
    is_valid: bool
    error_message: str = ""
    warning_message: str = ""
    suggestion: str = ""
    category: str = "general"


class EnvValidator:
    """
    Comprehensive environment variable validator with extensible rules.
    
    Features:
    - Type validation (int, float, bool, enum, regex)
    - Range validation for numeric values
    - URL and API key format validation
    - File path validation
    - Model name validation
    - Custom validation rules
    - Detailed error messages with suggestions
    """
    
    def __init__(self):
        """Initialize validator with predefined rules."""
        self.rules: Dict[str, ValidationRule] = {}
        self.categories: Set[str] = set()
        
        # Initialize with default validation rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default validation rules for common environment variables."""
        
        # API Configuration
        self.add_rule('API_KEY', 
                     self._validate_api_key, 
                     "OpenRouter or other AI API key", 
                     "api", required=True)
        
        self.add_rule('OPENROUTER_API_KEY', 
                     self._validate_openrouter_key,
                     "OpenRouter API key (sk-or-...)", 
                     "api")
        
        self.add_rule('PROVIDER',
                      lambda v: self._validate_enum(v, {'openrouter', 'tachyon', 'custom'}),
                      "AI provider (openrouter, tachyon, custom)",
                      "api")

        self.add_rule('PROVIDERS',
                      self._validate_provider_list,
                      "Comma-separated list of available AI providers",
                      "api")
        
        # Model Configuration
        self.add_rule('DEFAULT_MODEL', 
                     self._validate_model_name,
                     "Default AI model name (e.g., openai/gpt-4)", 
                     "models", required=True)
        
        self.add_rule('MODELS', 
                     self._validate_model_list,
                     "Comma-separated list of available models", 
                     "models", required=True)
        
        # Numeric Parameters
        self.add_rule('MAX_TOKENS', 
                     lambda v: self._validate_int_range(v, 1, 16000),
                     "Maximum tokens for AI responses (1-16000)", 
                     "parameters")
        
        self.add_rule('TEMPERATURE', 
                     lambda v: self._validate_float_range(v, 0.0, 2.0),
                     "AI response temperature (0.0-2.0, higher = more creative)", 
                     "parameters")
        
        self.add_rule('TOP_P', 
                     lambda v: self._validate_float_range(v, 0.0, 1.0),
                     "Top-p nucleus sampling (0.0-1.0)", 
                     "parameters")
        
        self.add_rule('FREQUENCY_PENALTY', 
                     lambda v: self._validate_float_range(v, -2.0, 2.0),
                     "Frequency penalty (-2.0 to 2.0)", 
                     "parameters")
        
        # UI Configuration
        self.add_rule('UI_THEME', 
                     lambda v: self._validate_enum(v, {'light', 'dark', 'auto'}),
                     "Application theme (light, dark, auto)", 
                     "ui")
        
        self.add_rule('WINDOW_SIZE', 
                     self._validate_window_size,
                     "Window size in format WIDTHxHEIGHT (e.g., 1200x800)", 
                     "ui")
        
        # File System Configuration
        self.add_rule('IGNORE_FOLDERS', 
                     self._validate_folder_list,
                     "Folders to ignore when scanning (comma-separated)", 
                     "filesystem")
        
        self.add_rule('SUPPORTED_EXTENSIONS', 
                     self._validate_extension_list,
                     "Supported file extensions (comma-separated, with dots)", 
                     "filesystem")
        
        self.add_rule('MAX_FILE_SIZE', 
                     lambda v: self._validate_int_range(v, 1, 100 * 1024 * 1024),  # 100MB
                     "Maximum file size in bytes", 
                     "filesystem")
        
        # System Message Configuration
        self.add_rule('CURRENT_SYSTEM_PROMPT', 
                     self._validate_system_prompt_file,
                     "Current system message file path", 
                     "system")
        
        # Tool Commands (dynamic validation)
        self._setup_tool_command_rules()
        
        # Advanced Configuration
        self.add_rule('LOG_LEVEL', 
                     lambda v: self._validate_enum(v, {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}),
                     "Logging level", 
                     "advanced")
        
        self.add_rule('CACHE_SIZE', 
                     lambda v: self._validate_int_range(v, 1, 1000),
                     "Cache size for file content (1-1000)", 
                     "advanced")
        
        self.add_rule('REQUEST_TIMEOUT', 
                     lambda v: self._validate_int_range(v, 1, 300),
                     "API request timeout in seconds (1-300)", 
                     "advanced")
        
        # Logging Configuration
        self.add_rule('LOG_LEVEL', 
                     lambda v: self._validate_enum(v, {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}),
                     "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", 
                     "logging")
        
        self.add_rule('LOG_DIR',
                      self._validate_log_directory,
                      "Directory for log files (defaults to 'logs')",
                      "logging")

        # Output Directory Configuration
        self.add_rule('DIR_SAVE',
                      self._validate_save_directory,
                      "Directory for saving analysis results (defaults to 'results')",
                      "output")

        # FastAPI Server Configuration
        self.add_rule('API_PORT',
                       lambda v: self._validate_int_range(v, 1, 65535),
                       "Port number for FastAPI server (1-65535, default: 8000)",
                       "server")

        self.add_rule('API_HOST',
                       self._validate_host_address,
                       "Host address for FastAPI server (IP address or hostname, default: 0.0.0.0)",
                       "server")

        # Web Application Configuration
        self.add_rule('FASTAPI_URL',
                       self._validate_fastapi_url,
                       "Backend URL for frontend (e.g., http://localhost:8000)",
                       "web")

        self.add_rule('WEB_PORT',
                       lambda v: self._validate_int_range(v, 1, 65535),
                       "Port number for NiceGUI web server (1-65535, default: 8080)",
                       "web")
    
    def _setup_tool_command_rules(self):
        """Set up validation rules for tool commands."""
        tool_commands = [
            'TOOL_LINT', 'TOOL_TEST', 'TOOL_REFACTOR', 'TOOL_EXPLAIN',
            'TOOL_DOCSTRING', 'TOOL_PERFORMANCE', 'TOOL_SECURITY',
            'TOOL_CONVERT', 'TOOL_DEBUG', 'TOOL_STYLEGUIDE'
        ]
        
        for tool in tool_commands:
            self.add_rule(tool, 
                         self._validate_tool_command,
                         f"Tool command prompt for {tool.lower().replace('tool_', '')}", 
                         "tools")
    
    def add_rule(self, var_name: str, validator: Callable[[str], Tuple[bool, str]], 
                 description: str, category: str = "general", required: bool = False):
        """Add a custom validation rule."""
        self.rules[var_name] = ValidationRule(validator, description, category, required)
        self.categories.add(category)
    
    def validate(self, var_name: str, value: str) -> ValidationResult:
        """
        Validate a single environment variable.
        
        Args:
            var_name: Environment variable name
            value: Variable value to validate
            
        Returns:
            ValidationResult with detailed information
        """
        if var_name not in self.rules:
            # Unknown variable - return warning
            return ValidationResult(
                is_valid=True,
                warning_message=f"Unknown environment variable: {var_name}",
                suggestion=f"Consider removing {var_name} if it's not needed"
            )
        
        rule = self.rules[var_name]
        
        # Check if required variable is empty
        if rule.required and not value.strip():
            return ValidationResult(
                is_valid=False,
                error_message=f"{var_name} is required but empty",
                suggestion=f"Please set {var_name}. {rule.description}",
                category=rule.category
            )
        
        # Skip validation for empty optional variables
        if not rule.required and not value.strip():
            return ValidationResult(is_valid=True, category=rule.category)
        
        # Run validation
        try:
            is_valid, error_msg = rule.validator(value)
            
            result = ValidationResult(
                is_valid=is_valid,
                error_message=error_msg,
                category=rule.category
            )
            
            # Add suggestions for common errors
            if not is_valid:
                result.suggestion = self._generate_suggestion(var_name, value, error_msg)
            
            return result
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error for {var_name}: {str(e)}",
                category=rule.category
            )
    
    def validate_all(self, env_vars: Dict[str, str]) -> Dict[str, ValidationResult]:
        """Validate all environment variables."""
        results = {}
        
        # Validate provided variables
        for var_name, value in env_vars.items():
            results[var_name] = self.validate(var_name, value)
        
        # Check for missing required variables
        for var_name, rule in self.rules.items():
            if rule.required and var_name not in env_vars:
                results[var_name] = ValidationResult(
                    is_valid=False,
                    error_message=f"Required variable {var_name} is missing",
                    suggestion=f"Please add {var_name}. {rule.description}",
                    category=rule.category
                )
        
        return results
    
    def get_validation_summary(self, results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Get a summary of validation results."""
        summary = {
            'total_vars': len(results),
            'valid_vars': sum(1 for r in results.values() if r.is_valid),
            'invalid_vars': sum(1 for r in results.values() if not r.is_valid),
            'warnings': sum(1 for r in results.values() if r.warning_message),
            'errors_by_category': {},
            'critical_errors': [],
            'suggestions': []
        }
        
        for var_name, result in results.items():
            if not result.is_valid:
                category = result.category
                if category not in summary['errors_by_category']:
                    summary['errors_by_category'][category] = 0
                summary['errors_by_category'][category] += 1
                
                # Critical errors (API keys, required config)
                if result.category in ['api', 'models'] or self.rules.get(var_name, ValidationRule(None, "", "")).required:
                    summary['critical_errors'].append(var_name)
            
            if result.suggestion:
                summary['suggestions'].append(f"{var_name}: {result.suggestion}")
        
        return summary
    
    def get_all_rules(self) -> Dict[str, ValidationRule]:
        """Get all validation rules."""
        return self.rules.copy()
    
    def get_rules_by_category(self, category: str) -> Dict[str, ValidationRule]:
        """Get validation rules for a specific category."""
        return {k: v for k, v in self.rules.items() if v.category == category}
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return sorted(list(self.categories))
    
    # Specific validation methods
    
    def _validate_int_range(self, value: str, min_val: int, max_val: int) -> Tuple[bool, str]:
        """Validate integer within range."""
        try:
            int_val = int(value)
            if int_val < min_val or int_val > max_val:
                return False, f"Value must be between {min_val} and {max_val}"
            return True, ""
        except ValueError:
            return False, "Value must be a valid integer"
    
    def _validate_float_range(self, value: str, min_val: float, max_val: float) -> Tuple[bool, str]:
        """Validate float within range."""
        try:
            float_val = float(value)
            if float_val < min_val or float_val > max_val:
                return False, f"Value must be between {min_val} and {max_val}"
            return True, ""
        except ValueError:
            return False, "Value must be a valid decimal number"
    
    def _validate_enum(self, value: str, valid_values: Set[str]) -> Tuple[bool, str]:
        """Validate value is in allowed set."""
        if value.lower() in {v.lower() for v in valid_values}:
            return True, ""
        return False, f"Value must be one of: {', '.join(sorted(valid_values))}"
    
    def _validate_api_key(self, value: str) -> Tuple[bool, str]:
        """Validate API key format."""
        if not value.strip():
            return False, "API key cannot be empty"
        
        # Check for common test/placeholder values first
        test_values = {'test', 'your_key_here', 'placeholder', 'example', 'dummy'}
        if value.lower() in test_values:
            return False, "Please replace placeholder with actual API key"
        
        if len(value) < 8:
            return False, "API key seems too short"
        
        return True, ""
    
    def _validate_openrouter_key(self, value: str) -> Tuple[bool, str]:
        """Validate OpenRouter specific API key format."""
        if not value.strip():
            return True, ""  # Optional
        
        if not value.startswith('sk-or-'):
            return False, "OpenRouter API keys should start with 'sk-or-'"
        
        if len(value) < 20:
            return False, "OpenRouter API key seems too short"
        
        return True, ""
    
    def _validate_model_name(self, value: str) -> Tuple[bool, str]:
        """Validate AI model name format."""
        if not value.strip():
            return False, "Model name cannot be empty"
        
        # Check for provider/model format
        if '/' not in value:
            return False, "Model name should include provider (e.g., 'openai/gpt-4')"
        
        provider, model = value.split('/', 1)
        if not provider or not model:
            return False, "Invalid model format. Use 'provider/model'"
        
        return True, ""
    
    def _validate_model_list(self, value: str) -> Tuple[bool, str]:
        """Validate comma-separated list of models."""
        if not value.strip():
            return False, "Model list cannot be empty"
        
        models = [m.strip() for m in value.split(',') if m.strip()]
        if not models:
            return False, "No valid models found"
        
        # Validate each model
        for model in models:
            is_valid, error = self._validate_model_name(model)
            if not is_valid:
                return False, f"Invalid model '{model}': {error}"
        
        return True, ""
    
    def _validate_window_size(self, value: str) -> Tuple[bool, str]:
        """Validate window size format (WIDTHxHEIGHT)."""
        if not value.strip():
            return True, ""  # Optional
        
        if 'x' not in value.lower():
            return False, "Window size must be in format 'WIDTHxHEIGHT' (e.g., '1200x800')"
        
        try:
            width_str, height_str = value.lower().split('x', 1)
            width = int(width_str.strip())
            height = int(height_str.strip())
            
            if width < 100 or height < 100:
                return False, "Window dimensions must be at least 100x100"
            
            if width > 5000 or height > 5000:
                return False, "Window dimensions seem unreasonably large"
            
            return True, ""
            
        except (ValueError, IndexError):
            return False, "Invalid window size format. Use 'WIDTHxHEIGHT'"
    
    def _validate_folder_list(self, value: str) -> Tuple[bool, str]:
        """Validate comma-separated folder list."""
        if not value.strip():
            return True, ""  # Optional
        
        folders = [f.strip() for f in value.split(',') if f.strip()]
        
        for folder in folders:
            # Check for invalid characters
            invalid_chars = '<>:"|?*'
            if any(char in folder for char in invalid_chars):
                return False, f"Folder name '{folder}' contains invalid characters"
            
            # Check for relative path traversal
            if '..' in folder or folder.startswith('/'):
                return False, f"Folder name '{folder}' looks like a path traversal attempt"
        
        return True, ""
    
    def _validate_extension_list(self, value: str) -> Tuple[bool, str]:
        """Validate comma-separated file extension list."""
        if not value.strip():
            return True, ""  # Optional
        
        extensions = [ext.strip() for ext in value.split(',') if ext.strip()]
        
        for ext in extensions:
            if not ext.startswith('.'):
                return False, f"Extension '{ext}' should start with a dot (e.g., '.py')"
            
            if len(ext) < 2:
                return False, f"Extension '{ext}' is too short"
            
            # Check for valid characters in extension
            if not re.match(r'^\.[a-zA-Z0-9]+$', ext):
                return False, f"Extension '{ext}' contains invalid characters"
        
        return True, ""
    
    def _validate_system_prompt_file(self, value: str) -> Tuple[bool, str]:
        """Validate system prompt file path."""
        if not value.strip():
            return True, ""  # Optional
        
        # Check if file exists
        if not os.path.exists(value):
            return False, f"System prompt file not found: {value}"
        
        # Check file extension
        if not value.endswith('.txt'):
            return False, "System prompt file should have .txt extension"
        
        # Check if it's a valid system message file
        if not (value.startswith('systemmessage') or 'system' in value.lower()):
            return False, "File name should indicate it's a system message file"
        
        return True, ""
    
    def _validate_tool_command(self, value: str) -> Tuple[bool, str]:
        """Validate tool command prompt."""
        if not value.strip():
            return True, ""  # Optional
        
        if len(value) < 10:
            return False, "Tool command seems too short to be useful"
        
        if len(value) > 500:
            return False, "Tool command is very long, consider shortening it"
        
        # Check for basic prompt structure
        if not any(word in value.lower() for word in ['please', 'help', 'analyze', 'review', 'explain']):
            return False, "Tool command should be phrased as a request or instruction"
        
        return True, ""
    
    def _validate_log_directory(self, value: str) -> Tuple[bool, str]:
        """Validate log directory path."""
        if not value.strip():
            return True, ""  # Optional - will use default

        # Check if path is valid
        try:
            log_path = Path(value)

            # Check for dangerous paths
            if str(log_path).startswith(('/etc', '/root', '/bin', '/usr')):
                return False, "Cannot use system directories for logging"

            # Check if parent directory exists or can be created
            parent = log_path.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    return False, f"Cannot create log directory: {value} (permission denied)"
                except Exception as e:
                    return False, f"Invalid log directory path: {str(e)}"

            return True, ""

        except Exception as e:
            return False, f"Invalid log directory path: {str(e)}"

    def _validate_save_directory(self, value: str) -> Tuple[bool, str]:
        """Validate save directory path for analysis results."""
        if not value.strip():
            return True, ""  # Optional - will use default "results"

        # Check if path is valid
        try:
            save_path = Path(value)

            # Check for dangerous paths
            dangerous_paths = ('/etc', '/root', '/bin', '/usr', '/var', '/tmp')
            if str(save_path).startswith(dangerous_paths):
                return False, "Cannot use system directories for saving results"

            # Check for absolute paths that might be problematic
            if save_path.is_absolute() and len(save_path.parts) < 2:
                return False, "Save directory path seems too short for an absolute path"

            # Check if parent directory exists or can be created
            parent = save_path.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    return False, f"Cannot create save directory: {value} (permission denied)"
                except Exception as e:
                    return False, f"Invalid save directory path: {str(e)}"

            # Try to create the directory itself to test write permissions
            try:
                if not save_path.exists():
                    save_path.mkdir(parents=True, exist_ok=True)
                # Test write permission by trying to create a temporary file
                test_file = save_path / ".write_test"
                test_file.touch()
                test_file.unlink()  # Clean up
            except PermissionError:
                return False, f"No write permission for save directory: {value}"
            except Exception as e:
                return False, f"Cannot write to save directory: {str(e)}"

            return True, ""

        except Exception as e:
            return False, f"Invalid save directory path: {str(e)}"

    def _validate_provider_list(self, value: str) -> Tuple[bool, str]:
        """Validate comma-separated list of AI providers."""
        if not value.strip():
            return False, "Provider list cannot be empty"

        providers = [p.strip() for p in value.split(',') if p.strip()]

        if not providers:
            return False, "No valid providers found in list"

        # Check for valid provider names (should match class names in providers/)
        valid_providers = {'openrouter', 'tachyon', 'custom'}
        invalid_providers = []

        for provider in providers:
            if provider not in valid_providers:
                invalid_providers.append(provider)

        if invalid_providers:
            return False, f"Invalid providers: {', '.join(invalid_providers)}. Valid options: {', '.join(valid_providers)}"

        # Check for duplicates
        if len(providers) != len(set(providers)):
            return False, "Provider list contains duplicates"

        return True, ""

    def _validate_host_address(self, value: str) -> Tuple[bool, str]:
        """Validate host address for FastAPI server."""
        if not value.strip():
            return True, ""  # Optional - will use default

        # Allow localhost, IP addresses, and hostnames
        import ipaddress
        import socket

        # Check if it's a valid IP address
        try:
            ipaddress.ip_address(value)
            return True, ""
        except ValueError:
            pass

        # Check if it's localhost or a valid hostname
        if value.lower() in ['localhost', '127.0.0.1', '::1', '0.0.0.0']:
            return True, ""

        # Try to resolve as hostname
        try:
            socket.gethostbyname(value)
            return True, ""
        except socket.gaierror:
            return False, f"Invalid host address: {value}. Use IP address, localhost, or valid hostname"

    def _validate_fastapi_url(self, value: str) -> Tuple[bool, str]:
        """Validate FastAPI URL for frontend backend connection."""
        if not value.strip():
            return True, ""  # Optional - will use default

        # Check if it's a valid URL
        import re
        from urllib.parse import urlparse

        # Basic URL pattern validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # path

        if not url_pattern.match(value):
            return False, f"Invalid URL format: {value}. Use format like 'http://localhost:8000'"

        # Parse URL to validate components
        try:
            parsed = urlparse(value)

            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False, f"URL must include scheme and host: {value}"

            # Scheme must be http or https
            if parsed.scheme.lower() not in ['http', 'https']:
                return False, f"URL scheme must be http or https: {value}"

            # If port is specified, validate it
            if parsed.port:
                if not (1 <= parsed.port <= 65535):
                    return False, f"Port must be between 1 and 65535: {parsed.port}"

            return True, ""

        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"

    def _generate_suggestion(self, var_name: str, value: str, error_msg: str) -> str:
        """Generate helpful suggestions for common validation errors."""
        suggestions = {
            'API_KEY': "Get your API key from https://openrouter.ai/ and paste it here",
            'DEFAULT_MODEL': "Use format 'provider/model' like 'openai/gpt-4' or 'anthropic/claude-3-sonnet'",
            'MODELS': "List models in format 'provider/model1,provider/model2'",
            'MAX_TOKENS': "Try a value between 1000-4000 for most use cases",
            'TEMPERATURE': "Use 0.7 for balanced creativity, 0.1 for focused responses, 0.9 for creative responses",
            'UI_THEME': "Use 'light', 'dark', or 'auto'",
            'WINDOW_SIZE': "Use format like '1200x800' for a 1200px wide by 800px tall window",
            'LOG_LEVEL': "Use DEBUG for development, INFO for normal operation, WARNING/ERROR for production",
            'LOG_DIR': "Use a relative path like 'logs' or absolute path like '/var/log/minicli'",
            'DIR_SAVE': "Use a relative path like 'results' or 'output' for saving analysis results",
            'API_PORT': "Use port 8000 for development, or any available port between 1024-65535 for production",
            'API_HOST': "Use '0.0.0.0' to accept connections from all interfaces, or '127.0.0.1' for localhost only",
            'FASTAPI_URL': "Use format 'http://localhost:8000' or 'https://your-domain.com:8000' for production",
            'WEB_PORT': "Use port 8080 for development, or any available port between 1024-65535 for production"
        }
        
        if var_name in suggestions:
            return suggestions[var_name]
        
        # Generate generic suggestions based on error patterns
        if "between" in error_msg:
            return f"Choose a value within the specified range for {var_name}"
        elif "format" in error_msg.lower():
            return f"Check the format requirements for {var_name}"
        elif "empty" in error_msg:
            return f"Please provide a value for {var_name}"
        
        return f"Please check the value for {var_name}"


# Global instance for easy access
env_validator = EnvValidator()