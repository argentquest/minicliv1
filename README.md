# Code Chat with AI

> A modern desktop application for intelligent code analysis and AI-powered development assistance

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com)

**Code Chat with AI** is a powerful desktop application that brings AI assistance directly to your development workflow. Select any codebase, choose from specialized AI experts, and get intelligent insights, code reviews, and architectural guidance through an intuitive chat interface.

![Application Screenshot](docs/screenshot.png)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.7 or higher** ([Download here](https://python.org/downloads/))
- **Git** (optional, for cloning)
- **API Key** from [OpenAI](https://openai.com/api/) or [OpenRouter](https://openrouter.ai/)

### Installation

1. **Clone or Download the Repository**
   ```bash
   git clone https://github.com/your-username/code-chat-ai.git
   cd code-chat-ai
   ```
   
   *Or download and extract the ZIP file*

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   *For virtual environment (recommended):*
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Set Up API Keys**
   
   **Option A: Environment File (Recommended)**
   
   Create a `.env` file in the project root:
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
   
   **Option B: Through the Application**
   
   Run the app and click **Settings** → **Environment Variables** to configure your API keys.

4. **Launch the Application**
   ```bash
   python modern_main.py
   ```
   
   *Alternative launch methods:*
   ```bash
   # For window visibility issues:
   python start_ui.py
   
   # Debug mode with enhanced error handling:
   python debug_app.py
   ```

---

## ✨ Features

### 🤖 **AI-Powered Code Analysis**
- Chat with specialized AI experts about your codebase
- Multiple expert modes: Security Auditor, Performance Engineer, Code Reviewer, etc.
- Context-aware responses based on your selected files

### 🎨 **Modern User Interface**
- **Dark/Light Theme Support** - Toggle with one click
- **Tabbed Conversations** - Manage multiple chat sessions
- **Responsive Design** - Clean, professional interface
- **Code Fragment Extraction** - Easily copy code suggestions

### 📁 **Smart File Management**
- **Intelligent File Scanning** - Automatically detects relevant code files
- **Persistent Context** - Selected files remembered across conversation turns
- **Project Detection** - Recognizes common project structures

### 🔧 **Multiple AI Providers**
- **OpenAI Integration** - GPT-3.5, GPT-4, GPT-4 Turbo
- **OpenRouter Support** - Access to multiple AI models
- **Flexible Configuration** - Easy provider switching

### 📝 **Conversation Management**
- **Save/Load History** - Never lose important conversations  
- **Export Options** - Save conversations as JSON files
- **New Conversation** - Clean slate for different topics

---

## 📖 Usage Guide

### Getting Started

1. **Launch the Application**
   ```bash
   python modern_main.py
   ```

2. **Configure Your API Key** (First Time Only)
   - Click the **Settings** button
   - Add your OpenAI or OpenRouter API key
   - Select your preferred AI model

3. **Select Your Codebase**
   - Click **Browse** to select a directory containing your code
   - The app will automatically scan for relevant files
   - Check/uncheck files to include in the analysis

4. **Choose an AI Expert**
   - Use the **System Message** dropdown to select an expert:
     - **Default** - General coding assistance
     - **Security** - Security audits and vulnerability analysis
     - **Performance** - Performance optimization suggestions
     - **Code Review** - Comprehensive code quality analysis
     - **Architecture** - System design and architecture advice
     - And more specialized experts...

5. **Start Chatting**
   - Type your questions in the chat area
   - Use **Execute System Prompt** for immediate expert analysis
   - Get AI-powered insights, suggestions, and code improvements

### Advanced Features

#### **Code Fragment Extraction**
When AI responses contain code blocks marked with triple backticks (```), a **📋 Code Fragments** button appears:
- Click to view all code suggestions
- Select and copy specific code blocks to clipboard
- Perfect for implementing AI suggestions

#### **Theme Switching**
Toggle between light and dark themes:
- Click the **🌙 Dark** / **☀️ Light** button in the toolbar
- Preference is automatically saved
- Restart recommended for full effect

#### **Persistent File Context**
Files selected in your first conversation are automatically remembered:
- No need to reselect files for follow-up questions
- Context persists until you start a new conversation
- Clear conversation to reset file selection

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root to customize the application:

```env
# API Configuration (Required)
OPENAI_API_KEY=sk-your-openai-key-here
OPENROUTER_API_KEY=sk-your-openrouter-key-here

# Model Settings
DEFAULT_MODEL=openai/gpt-4                    # Default AI model
MODELS=openai/gpt-3.5-turbo,openai/gpt-4     # Available models (comma-separated)

# UI Preferences
UI_THEME=light                                # Theme: 'light' or 'dark'
CURRENT_SYSTEM_PROMPT=systemmessage_default.txt  # Default expert mode

# AI Parameters
MAX_TOKENS=2000                               # Maximum response length
TEMPERATURE=0.7                               # AI creativity (0.0-1.0)

# File Scanning
IGNORE_FOLDERS=node_modules,venv,.git         # Folders to ignore (comma-separated)

# Tool Commands (Advanced)
TOOL_LINT=pylint                              # Custom linting command
TOOL_TEST=pytest                              # Custom test command
```

### System Messages (Expert Modes)

The application includes specialized system messages for different analysis types:

| File | Expert Mode | Use Case |
|------|-------------|----------|
| `systemmessage_default.txt` | General Assistant | Balanced code analysis |
| `systemmessage_security.txt` | Security Auditor | Vulnerability assessment |
| `systemmessage_performance.txt` | Performance Engineer | Optimization suggestions |
| `systemmessage_codereview.txt` | Code Reviewer | Quality and best practices |
| `systemmessage_architecture.txt` | System Architect | Design and structure |
| `systemmessage_debugging.txt` | Debug Specialist | Bug finding and fixes |
| `systemmessage_testing.txt` | Test Engineer | Test coverage and strategy |

### Advanced Settings

Access advanced configuration through **Settings** → **Environment Variables**:

- **API Keys** - Configure OpenAI and OpenRouter access
- **Model Selection** - Choose default AI models
- **UI Preferences** - Theme and interface settings  
- **Performance Tuning** - Token limits and temperature
- **Tool Integration** - Custom linting and testing commands

---

## 🗂️ Project Structure

```
code-chat-ai/
├── 📁 Core Application
│   ├── minicli.py              # Main application orchestration
│   ├── modern_main.py          # Primary application entry point
│   ├── start_ui.py             # Alternative launcher with UI forcing
│   └── debug_app.py            # Debug launcher with error handling
│
├── 📁 AI & Processing
│   ├── ai.py                   # AI API integration and processing
│   ├── system_message_manager.py  # Expert mode management
│   └── systemmessage_*.txt     # Expert mode definitions
│
├── 📁 User Interface
│   ├── simple_modern_ui.py     # Modern UI components
│   ├── tabbed_chat_area.py     # Chat interface with tabs
│   ├── theme.py                # Dark/light theme system
│   ├── icons.py                # Icon management
│   └── *_dialog.py             # Various dialog windows
│
├── 📁 Data & State
│   ├── models.py               # Data structures and state management
│   ├── env_manager.py          # Environment variable handling
│   └── file_scanner.py         # Codebase file scanning
│
├── 📁 Utilities
│   ├── code_fragment_parser.py # Code extraction from AI responses
│   └── conversation_history_tab.py  # History management
│
└── 📁 Configuration
    ├── requirements.txt        # Python dependencies
    ├── .env                   # Environment configuration
    └── README.md              # This file
```

---

## 🛠️ Troubleshooting

### Common Issues

**❌ Application won't start**
```bash
# Check Python version (must be 3.7+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Try alternative launcher
python start_ui.py
```

**❌ API key errors**
- Verify your API key in the `.env` file
- Check that the key starts with `sk-` (OpenAI) or is properly formatted
- Ensure you have sufficient API credits
- Test with: **Settings** → **Environment Variables** → **Test Connection**

**❌ Window doesn't appear**
```bash
# Use the visibility-forced launcher
python start_ui.py

# Or check if window is hidden behind other windows
# Press Alt+Tab to cycle through open applications
```

**❌ File scanning issues**
- Ensure you have read permissions for the selected directory
- Check that the directory contains supported file types (.py, .js, .ts, etc.)
- Large directories may take time to scan - wait for completion

**❌ Theme issues**
```bash
# Reset theme to default
# Edit .env file and set:
UI_THEME=light

# Or delete the theme preference and restart
```

### Debug Mode

For detailed error information:
```bash
python debug_app.py
```

This launcher provides:
- Detailed error messages
- Stack trace information
- Component status checking
- Safe error handling

### Getting Help

1. **Check the logs** - Error messages appear in the status bar
2. **Use debug mode** - Run `python debug_app.py` for detailed errors
3. **Reset configuration** - Delete `.env` file to reset to defaults
4. **Update dependencies** - Run `pip install -r requirements.txt --upgrade`

---

## 🔧 Development

### Requirements

- **Python 3.7+** with tkinter support
- **Dependencies** listed in `requirements.txt`
- **API Access** to OpenAI or OpenRouter

### Running Tests

```bash
# Test OpenRouter integration
python test_openrouter.py

# Manual testing
python debug_app.py
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for all public methods
- Comment complex logic

---

## 📄 License

This project is available under standard software licensing terms.

---

## 🙏 Acknowledgments

- **OpenAI** for providing powerful language models
- **OpenRouter** for multi-model API access
- **Python Community** for excellent libraries and tools
- **Contributors** who help improve this project

---

## 🔗 Links

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [Python Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)

---

*Built with ❤️ for developers who want AI assistance in their coding workflow*