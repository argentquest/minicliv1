# CodeWhisper - Modern AI Code Analysis Application

## Project Overview

CodeWhisper is a powerful full-stack web application that brings AI assistance directly to your development workflow. It enables users to select any codebase, choose from specialized AI experts, and get intelligent insights, code reviews, and architectural guidance through an intuitive web interface. The application supports both GUI and CLI interfaces and provides multiple AI provider integrations.

## Architecture

The application follows a modern architecture with:
- **Frontend**: React application in the `web1/` directory
- **Backend**: FastAPI server in `fastapi_server.py` with supporting modules in `web_backend/`
- **Core Logic**: AI processing, file scanning, and application state management
- **Multiple Interfaces**: GUI, Standard CLI, Rich CLI, and REST API modes

The architecture implements several key patterns:
- Provider Pattern for multiple AI services (OpenRouter, OpenAI, etc.)
- Dual Scanner Architecture for performance optimization
- Persistent Context Management for conversation continuity
- File Locking System for safe concurrent operations

## Project Structure

```
minicli/
├── 📁 Web Frontend (React)
│   ├── web1/                  # React application
│   │   ├── src/               # React source code
│   │   ├── package.json       # Frontend dependencies
│   │   └── vite.config.ts     # Vite build configuration
│   └──
├── 📁 Backend (FastAPI)
│   ├── fastapi_server.py      # Main FastAPI server
│   ├── web_backend/            # FastAPI application modules
│   │   ├── api.py              # REST API endpoints
│   │   ├── schemas.py          # Pydantic models
│   │   └── services/           # Business logic services
│   └──
├── 📁 Core Application
│   ├── minicli.py              # Main application orchestration
│   ├── modern_main.py          # Desktop GUI application
│   ├── start_ui.py             # Alternative launcher
│   └── run_app.bat             # Windows batch launcher
│
├── 📁 AI & Processing
│   ├── ai.py                   # AI API integration and processing
│   ├── base_ai.py              # Base AI provider interface
│   ├── providers/              # AI provider implementations
│   │   ├── openrouter_provider.py  # OpenRouter AI provider
│   │   ├── tachyon_provider.py     # Tachyon AI provider
│   │   └── custom_provider.py      # Custom provider support
│   └── systemmessage_*.txt     # Expert mode definitions
│
├── 📁 Desktop UI Components
│   ├── simple_modern_ui.py     # Modern UI components
│   ├── tabbed_chat_area.py     # Chat interface with tabs
│   ├── theme.py                # Dark/light theme system
│   ├── icons.py                # Icon management
│   └── ui_controller.py        # UI state management
│
├── 📁 CLI Interfaces
│   ├── cli_interface.py        # Standard CLI interface
│   ├── cli_rich.py             # Rich CLI interface components
│   └── codechat-rich.py        # Rich CLI entry point
│
├── 📁 Data & State Management
│   ├── models.py               # Data structures and state management
│   ├── env_manager.py          # Environment variable handling
│   ├── file_scanner.py         # Standard codebase file scanning
│   ├── lazy_file_scanner.py    # Lazy loading file scanner for large codebases
│   ├── file_lock.py            # Safe JSON file operations
│   └── logger.py               # Structured logging system
│
├── 📁 Utilities
│   ├── code_fragment_parser.py # Code extraction from AI responses
│   ├── conversation_history_tab.py  # History management
│   ├── pattern_matcher.py      # Tool command pattern matching
│   ├── security_utils.py       # Security utilities for API keys
│   └── api_client.py           # API client utilities
│
└── 📁 Configuration & Documentation
    ├── requirements.txt        # Python dependencies
    ├── requirements-test.txt   # Test dependencies
    ├── .env                    # Environment configuration
    ├── .envTemplate            # Environment configuration template
    ├── config.py               # Centralized configuration
    └── systemmessage_*.txt     # Expert mode definitions
```

## Building and Running

### Prerequisites
- Python 3.7 or higher
- Node.js 16 or higher (for web frontend)
- Git
- API Key from OpenAI or OpenRouter

