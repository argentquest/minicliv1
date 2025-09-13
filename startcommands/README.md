# 🚀 Start Commands Launcher

An interactive command launcher for Code Chat AI that helps users choose the right way to start the application with clear categorization and descriptions.

## 📋 Overview

The Start Commands system provides a unified interface to launch different components of the Code Chat AI application. Instead of remembering multiple command-line arguments and file paths, users can browse through organized categories and select the appropriate startup method.

## 🎯 Features

- **Interactive Selection**: Browse commands by category or search by keyword
- **Clear Organization**: Commands grouped by functionality (GUI, Web, CLI, etc.)
- **Rich Descriptions**: Detailed explanations of what each command does
- **Status Indicators**: Shows if commands are ready to run or need setup
- **Multiple Launch Modes**: GUI applications launch in background, CLI tools run in foreground
- **Command-line Interface**: Direct command execution without interaction

## 📂 Command Categories

### 🖥️ GUI Applications
Desktop graphical interfaces with full features:
- **Main GUI Application**: Full-featured Tkinter GUI with AI chat interface
- **Modern GUI Launcher**: Enhanced launcher with better error handling
- **Enhanced UI Launcher**: GUI with improved window visibility

### 🌐 Web Applications
Browser-based web interfaces:
- **Web Application (Full)**: Complete web app with FastAPI backend + NiceGUI frontend
- **Web Frontend Only**: NiceGUI frontend (requires separate backend)
- **Web Backend Only**: FastAPI backend server

### 💻 CLI Applications
Command-line interfaces for automation:
- **Standard CLI**: Command-line interface for batch processing
- **Rich CLI (Enhanced)**: Beautiful CLI with progress bars and colors

### ⚙️ Server Components
Backend servers and APIs:
- **FastAPI Server**: Standalone FastAPI backend server
- **Server Runner**: Alternative server launcher

### 🧪 Development & Testing
Testing and development tools:
- **FastAPI Tests**: Run FastAPI integration tests
- **CLI Tests**: Run CLI interface tests

### 📜 Legacy & Special
Legacy versions and special launchers:
- **Legacy Chat**: Original chat interface
- **Windows Batch Launcher**: Desktop batch file launcher

## 🚀 Usage

### Option 1: Double-Click Batch File (Easiest - Windows)
Simply **double-click the `start.bat` file** in the project root directory!

**What it does:**
- ✅ Automatically detects and activates your virtual environment
- ✅ Launches the interactive startcommands launcher
- ✅ Provides clear error messages if something goes wrong
- ✅ Works on any Windows system with Python installed

### Option 2: Interactive Mode (Recommended)

```bash
# Launch interactive launcher
python -m startcommands

# Or run the launcher directly
python startcommands/launcher.py
```

**Note:** The `python -m startcommands` command works because of the `__main__.py` file in the package, which serves as the entry point for module execution.

The interactive launcher will:
1. Show a welcome banner
2. Display available categories
3. Let you browse commands by category
4. Show detailed information about each command
5. Execute your selected command

### Command-Line Mode

```bash
# List all available commands
python -m startcommands --list

# Show commands in specific category
python -m startcommands --category "GUI Applications"

# Run specific command directly
python -m startcommands --run main_gui

# Search commands by keyword
python -m startcommands --search "web"
```

## 📖 Command Reference

### Quick Start Commands

| Command ID | Description | Category |
|------------|-------------|----------|
| `main_gui` | Full-featured desktop GUI | GUI Applications |
| `web_app` | Complete web application | Web Applications |
| `cli_rich` | Enhanced command-line interface | CLI Applications |
| `fastapi_server` | Standalone API server | Server Components |

### All Available Commands

Run `python -m startcommands --list` to see all commands with their descriptions and status.

## 🔧 Requirements

The launcher automatically checks if commands can be executed:

- **Environment Setup**: Some commands require API keys and configuration
- **Dependencies**: Commands check for required Python packages
- **File Availability**: Verifies that command files exist

Commands that need setup will show:
```
⚠️ Requires environment setup
```

## 🎨 Interface Features

### Rich Terminal Output
- Color-coded categories and commands
- Progress indicators for long-running operations
- Status messages and error handling
- Beautiful tables and panels

### Smart Command Execution
- **GUI Applications**: Launch in background (non-blocking) - launcher continues running
- **CLI Applications**: Run in foreground (blocking) - launcher exits after completion
- **Server Components**: Run in background with process management - launcher continues
- **Web Applications**: Run in background with URL detection - launcher continues
- Automatic error detection and user feedback
- Confirmation prompts for destructive operations

### Server & Web Application Handling
- **Background Execution**: Servers and web apps run as separate processes
- **Process Monitoring**: Tracks process IDs and startup status
- **URL Detection**: Automatically detects and displays web interface URLs
- **Cross-Platform**: Works on Windows, Linux, and macOS with proper process groups
- **Error Recovery**: Captures startup errors and provides helpful diagnostics

### Exit & Navigation
- **Multiple Exit Options**: '4', 'q', 'quit', 'exit', or Ctrl+C/Ctrl+D
- **Graceful Shutdown**: Clean exit with status messages
- **Context-Aware**: Different behavior based on application type
- **Background Apps**: Can exit launcher while apps continue running

### Search and Filter
- Search commands by name or description
- Filter by category
- Direct command execution by ID

## 🛠️ Development

### Adding New Commands

1. Edit `startcommands/commands.py`
2. Add new `StartupCommand` instances to the registry
3. Commands are automatically categorized and sorted by priority

Example:
```python
self._register_command(StartupCommand(
    id="my_command",
    name="My Custom Command",
    description="Description of what this command does",
    category="My Category",
    command="my_script.py",
    icon="🎯",
    priority=5
))
```

### Command Properties

- **id**: Unique identifier for the command
- **name**: Display name shown to users
- **description**: Detailed explanation of the command
- **category**: Category for organization
- **command**: Python script to execute
- **args**: Optional command-line arguments
- **icon**: Emoji icon for visual identification
- **priority**: Sort order within category (higher = first)

## 📋 Examples

### Example 1: First-time Setup
```bash
# Launch interactive launcher
python -m startcommands

# Select "GUI Applications" category
# Choose "Main GUI Application"
# Application launches with full interface
```

### Example 2: Web Development
```bash
# Launch web application
python -m startcommands --run web_app

# Or use interactive mode
python -m startcommands
# Select "Web Applications" -> "Web Application (Full)"
```

### Example 3: CLI Automation
```bash
# Run CLI with specific parameters
python -m startcommands --run cli_rich

# Or search for CLI commands
python -m startcommands --search "cli"
```

## 🔍 Troubleshooting

### Command Not Found
- Check if the command file exists in the project directory
- Verify Python path and working directory
- Use `--list` to see all available commands

### Environment Setup Required
- Run `python -m startcommands setup` (if available)
- Check `.env` file for required variables
- Verify API keys and configuration

### Permission Errors
- Ensure execute permissions on script files
- Check file ownership and access rights
- Try running with appropriate user privileges

## 📝 Notes

- GUI applications launch in background and don't block the terminal
- CLI applications run in foreground and return control when complete
- The launcher automatically detects command availability and requirements
- Commands are sorted by priority within each category
- Search is case-insensitive and matches both names and descriptions

## 🤝 Contributing

To add new startup commands:

1. Follow the `StartupCommand` structure in `commands.py`
2. Add appropriate icons and descriptions
3. Test the command execution
4. Update this documentation

The launcher is designed to be extensible and easy to maintain.