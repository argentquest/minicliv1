"""
Command definitions for Code Chat AI startup options.

This module defines all available startup commands with their descriptions,
categories, and execution details.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
import os
import sys
import subprocess


@dataclass
class StartupCommand:
    """Represents a startup command with metadata."""
    id: str
    name: str
    description: str
    category: str
    command: str
    args: List[str] = None
    environment_vars: Dict[str, str] = None
    requires_env: bool = False
    icon: str = "🚀"
    priority: int = 0  # Higher priority = shown first in category

    def get_full_command(self) -> List[str]:
        """Get the full command as a list for subprocess execution."""
        cmd = [sys.executable, self.command]
        if self.args:
            cmd.extend(self.args)
        return cmd

    def can_run(self) -> bool:
        """Check if this command can be executed."""
        if self.requires_env:
            # Check if required environment variables are set
            required_vars = ['API_KEY', 'DEFAULT_MODEL']
            return all(os.getenv(var) for var in required_vars)
        return True

    def get_status(self) -> str:
        """Get status message for this command."""
        if not self.can_run():
            return "⚠️  Requires environment setup"
        return "✅ Ready to run"


class CommandRegistry:
    """Registry for all available startup commands."""

    def __init__(self):
        self.commands: Dict[str, StartupCommand] = {}
        self.categories: Dict[str, List[str]] = {}
        self._register_commands()

    def _register_commands(self):
        """Register all available startup commands."""

        # GUI Applications
        self._register_command(StartupCommand(
            id="main_gui",
            name="Main GUI Application",
            description="Full-featured desktop GUI with Tkinter - Complete AI chat interface with file analysis",
            category="GUI Applications",
            command="minicli.py",
            icon="🖥️",
            priority=10
        ))

        self._register_command(StartupCommand(
            id="modern_gui",
            name="Modern GUI Launcher",
            description="Enhanced Tkinter GUI launcher with better error handling",
            category="GUI Applications",
            command="modern_main.py",
            icon="🎨",
            priority=9
        ))

        self._register_command(StartupCommand(
            id="enhanced_ui",
            name="Enhanced UI Launcher",
            description="Tkinter GUI with enhanced window visibility and positioning",
            category="GUI Applications",
            command="start_ui.py",
            icon="✨",
            priority=8
        ))

        # Web Applications
        self._register_command(StartupCommand(
            id="web_app",
            name="Web Application (Full)",
            description="Complete web application with FastAPI backend + NiceGUI frontend",
            category="Web Applications",
            command="run_web_app.py",
            icon="🌐",
            priority=10
        ))

        self._register_command(StartupCommand(
            id="web_frontend",
            name="Web Frontend Only",
            description="NiceGUI web frontend (requires backend to be running separately)",
            category="Web Applications",
            command="run_web_app.py",
            args=["--frontend-only"],
            icon="💻",
            priority=8
        ))

        self._register_command(StartupCommand(
            id="web_backend",
            name="Web Backend Only",
            description="FastAPI backend server (for development or separate deployment)",
            category="Web Applications",
            command="run_web_app.py",
            args=["--backend-only"],
            icon="⚙️",
            priority=9
        ))

        # CLI Applications
        self._register_command(StartupCommand(
            id="cli_standard",
            name="Standard CLI",
            description="Command-line interface for batch processing and automation",
            category="CLI Applications",
            command="minicli.py",
            args=["--cli"],
            icon="💻",
            priority=10
        ))

        self._register_command(StartupCommand(
            id="cli_rich",
            name="Rich CLI (Enhanced)",
            description="Beautiful CLI with progress bars, colors, and interactive prompts",
            category="CLI Applications",
            command="minicli.py",
            args=["--rich-cli"],
            icon="🎨",
            priority=9
        ))

        # Server Components
        self._register_command(StartupCommand(
            id="fastapi_server",
            name="FastAPI Server",
            description="Standalone FastAPI backend server for API access",
            category="Server Components",
            command="fastapi_server.py",
            icon="🚀",
            priority=10
        ))

        self._register_command(StartupCommand(
            id="run_server",
            name="Server Runner",
            description="Alternative server launcher with additional configuration",
            category="Server Components",
            command="run_server.py",
            icon="🔧",
            priority=8
        ))

        # Development & Testing
        self._register_command(StartupCommand(
            id="test_fastapi",
            name="FastAPI Tests",
            description="Run FastAPI integration tests and API validation",
            category="Development & Testing",
            command="run_fastapi_tests.py",
            icon="🧪",
            priority=10
        ))

        self._register_command(StartupCommand(
            id="test_cli",
            name="CLI Tests",
            description="Run CLI interface tests and validation",
            category="Development & Testing",
            command="run_fastapi_tests.py",
            args=["--cli-tests"],
            icon="🧪",
            priority=9
        ))

        # Legacy & Special
        self._register_command(StartupCommand(
            id="legacy_chat",
            name="Legacy Chat",
            description="Original chat interface (legacy version)",
            category="Legacy & Special",
            command="codechat-rich.py",
            icon="📜",
            priority=5
        ))

        self._register_command(StartupCommand(
            id="batch_app",
            name="Windows Batch Launcher",
            description="Windows batch file launcher for easy desktop access",
            category="Legacy & Special",
            command="run_app.bat",
            icon="🏁",
            priority=3
        ))

    def _register_command(self, command: StartupCommand):
        """Register a single command."""
        self.commands[command.id] = command

        if command.category not in self.categories:
            self.categories[command.category] = []
        self.categories[command.category].append(command.id)

        # Sort commands within category by priority (descending)
        self.categories[command.category].sort(
            key=lambda cmd_id: self.commands[cmd_id].priority,
            reverse=True
        )

    def get_command(self, command_id: str) -> Optional[StartupCommand]:
        """Get a command by ID."""
        return self.commands.get(command_id)

    def get_commands_by_category(self, category: str) -> List[StartupCommand]:
        """Get all commands in a category."""
        return [self.commands[cmd_id] for cmd_id in self.categories.get(category, [])]

    def get_all_categories(self) -> List[str]:
        """Get all available categories."""
        return list(self.categories.keys())

    def get_all_commands(self) -> List[StartupCommand]:
        """Get all commands sorted by category and priority."""
        all_commands = []
        for category in self.get_all_categories():
            all_commands.extend(self.get_commands_by_category(category))
        return all_commands

    def search_commands(self, query: str) -> List[StartupCommand]:
        """Search commands by name or description."""
        query_lower = query.lower()
        return [
            cmd for cmd in self.get_all_commands()
            if query_lower in cmd.name.lower() or query_lower in cmd.description.lower()
        ]


# Global registry instance
command_registry = CommandRegistry()