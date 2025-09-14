"""
Unit tests for the startcommands module.

This module tests the startcommands functionality including:
- Command registry operations
- Launcher interactive mode
- CLI argument parsing
- Command execution (with mocks)
- Error handling and validation
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, call
from io import StringIO

# Import the startcommands modules
from startcommands.commands import CommandRegistry, StartupCommand
from startcommands.launcher import CommandLauncher
from startcommands.main import create_parser, list_all_commands, show_category_commands, run_specific_command, search_commands


class TestStartupCommand:
    """Test cases for StartupCommand class."""

    def test_init_basic(self):
        """Test basic StartupCommand initialization."""
        cmd = StartupCommand(
            id="test_cmd",
            name="Test Command",
            description="A test command",
            category="Test Category",
            command="test_script.py"
        )

        assert cmd.id == "test_cmd"
        assert cmd.name == "Test Command"
        assert cmd.description == "A test command"
        assert cmd.category == "Test Category"
        assert cmd.command == "test_script.py"
        assert cmd.args is None
        assert cmd.icon == "🚀"
        assert cmd.priority == 0

    def test_init_with_args(self):
        """Test StartupCommand initialization with arguments."""
        cmd = StartupCommand(
            id="test_cmd",
            name="Test Command",
            description="A test command",
            category="Test Category",
            command="test_script.py",
            args=["--arg1", "value1"],
            icon="🎯",
            priority=5
        )

        assert cmd.args == ["--arg1", "value1"]
        assert cmd.icon == "🎯"
        assert cmd.priority == 5

    def test_get_full_command(self):
        """Test get_full_command method."""
        cmd = StartupCommand(
            id="test_cmd",
            name="Test Command",
            description="A test command",
            category="Test Category",
            command="test_script.py",
            args=["--verbose"]
        )

        full_cmd = cmd.get_full_command()
        expected = [sys.executable, "test_script.py", "--verbose"]
        assert full_cmd == expected

    def test_can_run_without_env(self):
        """Test can_run method for commands that don't require environment."""
        cmd = StartupCommand(
            id="test_cmd",
            name="Test Command",
            description="A test command",
            category="Test Category",
            command="test_script.py"
        )

        assert cmd.can_run() is True

    def test_can_run_with_env_missing(self):
        """Test can_run method when environment variables are missing."""
        cmd = StartupCommand(
            id="test_cmd",
            name="Test Command",
            description="A test command",
            category="Test Category",
            command="test_script.py",
            requires_env=True
        )

        with patch.dict(os.environ, {}, clear=True):
            assert cmd.can_run() is False

    def test_can_run_with_env_present(self):
        """Test can_run method when required environment variables are present."""
        cmd = StartupCommand(
            id="test_cmd",
            name="Test Command",
            description="A test command",
            category="Test Category",
            command="test_script.py",
            requires_env=True
        )

        with patch.dict(os.environ, {'API_KEY': 'test_key', 'DEFAULT_MODEL': 'gpt-4'}):
            assert cmd.can_run() is True

    def test_get_status_ready(self):
        """Test get_status method for ready command."""
        cmd = StartupCommand(
            id="test_cmd",
            name="Test Command",
            description="A test command",
            category="Test Category",
            command="test_script.py"
        )

        assert cmd.get_status() == "✅ Ready to run"

    def test_get_status_requires_env(self):
        """Test get_status method for command requiring environment."""
        cmd = StartupCommand(
            id="test_cmd",
            name="Test Command",
            description="A test command",
            category="Test Category",
            command="test_script.py",
            requires_env=True
        )

        with patch.dict(os.environ, {}, clear=True):
            assert cmd.get_status() == "⚠️  Requires environment setup"


