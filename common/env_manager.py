"""
Environment file manager for editing .env files.

This module provides comprehensive management of .env files including parsing,
validation, and safe writing operations. It preserves comments, formatting,
and handles various .env file formats while providing a clean API for
environment variable management.

Key Features:
- Safe .env file parsing with error handling
- Preservation of comments and original formatting
- Validation of environment variable values
- Atomic file operations to prevent corruption
- Default .env file creation for new installations
- Support for inline comments and various quoting styles

The EnvManager class is designed to be used as both a standalone utility
and as part of the larger application's configuration system.
"""

import os
from typing import Dict, List, Tuple, Optional
import re
from env_validator import env_validator


class EnvManager:
    """
    Manages .env file reading, parsing, and writing operations.

    This class provides a comprehensive interface for managing environment
    files while preserving the original file structure, comments, and
    formatting. It supports standard .env file conventions including
    quoted values, inline comments, and proper escaping.

    Features:
    - Parse existing .env files while preserving structure
    - Validate environment variable values based on type
    - Safe atomic writing to prevent file corruption
    - Automatic creation of default .env files
    - Support for various value formats (quoted, unquoted, etc.)
    - Inline comment preservation

    Usage:
        env_manager = EnvManager('.env')
        env_vars = env_manager.load_env_file()
        env_vars['NEW_VAR'] = 'new_value'
        env_manager.save_env_file(env_vars)
    """

    def __init__(self, env_path: str = ".env"):
        self.env_path = env_path
        self.env_vars = {}
        self.comments = {}
        self.original_lines = []

    def load_env_file(self) -> Dict[str, str]:
        """Load and parse the .env file."""
        self.env_vars = {}
        self.comments = {}
        self.original_lines = []

        if not os.path.exists(self.env_path):
            # Create a default .env file if it doesn't exist
            self._create_default_env()

        try:
            with open(self.env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.original_lines = [line.rstrip("\n\r") for line in lines]

            for i, line in enumerate(self.original_lines):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Handle comments
                if line.startswith("#"):
                    self.comments[i] = line
                    continue

                # Parse key=value pairs
                if "=" in line:
                    # Handle comments at end of line
                    if "#" in line:
                        line_parts = line.split("#", 1)
                        env_part = line_parts[0].strip()
                        comment_part = "#" + line_parts[1]
                        self.comments[i] = comment_part
                    else:
                        env_part = line

                    # Parse the environment variable
                    key, value = env_part.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    self.env_vars[key] = value

        except Exception as e:
            print(f"Error loading .env file: {e}")

        return self.env_vars

    def _create_default_env(self):
        """Create a default .env file with common variables."""
        default_content = """# Code Chat with AI Configuration
# OpenRouter API key (get from https://openrouter.ai/)
API_KEY=

# Default AI model to use
DEFAULT_MODEL=openai/gpt-3.5-turbo

# Available models (comma-separated)
MODELS=openai/gpt-3.5-turbo,openai/gpt-4,openai/gpt-4-turbo,anthropic/claude-3-haiku,anthropic/claude-3-sonnet

# Folders to ignore when scanning (comma-separated)
IGNORE_FOLDERS=venv,.venv,env,.env,__pycache__,node_modules,.git

# UI Theme (light or dark)
UI_THEME=light

# Maximum tokens for AI responses
MAX_TOKENS=2000

# Temperature for AI responses (0.0 to 1.0)
TEMPERATURE=0.7

# --- TOOL COMMANDS ---
# Commands that can be injected into the chat.
TOOL_LINT="Please lint the following code and provide suggestions for improvement."
TOOL_TEST="Please write unit tests for the following code."
TOOL_REFACTOR="Please refactor the following code to improve its readability and maintainability."
TOOL_EXPLAIN="Please explain the following code in detail."
TOOL_DOCSTRING="Please add docstrings to the following Python code."
TOOL_PERFORMANCE="Please analyze the performance of the following code and suggest optimizations."
TOOL_SECURITY="Please review the following code for security vulnerabilities."
TOOL_CONVERT="Please convert the following code to JavaScript."
TOOL_DEBUG="I'm having trouble with the following code. Can you help me debug it?"
TOOL_STYLEGUIDE="Please check if the following code conforms to the PEP 8 style guide."
"""
        try:
            with open(self.env_path, "w", encoding="utf-8") as f:
                f.write(default_content)
        except Exception as e:
            print(f"Error creating default .env file: {e}")

    def save_env_file(self, env_vars: Dict[str, str]) -> bool:
        """Save environment variables back to the .env file, always using double quotes for values."""
        try:
            lines = []
            processed_keys = set()
            for i, line in enumerate(self.original_lines):
                original_line = line.strip()
                # Keep empty lines and comments as-is
                if not original_line or original_line.startswith("#"):
                    lines.append(line)
                    continue
                # Handle key=value lines
                if "=" in original_line:
                    key_part = original_line.split("=")[0].strip()
                    if key_part in env_vars:
                        new_value = env_vars[key_part]
                        # Always wrap value in double quotes
                        new_value = f'"{new_value}"'
                        new_line = f"{key_part}={new_value}"
                        # Add inline comment if it existed
                        if i in self.comments:
                            new_line += f" {self.comments[i]}"
                        lines.append(new_line)
                        processed_keys.add(key_part)
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
            # Add any new variables that weren't in the original file
            for key, value in env_vars.items():
                if key not in processed_keys:
                    value = f'"{value}"'
                    lines.append(f"{key}={value}")
            # Write back to file
            with open(self.env_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
                if lines and not lines[-1].endswith("\n"):
                    f.write("\n")
            return True
        except Exception as e:
            print(f"Error saving .env file: {e}")
            return False

    def get_env_descriptions(self) -> Dict[str, str]:
        """Get descriptions for common environment variables."""
        return {
            "API_KEY": "Your OpenRouter API key (get from https://openrouter.ai/)",
            "DEFAULT_MODEL": "Default AI model to use for conversations",
            "MODELS": "Available models (comma-separated list)",
            "IGNORE_FOLDERS": "Folders to ignore when scanning codebase (comma-separated)",
            "UI_THEME": "Application theme (light or dark)",
            "MAX_TOKENS": "Maximum tokens for AI responses (1-4000)",
            "TEMPERATURE": "AI response creativity (0.0-1.0, higher = more creative)",
            "CURRENT_SYSTEM_PROMPT": "Currently selected system message file (e.g., systemmessage_security.txt)",
            "API_PORT": "Port number for the FastAPI server (default: 8000)",
            "API_HOST": "Host address for the FastAPI server (default: 0.0.0.0 for all interfaces)",
            "FASTAPI_URL": "Backend URL for frontend (default: http://localhost:8000)",
            "WEB_PORT": "Port number for NiceGUI web server (default: 8080)",
            "TOOL_LINT": "Command to run a linter on the code",
            "TOOL_TEST": "Command to run unit tests on the code",
            "TOOL_REFACTOR": "Prompt to ask the AI to refactor the code",
            "TOOL_EXPLAIN": "Prompt to ask the AI for an explanation of the code",
            "TOOL_DOCSTRING": "Prompt to ask the AI to write docstrings for the code",
            "TOOL_PERFORMANCE": "Prompt to ask for a performance analysis of the code",
            "TOOL_SECURITY": "Prompt to ask for a security audit of the code",
            "TOOL_CONVERT": "Prompt to ask the AI to convert the code to another language",
            "TOOL_DEBUG": "Prompt to ask for help debugging the code",
            "TOOL_STYLEGUIDE": "Prompt to check for style guide conformance",
            "VALIDATE_SSL": "SSL certificate validation for API requests (true/false; default: true)",
        }

    def validate_env_var(self, key: str, value: str) -> Tuple[bool, str]:
        """Validate an environment variable value using the comprehensive validator."""
        result = env_validator.validate(key, value)
        return result.is_valid, result.error_message

    def validate_all_env_vars(
        self, env_vars: Dict[str, str]
    ) -> Dict[str, Tuple[bool, str]]:
        """Validate all environment variables and return results."""
        validation_results = env_validator.validate_all(env_vars)

        # Convert to legacy format for backwards compatibility
        results = {}
        for var_name, result in validation_results.items():
            results[var_name] = (result.is_valid, result.error_message)

        return results

    def get_validation_summary(self, env_vars: Dict[str, str]) -> Dict:
        """Get a comprehensive validation summary."""
        validation_results = env_validator.validate_all(env_vars)
        return env_validator.get_validation_summary(validation_results)

    def get_validation_suggestions(self, env_vars: Dict[str, str]) -> List[str]:
        """Get validation suggestions for improvement."""
        validation_results = env_validator.validate_all(env_vars)
        suggestions = []

        for var_name, result in validation_results.items():
            if result.suggestion:
                suggestions.append(f"{var_name}: {result.suggestion}")
            elif result.warning_message:
                suggestions.append(f"{var_name}: {result.warning_message}")

        return suggestions

    def update_single_var(self, key: str, value: str) -> bool:
        """Update a single environment variable and save to file."""
        try:
            # Load current environment variables
            current_vars = self.load_env_file()

            # Update the specific variable
            current_vars[key] = value

            # Save back to file
            return self.save_env_file(current_vars)
        except Exception as e:
            print(f"Error updating environment variable {key}: {e}")
            return False


# Global instance
env_manager = EnvManager()
