# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a standalone Python desktop application called "Code Chat with AI" that provides a GUI interface for chatting with OpenAI models about codebases. The application uses tkinter for the interface and integrates with OpenAI's API.

## Key Files

- `code_chat.py` - Main application file containing the entire GUI application (CodeChatApp class)
- `requirements.txt` - Python dependencies (openai>=1.0.0, python-dotenv>=1.0.0)
- `.env` - Contains OpenAI API key configuration

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python code_chat.py
```

## Architecture

The application is built around a single `CodeChatApp` class that:

1. **GUI Management**: Creates tkinter interface with model selection, directory browsing, file display, and chat areas
2. **File Processing**: Scans selected directories for `.py` files and `.env` files, reads their content
3. **API Integration**: Sends codebase content + user questions to OpenAI API using the selected model
4. **Conversation Handling**: Maintains conversation history and supports save/load functionality

### Key Components

- **Model Selection**: Supports GPT-3.5-turbo, GPT-4, GPT-4-turbo via dropdown
- **Directory Scanner**: Recursively finds Python files and includes .env files
- **Threading**: API calls run in separate threads to prevent GUI blocking
- **Settings Management**: Secure API key configuration through settings dialog

### API Integration Pattern

The application constructs API messages by:
1. Creating system message with full codebase content
2. Appending conversation history
3. Adding current user question
4. Sending to OpenAI with model-specific parameters (max_tokens=2000, temperature=0.7)

## Environment Setup

Requires `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key_here
```

API key can also be set through the Settings menu in the application.