class TestCommandRegistry:
    """Test cases for CommandRegistry class."""

    def test_init(self):
        """Test CommandRegistry initialization."""
        registry = CommandRegistry()
        assert isinstance(registry.commands, dict)
        assert isinstance(registry.categories, dict)
        assert len(registry.commands) > 0  # Should have registered commands

    def test_get_command_existing(self):
        """Test getting an existing command."""
        registry = CommandRegistry()
        cmd = registry.get_command("main_gui")

        assert cmd is not None
        assert cmd.id == "main_gui"
        assert cmd.name == "Main GUI Application"

    def test_get_command_nonexistent(self):
        """Test getting a nonexistent command."""
        registry = CommandRegistry()
        cmd = registry.get_command("nonexistent_command")

        assert cmd is None

    def test_get_commands_by_category(self):
        """Test getting commands by category."""
        registry = CommandRegistry()
        gui_commands = registry.get_commands_by_category("GUI Applications")

        assert len(gui_commands) > 0
        for cmd in gui_commands:
            assert cmd.category == "GUI Applications"

    def test_get_commands_by_category_empty(self):
        """Test getting commands for nonexistent category."""
        registry = CommandRegistry()
        commands = registry.get_commands_by_category("Nonexistent Category")

        assert commands == []

    def test_get_all_categories(self):
        """Test getting all available categories."""
        registry = CommandRegistry()
        categories = registry.get_all_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "GUI Applications" in categories

    def test_get_all_commands(self):
        """Test getting all commands."""
        registry = CommandRegistry()
        all_commands = registry.get_all_commands()

        assert isinstance(all_commands, list)
        assert len(all_commands) > 0

        # Check that commands are sorted by priority within categories
        categories = registry.get_all_categories()
        for category in categories:
            category_commands = [cmd for cmd in all_commands if cmd.category == category]
            priorities = [cmd.priority for cmd in category_commands]
            assert priorities == sorted(priorities, reverse=True)

    def test_search_commands_by_name(self):
        """Test searching commands by name."""
        registry = CommandRegistry()
        results = registry.search_commands("GUI")

        assert len(results) > 0
        for cmd in results:
            assert "gui" in cmd.name.lower() or "gui" in cmd.description.lower()

    def test_search_commands_by_description(self):
        """Test searching commands by description."""
        registry = CommandRegistry()
        results = registry.search_commands("desktop")

        assert len(results) > 0
        for cmd in results:
            assert "desktop" in cmd.name.lower() or "desktop" in cmd.description.lower()

    def test_search_commands_no_results(self):
        """Test searching with no matching results."""
        registry = CommandRegistry()
        results = registry.search_commands("nonexistent_search_term")

        assert results == []


