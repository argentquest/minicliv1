# Code Chat with AI

A modern desktop application for chatting with AI models about codebases. Features a beautiful GUI interface with dark/light themes, tabbed conversations, and seamless AI integration.

## Features

- 🤖 **AI-Powered Code Analysis** - Chat with AI models about your codebase
- 🎨 **Modern UI** - Clean, intuitive interface with dark/light theme support
- 📁 **Smart File Scanning** - Automatically scans and includes relevant code files
- 💬 **Tabbed Conversations** - Manage multiple chat sessions
- 🔧 **Multiple AI Providers** - Support for OpenAI and OpenRouter APIs
- 📝 **Conversation History** - Save and load previous conversations
- ⚙️ **Environment Management** - Easy API key and settings configuration

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up API Keys**
   - Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENROUTER_API_KEY=your_openrouter_key_here
   ```
   - Or configure through the Settings dialog in the application

3. **Run the Application**
   ```bash
   # Standard launch
   python modern_main.py
   
   # Or with forced window visibility
   python start_ui.py
   ```

## Project Structure

### Core Application
- `minicli.py` - Main application class and logic
- `modern_main.py` - Primary entry point
- `start_ui.py` - Alternative entry point with UI forcing

### UI Components
- `simple_modern_ui.py` - Modern UI components and styling
- `tabbed_chat_area.py` - Chat interface with tabs
- `theme.py` - Theme management (dark/light modes)
- `icons.py` - Icon management system

### Core Functionality
- `ai.py` - AI processing and API integration
- `file_scanner.py` - Codebase scanning and file processing
- `models.py` - Data models and structures

### Settings & Configuration
- `env_manager.py` - Environment variable management
- `env_settings_dialog.py` - Settings configuration dialog
- `system_message_manager.py` - System message handling
- `system_message_dialog.py` - System message configuration

### Dialogs
- `about_dialog.py` - Application about dialog
- `conversation_history_tab.py` - Conversation history management

## Usage

1. **Launch the Application**
   - Run `python modern_main.py`
   - The application window will open with the modern interface

2. **Configure AI Settings**
   - Click the Settings button to configure API keys
   - Choose your preferred AI model and provider

3. **Select Codebase**
   - Use the "Browse" button to select a directory containing your code
   - The application will automatically scan for relevant files

4. **Start Chatting**
   - Type your questions about the codebase in the chat area
   - The AI will analyze your code and provide insights

5. **Manage Conversations**
   - Use tabs to manage multiple conversations
   - Save/load conversation history as needed

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENROUTER_API_KEY` - Your OpenRouter API key

### System Messages
The application includes preset system messages for different use cases:
- `systemmessage_beginner.txt` - For beginners
- `systemmessage_performance.txt` - Performance-focused analysis
- `systemmessage_security.txt` - Security-focused analysis

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- Dependencies listed in `requirements.txt`:
  - openai
  - python-dotenv
  - requests

## Development

### Testing
- `test_openrouter.py` - Test script for OpenRouter API integration

### Debugging
- `debug_app.py` - Debug version with enhanced error handling

## License

This project is available under standard software licensing terms.