### Installation
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. For virtual environment (recommended):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd web1
   npm install
   cd ..
   ```

4. Set up API keys by creating a `.env` file in the project root:
   ```env
   # Required: At least one API key
   OPENAI_API_KEY=sk-your-openai-key-here
   OPENROUTER_API_KEY=sk-your-openrouter-key-here
   
   # Optional: Customize default settings
   DEFAULT_MODEL=openai/gpt-4
   UI_THEME=light
   MAX_TOKENS=2000
   TEMPERATURE=0.7
   ```

### Launching the Application

**Web Application Mode (Recommended):**
```bash
# Start the FastAPI backend
python fastapi_server.py

# In another terminal, start the React frontend
cd web1 && npm run dev
```

**Desktop GUI Mode:**
```bash
python modern_main.py
```

**Alternative GUI Launchers:**
```bash
# For window visibility issues:
python start_ui.py

# Windows batch file:
run_app.bat
```

**CLI Modes:**
```bash
# Standard CLI mode:
python minicli.py --cli --folder ./src --question "What does this code do?"

# Rich CLI mode (enhanced terminal interface):
python codechat-rich.py analyze ./src "What does this code do?"
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest --cov=. --cov-report=html --cov-exclude=tests/*
```

## Key Features

### AI-Powered Code Analysis
- Chat with specialized AI experts about your codebase
- Multiple expert modes: Security Auditor, Performance Engineer, Code Reviewer, etc.
- Context-aware responses based on your selected files

### Modern User Interface
- Dark/Light Theme Support - Toggle with one click
- Tabbed Conversations - Manage multiple chat sessions
- Responsive Design - Clean, professional interface
- Rich Markdown Rendering - AI responses formatted with GitHub-style Markdown

### Smart File Management
- Intelligent File Scanning - Automatically detects relevant code files
- Persistent Context - Selected files remembered across conversation turns
- Project Detection - Recognizes common project structures

### Multiple AI Providers
- OpenRouter Integration - Access to 100+ AI models from multiple providers
- Provider Factory Pattern - Extensible architecture for adding new providers
- Flexible Configuration - Easy provider switching and model selection

### Multiple Interface Modes
- GUI Mode - Full graphical interface with modern UI
- Standard CLI - Command-line interface for automation and scripting
- Rich CLI - Enhanced terminal interface with syntax highlighting
- API Server - REST API for programmatic access and integrations

### Conversation Management
- Save/Load History - Never lose important conversations
- Export Options - Save conversations as JSON files
- New Conversation - Clean slate for different topics

## Configuration

The application uses a centralized configuration system through the Config class in config.py. Environment variables can be set in a `.env` file in the project root:

```env
# API Configuration (Required)
OPENAI_API_KEY=sk-your-openai-key-here
OPENROUTER_API_KEY=sk-your-openrouter-key-here

# Model Settings
DEFAULT_MODEL=openai/gpt-4
MODELS=openai/gpt-3.5-turbo,openai/gpt-4

# UI Preferences
UI_THEME=light
CURRENT_SYSTEM_PROMPT=systemmessage_default.txt

# AI Parameters
MAX_TOKENS=2000
TEMPERATURE=0.7

# File Scanning
IGNORE_FOLDERS=node_modules,venv,.git
```

## System Messages (Expert Modes)

The application includes specialized system messages for different analysis types:
- `systemmessage_default.txt` - General Assistant
- `systemmessage_security.txt` - Security Auditor
- `systemmessage_performance.txt` - Performance Engineer
- `systemmessage_codereview.txt` - Code Reviewer
- `systemmessage_architecture.txt` - System Architect
- And more specialized expert modes...

## Development Conventions

- Follow PEP 8 guidelines for Python code
- Use type hints where appropriate
- Add docstrings for all public methods
- Comment complex logic
- Use structured logging with context
- Implement asynchronous processing where appropriate for responsiveness

## Troubleshooting

Common issues and solutions:
- **Application won't start**: Check Python version (must be 3.7+), reinstall dependencies, try alternative launchers
- **API key errors**: Verify your API key in the `.env` file, check key format, ensure sufficient API credits
- **Window doesn't appear**: Use the visibility-forced launcher (`python start_ui.py`)
- **File scanning issues**: Ensure read permissions, check supported file types, be patient with large directories
- **Theme issues**: Reset theme preference in .env file

For detailed error information, use the Rich CLI with verbose output:
```bash
python codechat-rich.py config --validate  # Test configuration
python codechat-rich.py analyze ./src "test question" --verbose  # Detailed logging
```