class TestCommandLauncher:
    """Test cases for CommandLauncher class."""

    def test_init(self):
        """Test CommandLauncher initialization."""
        launcher = CommandLauncher()
        assert launcher.selected_category is None
        assert hasattr(launcher, 'console')

    @patch('startcommands.launcher.Console')
    def test_print_welcome(self, mock_console):
        """Test welcome banner printing."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        launcher.print_welcome()

        # Verify that print was called (exact content may vary)
        mock_console.print.assert_called()

    @patch('startcommands.launcher.Console')
    def test_show_categories(self, mock_console):
        """Test showing available categories."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        categories = launcher.show_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        mock_console.print.assert_called()

    @patch('startcommands.launcher.Console')
    def test_show_category_commands(self, mock_console):
        """Test showing commands in a category."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        launcher.show_category_commands("GUI Applications")

        mock_console.print.assert_called()

    @patch('startcommands.launcher.Console')
    def test_show_category_commands_empty(self, mock_console):
        """Test showing commands for empty category."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        launcher.show_category_commands("Nonexistent Category")

        # Should print error message
        mock_console.print.assert_called()

    @patch('startcommands.launcher.Prompt')
    @patch('startcommands.launcher.IntPrompt')
    @patch('startcommands.launcher.Console')
    def test_select_category_single(self, mock_console, mock_int_prompt, mock_prompt):
        """Test category selection with single category."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        # Mock single category
        with patch('startcommands.launcher.command_registry') as mock_registry:
            mock_registry.get_all_categories.return_value = ["Single Category"]

            result = launcher.select_category(["Single Category"])

            assert result == "Single Category"
            # Should not prompt for single category
            mock_int_prompt.ask.assert_not_called()

    @patch('startcommands.launcher.Prompt')
    @patch('startcommands.launcher.IntPrompt')
    @patch('startcommands.launcher.Console')
    def test_select_category_multiple(self, mock_console, mock_int_prompt, mock_prompt):
        """Test category selection with multiple categories."""
        launcher = CommandLauncher()
        launcher.console = mock_console
        mock_int_prompt.ask.return_value = 1

        categories = ["Category 1", "Category 2"]
        result = launcher.select_category(categories)

        assert result == "Category 1"
        mock_int_prompt.ask.assert_called_once()

    @patch('startcommands.launcher.Prompt')
    @patch('startcommands.launcher.IntPrompt')
    @patch('startcommands.launcher.Console')
    def test_select_command_single(self, mock_console, mock_int_prompt, mock_prompt):
        """Test command selection with single command."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        mock_cmd = Mock()
        commands = [mock_cmd]

        result = launcher.select_command(commands)

        assert result == mock_cmd
        # Should not prompt for single command
        mock_int_prompt.ask.assert_not_called()

    @patch('startcommands.launcher.Prompt')
    @patch('startcommands.launcher.IntPrompt')
    @patch('startcommands.launcher.Console')
    def test_select_command_multiple(self, mock_console, mock_int_prompt, mock_prompt):
        """Test command selection with multiple commands."""
        launcher = CommandLauncher()
        launcher.console = mock_console
        mock_int_prompt.ask.return_value = 1

        mock_cmd1 = Mock()
        mock_cmd2 = Mock()
        commands = [mock_cmd1, mock_cmd2]

        result = launcher.select_command(commands)

        assert result == mock_cmd1
        mock_int_prompt.ask.assert_called_once()

    @patch('startcommands.launcher.Console')
    @patch('startcommands.launcher.subprocess.Popen')
    @patch('startcommands.launcher.Confirm')
    def test_execute_command_success(self, mock_confirm, mock_popen, mock_console):
        """Test successful command execution."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        # Mock command - use GUI category to avoid confirmation prompt
        mock_cmd = Mock()
        mock_cmd.id = "test_cmd"
        mock_cmd.name = "Test Command"
        mock_cmd.category = "GUI Applications"  # GUI apps don't need confirmation
        mock_cmd.get_full_command.return_value = ["python", "test.py"]
        mock_cmd.can_run.return_value = True

        # Mock process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process

        result = launcher.execute_command(mock_cmd)

        assert result is True
        mock_popen.assert_called_once_with(
            ["python", "test.py"],
            cwd=os.getcwd(),
            env=os.environ.copy()
        )

    @patch('startcommands.launcher.Console')
    def test_execute_command_not_ready(self, mock_console):
        """Test command execution when command is not ready."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        # Mock command that can't run
        mock_cmd = Mock()
        mock_cmd.can_run.return_value = False
        mock_cmd.requires_env = True
        mock_cmd.name = "Test Command"
        mock_cmd.get_full_command.return_value = ["python", "test.py"]  # Add this

        result = launcher.execute_command(mock_cmd)

        assert result is False
        # Should have called print at least twice (error messages)
        assert mock_console.print.call_count >= 2

    @patch('startcommands.launcher.Console')
    @patch('startcommands.launcher.Confirm')
    def test_execute_command_cancelled(self, mock_confirm, mock_console):
        """Test command execution when user cancels."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        # Mock command
        mock_cmd = Mock()
        mock_cmd.can_run.return_value = True
        mock_cmd.category = "CLI Applications"  # Use CLI to trigger confirmation
        mock_cmd.name = "Test Command"
        mock_cmd.get_full_command.return_value = ["python", "test.py"]  # Add this

        # Mock user cancellation
        mock_confirm.ask.return_value = False

        result = launcher.execute_command(mock_cmd)

        assert result is False
        # Should have called print for cancellation message
        mock_console.print.assert_called()

    @patch('startcommands.launcher.Console')
    def test_search_commands(self, mock_console):
        """Test command search functionality."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        with patch('startcommands.launcher.Prompt') as mock_prompt:
            with patch('startcommands.launcher.command_registry') as mock_registry:
                mock_prompt.ask.return_value = "GUI"
                mock_cmd = Mock()
                mock_registry.search_commands.return_value = [mock_cmd]

                result = launcher.search_commands()

                assert result == mock_cmd
                mock_registry.search_commands.assert_called_once_with("GUI")

    @patch('startcommands.launcher.Console')
    def test_search_commands_no_results(self, mock_console):
        """Test command search with no results."""
        launcher = CommandLauncher()
        launcher.console = mock_console

        with patch('startcommands.launcher.Prompt') as mock_prompt:
            with patch('startcommands.launcher.command_registry') as mock_registry:
                mock_prompt.ask.return_value = "nonexistent"
                mock_registry.search_commands.return_value = []

                result = launcher.search_commands()

                assert result is None
                mock_console.print.assert_called()


class TestMainModule:
    """Test cases for main module functions."""

    def test_create_parser(self):
        """Test argument parser creation."""
        parser = create_parser()

        assert parser is not None

        # Test parsing various arguments
        args = parser.parse_args(['--list'])
        assert args.list is True

        args = parser.parse_args(['--category', 'GUI Applications'])
        assert args.category == 'GUI Applications'

        args = parser.parse_args(['--run', 'main_gui'])
        assert args.run == 'main_gui'

        args = parser.parse_args(['--search', 'web'])
        assert args.search == 'web'

    @patch('startcommands.main.CommandLauncher')
    def test_list_all_commands(self, mock_launcher_class):
        """Test listing all commands."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher

        with patch('startcommands.main.command_registry') as mock_registry:
            mock_registry.get_all_categories.return_value = ['Category 1']
            mock_registry.get_commands_by_category.return_value = []

            list_all_commands()

            mock_launcher_class.assert_called_once()
            mock_launcher.console.print.assert_called()

    @patch('startcommands.main.CommandLauncher')
    def test_show_category_commands(self, mock_launcher_class):
        """Test showing category commands."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher

        show_category_commands("Test Category")

        mock_launcher.show_category_commands.assert_called_once_with("Test Category")

    @patch('startcommands.main.CommandLauncher')
    @patch('startcommands.main.command_registry')
    def test_run_specific_command_success(self, mock_registry, mock_launcher_class):
        """Test running a specific command successfully."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        mock_launcher.execute_command.return_value = True

        mock_cmd = Mock()
        mock_registry.get_command.return_value = mock_cmd

        # Test that the function returns the expected value
        result = run_specific_command("test_cmd")

        assert result is True
        mock_registry.get_command.assert_called_once_with("test_cmd")
        mock_launcher.execute_command.assert_called_once_with(mock_cmd)

    @patch('startcommands.main.CommandLauncher')
    @patch('startcommands.main.command_registry')
    def test_run_specific_command_not_found(self, mock_registry, mock_launcher_class):
        """Test running a nonexistent command."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher

        mock_registry.get_command.return_value = None

        # Test that the function returns False for nonexistent command
        result = run_specific_command("nonexistent_cmd")

        assert result is False
        mock_launcher.console.print.assert_called()

    @patch('startcommands.main.CommandLauncher')
    @patch('startcommands.main.command_registry')
    def test_search_commands_with_results(self, mock_registry, mock_launcher_class):
        """Test searching commands with results."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher

        mock_cmd = Mock()
        mock_registry.search_commands.return_value = [mock_cmd]

        search_commands("test query")

        mock_launcher.console.print.assert_called()
        mock_registry.search_commands.assert_called_once_with("test query")

    @patch('startcommands.main.CommandLauncher')
    def test_search_commands_no_results(self, mock_launcher_class):
        """Test searching commands with no results."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher

        with patch('startcommands.main.command_registry') as mock_registry:
            mock_registry.search_commands.return_value = []

            search_commands("nonexistent query")

            mock_launcher.console.print.assert_called()


class TestStartCommandsIntegration:
    """Integration tests for startcommands functionality."""

    @pytest.mark.integration
    def test_command_registry_has_all_expected_commands(self):
        """Test that command registry contains all expected commands."""
        registry = CommandRegistry()

        # Check that we have commands in each category
        categories = registry.get_all_categories()
        assert "GUI Applications" in categories
        assert "Web Applications" in categories
        assert "CLI Applications" in categories
        assert "Server Components" in categories

        # Check specific commands exist
        assert registry.get_command("main_gui") is not None
        assert registry.get_command("web_app") is not None
        assert registry.get_command("cli_rich") is not None
        assert registry.get_command("fastapi_server") is not None

    @pytest.mark.integration
    def test_all_commands_have_valid_file_paths(self):
        """Test that all commands reference existing files."""
        registry = CommandRegistry()

        for cmd in registry.get_all_commands():
            # Skip commands that don't reference local files
            if cmd.command in ["run_app.bat"]:
                continue

            # Check if the command file exists
            if cmd.command and not cmd.command.startswith(("python", "http")):
                file_path = Path(cmd.command)
                if not file_path.exists():
                    pytest.fail(f"Command '{cmd.id}' references non-existent file: {cmd.command}")

    @pytest.mark.integration
    @patch('startcommands.launcher.subprocess.Popen')
    def test_launcher_can_execute_commands(self, mock_popen):
        """Test that launcher can execute commands (with mocked subprocess)."""
        launcher = CommandLauncher()

        # Mock a successful process
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Get a real command from registry
        registry = CommandRegistry()
        cmd = registry.get_command("main_gui")

        assert cmd is not None

        # Mock user confirmation
        with patch('startcommands.launcher.Confirm') as mock_confirm:
            mock_confirm.ask.return_value = True

            result = launcher.execute_command(cmd)

            assert result is True
            mock_popen.assert_called_once()

    @pytest.mark.integration
    def test_main_module_can_import_and_run(self):
        """Test that main module can be imported and basic functions work."""
        # This test ensures the module structure is correct
        from startcommands import main, commands, launcher

        # Test that we can create instances
        registry = commands.CommandRegistry()
        assert len(registry.get_all_commands()) > 0

        test_launcher = launcher.CommandLauncher()
        assert test_launcher is not None

        # Test parser creation
        parser = main.create_parser()
        assert parser is not None