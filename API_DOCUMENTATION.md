# API Documentation

## Overview

This document provides comprehensive API documentation for the Code Chat with AI FastAPI backend. The application exposes a REST API that serves the React frontend and provides programmatic access to AI-powered code analysis capabilities.

## Base URL
```
http://localhost:8000
```

## Authentication
API keys are managed through environment variables and are not required in API requests. Authentication is handled server-side using the configured API keys.

## API Endpoints

### Health & Status

#### GET /health
Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T14:30:22.123456",
  "version": "1.0.0"
}
```

### AI Models & Providers

#### GET /meta/providers
Returns available AI providers.

**Response:**
```json
{
  "providers": ["openrouter", "tachyon"],
  "default": "openrouter"
}
```

#### GET /meta/models
Returns available AI models for a provider.

**Parameters:**
- `provider` (optional): Filter models by provider

**Response:**
```json
{
  "models": ["openai/gpt-4", "openai/gpt-3.5-turbo", "anthropic/claude-3-sonnet"],
  "default": "openai/gpt-4",
  "provider": "openrouter"
}
```

#### GET /meta/ui-defaults
Returns UI configuration defaults.

**Response:**
```json
{
  "provider": "openrouter",
  "models": ["openai/gpt-4", "openai/gpt-3.5-turbo"],
  "defaultModel": "openai/gpt-4",
  "toolCommands": [{"key": "TOOL_LINT", "value": "pylint"}],
  "systemMessages": {
    "current": "systemmessage_default.txt",
    "messages": [
      {
        "filename": "systemmessage_default.txt",
        "display_name": "Default",
        "preview": "General purpose instructions",
        "length": 150
      }
    ]
  },
  "apiKey": "sk-..."
}
```

### Conversation Management

#### POST /conversations
Creates a new conversation session.

**Request Body:**
```json
{
  "provider": "openrouter",
  "model": "openai/gpt-4",
  "apiKey": "sk-your-api-key"
}
```

**Response:**
```json
{
  "conversation_id": "conv_123456",
  "provider": "openrouter",
  "model": "openai/gpt-4",
  "available_models": ["openai/gpt-4", "openai/gpt-3.5-turbo"],
  "summary": {
    "conversation_id": "conv_123456",
    "provider": "openrouter",
    "selected_model": "openai/gpt-4",
    "selected_directory": null,
    "selected_files": [],
    "persistent_files": [],
    "question_history": [],
    "conversation_history": []
  }
}
```

#### GET /conversations/{conversation_id}
Retrieves conversation summary.

**Response:**
```json
{
  "conversation_id": "conv_123456",
  "provider": "openrouter",
  "selected_model": "openai/gpt-4",
  "selected_directory": "/path/to/project",
  "selected_files": ["main.py", "utils.py"],
  "persistent_files": ["main.py"],
  "question_history": [
    {
      "question": "What does this code do?",
      "status": "completed",
      "response": "This code implements...",
      "timestamp": "2023-12-01T14:30:22.123456",
      "tokens_used": 150,
      "processing_time": 2.34,
      "model_used": "openai/gpt-4"
    }
  ],
  "conversation_history": [
    {"role": "user", "content": "What does this code do?"},
    {"role": "assistant", "content": "This code implements..."}
  ]
}
```

#### POST /conversations/{conversation_id}/clear
Clears conversation history.

**Response:**
```json
{
  "conversation_id": "conv_123456",
  "provider": "openrouter",
  "selected_model": "openai/gpt-4",
  "selected_directory": "/path/to/project",
  "selected_files": ["main.py"],
  "persistent_files": [],
  "question_history": [],
  "conversation_history": []
}
```

#### DELETE /conversations/{conversation_id}
Deletes a conversation session.

**Response:**
```json
{
  "conversation_id": "conv_123456"
}
```

### Question & Answer

#### POST /conversations/{conversation_id}/question
Asks a question about the codebase.

**Request Body:**
```json
{
  "question": "What does this function do?",
  "selectedFiles": ["main.py", "utils.py"],
  "persistent": false
}
```

**Response:**
```json
{
  "response": "This function implements a data processing pipeline...",
  "processing_time": 2.34,
  "tokens_used": 150,
  "question_index": 1,
  "summary": {
    "conversation_id": "conv_123456",
    "provider": "openrouter",
    "selected_model": "openai/gpt-4",
    "selected_directory": "/path/to/project",
    "selected_files": ["main.py", "utils.py"],
    "persistent_files": ["main.py"],
    "question_history": [
      {
        "question": "What does this function do?",
        "status": "completed",
        "response": "This function implements...",
        "timestamp": "2023-12-01T14:30:22.123456",
        "tokens_used": 150,
        "processing_time": 2.34,
        "model_used": "openai/gpt-4"
      }
    ],
    "conversation_history": [
      {"role": "user", "content": "What does this function do?"},
      {"role": "assistant", "content": "This function implements..."}
    ]
  }
}
```

#### POST /conversations/{conversation_id}/system-prompt
Executes the system prompt for initial analysis.

**Response:**
```json
{
  "response": "I've analyzed your codebase and found...",
  "processing_time": 3.45,
  "tokens_used": 200,
  "summary": {
    "conversation_id": "conv_123456",
    // ... conversation summary
  }
}
```

### File Management

#### POST /conversations/{conversation_id}/directory
Sets the working directory and scans for files.

**Request Body:**
```json
{
  "path": "/path/to/project"
}
```

**Response:**
```json
{
  "directory": "/path/to/project",
  "files": [
    {
      "name": "main.py",
      "path": "/path/to/project/main.py",
      "size": 1024,
      "modified": "2023-12-01T14:30:22.123456",
      "type": "file"
    }
  ],
  "message": "Successfully scanned directory",
  "summary": {
    "conversation_id": "conv_123456",
    // ... updated conversation summary
  }
}
```

#### POST /conversations/{conversation_id}/files
Updates selected files for analysis.

**Request Body:**
```json
{
  "selected_files": ["main.py", "utils.py"],
  "persistent": true
}
```

**Response:**
```json
{
  "conversation_id": "conv_123456",
  "provider": "openrouter",
  "selected_model": "openai/gpt-4",
  "selected_directory": "/path/to/project",
  "selected_files": ["main.py", "utils.py"],
  "persistent_files": ["main.py", "utils.py"],
  "question_history": [],
  "conversation_history": []
}
```

#### POST /files/scan
Scans a directory for files (utility endpoint).

**Request Body:**
```json
{
  "path": "/path/to/project"
}
```

**Response:**
```json
{
  "directory": "/path/to/project",
  "files": [
    {
      "name": "main.py",
      "path": "/path/to/project/main.py",
      "size": 1024,
      "modified": "2023-12-01T14:30:22.123456",
      "type": "file"
    }
  ],
  "tree": {
    "name": "project",
    "type": "directory",
    "children": [
      {
        "name": "main.py",
        "type": "file",
        "size": 1024
      }
    ]
  }
}
```

#### POST /files/content
Retrieves content of specified files.

**Request Body:**
```json
{
  "files": ["/path/to/project/main.py", "/path/to/project/utils.py"]
}
```

**Response:**
```json
{
  "combined_content": "# main.py\n\ndef main():\n    print('Hello World')\n\n# utils.py\n\ndef helper():\n    return 'helper function'\n"
}
```

### Model & Settings Management

#### PUT /conversations/{conversation_id}/model
Updates the AI model for a conversation.

**Request Body:**
```json
{
  "model": "openai/gpt-4"
}
```

**Response:**
```json
{
  "conversation_id": "conv_123456",
  "provider": "openrouter",
  "model": "openai/gpt-4",
  "available_models": ["openai/gpt-4", "openai/gpt-3.5-turbo"],
  "summary": {
    // ... updated conversation summary
  }
}
```

#### PUT /conversations/{conversation_id}/api-key
Updates the API key for a conversation.

**Request Body:**
```json
{
  "api_key": "sk-new-api-key"
}
```

**Response:**
```json
{
  "conversation_id": "conv_123456",
  "provider": "openrouter",
  "model": "openai/gpt-4",
  "available_models": ["openai/gpt-4", "openai/gpt-3.5-turbo"],
  "summary": {
    // ... updated conversation summary
  }
}
```

### History Management

#### GET /conversations/{conversation_id}/export
Exports conversation data.

**Response:**
```json
{
  "summary": {
    "conversation_id": "conv_123456",
    "provider": "openrouter",
    "selected_model": "openai/gpt-4",
    "selected_directory": "/path/to/project",
    "selected_files": ["main.py"],
    "persistent_files": ["main.py"],
    "question_history": [
      {
        "question": "What does this code do?",
        "status": "completed",
        "response": "This code implements...",
        "timestamp": "2023-12-01T14:30:22.123456",
        "tokens_used": 150,
        "processing_time": 2.34,
        "model_used": "openai/gpt-4"
      }
    ],
    "conversation_history": [
      {"role": "user", "content": "What does this code do?"},
      {"role": "assistant", "content": "This code implements..."}
    ]
  }
}
```

#### POST /conversations/import
Imports conversation data.

**Request Body:**
```json
{
  "provider": "openrouter",
  "model": "openai/gpt-4",
  "api_key": "sk-api-key",
  "conversation_history": [
    {"role": "user", "content": "What does this code do?"},
    {"role": "assistant", "content": "This code implements..."}
  ],
  "question_history": [
    {
      "question": "What does this code do?",
      "status": "completed",
      "response": "This code implements...",
      "timestamp": "2023-12-01T14:30:22.123456",
      "tokens_used": 150,
      "processing_time": 2.34,
      "model_used": "openai/gpt-4"
    }
  ],
  "selected_files": ["main.py"],
  "persistent_files": ["main.py"],
  "selected_directory": "/path/to/project"
}
```

**Response:**
```json
{
  "conversation_id": "conv_789012",
  "provider": "openrouter",
  "model": "openai/gpt-4",
  "available_models": ["openai/gpt-4", "openai/gpt-3.5-turbo"],
  "summary": {
    // ... imported conversation summary
  }
}
```

### Settings & Theme

#### GET /settings
Retrieves current settings.

**Response:**
```json
{
  "theme": "light",
  "provider": "openrouter",
  "model": "openai/gpt-4"
}
```

#### PUT /settings/theme
Updates theme setting.

**Request Body:**
```json
{
  "theme": "dark"
}
```

**Response:**
```json
{
  "theme": "dark",
  "message": "Theme updated"
}
```

#### POST /settings/theme/toggle
Toggles between light and dark theme.

**Response:**
```json
{
  "theme": "dark",
  "message": "Theme toggled to dark"
}
```

### System Messages

#### GET /system-messages
Lists available system messages.

**Response:**
```json
{
  "current": "systemmessage_default.txt",
  "messages": [
    {
      "filename": "systemmessage_default.txt",
      "display_name": "Default",
      "preview": "General purpose instructions for Code Chat conversations.",
      "length": 150,
      "is_current": true
    }
  ]
}
```

#### GET /system-messages/{filename}
Retrieves content of a specific system message.

**Response:**
```json
{
  "filename": "systemmessage_default.txt",
  "content": "You are an expert software engineer..."
}
```

#### PUT /system-messages/current
Sets the current system message.

**Request Body:**
```json
{
  "filename": "systemmessage_security.txt"
}
```

**Response:**
```json
{
  "current": "systemmessage_security.txt"
}
```

#### POST /system-messages
Creates a new system message.

**Request Body:**
```json
{
  "filename": "systemmessage_custom.txt",
  "content": "Custom system message content..."
}
```

**Response:**
```json
{
  "filename": "systemmessage_custom.txt"
}
```

#### DELETE /system-messages/{filename}
Deletes a system message.

**Response:**
```json
{
  "filename": "systemmessage_custom.txt",
  "deleted": true
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes and error messages:

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid directory: Directory does not exist"
}
```

#### 404 Not Found
```json
{
  "detail": "Conversation not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "AI processing failed: API key invalid"
}
```

#### 503 Service Unavailable
```json
{
  "detail": "AI processor not initialized"
}
```

## Rate Limiting

- API requests are subject to the rate limits of the underlying AI providers
- Implement exponential backoff for retry logic
- Monitor token usage through response metadata

## Data Types

### ConversationSummary
```typescript
interface ConversationSummary {
  conversation_id: string;
  provider: string;
  selected_model: string;
  selected_directory?: string;
  selected_files: string[];
  persistent_files: string[];
  question_history: QuestionStatus[];
  conversation_history: ChatMessage[];
}
```

### QuestionStatus
```typescript
interface QuestionStatus {
  question: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  response?: string;
  timestamp: string;
  tokens_used?: number;
  processing_time?: number;
  model_used?: string;
}
```

### ChatMessage
```typescript
interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}
```

## SDK Examples

### JavaScript/TypeScript
```javascript
// Create conversation
const response = await fetch('/conversations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    provider: 'openrouter',
    model: 'openai/gpt-4',
    apiKey: 'sk-your-key'
  })
});

// Ask question
const questionResponse = await fetch(`/conversations/${conversationId}/question`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'What does this code do?',
    selectedFiles: ['main.py'],
    persistent: false
  })
});
```

### Python
```python
import requests

# Create conversation
response = requests.post('http://localhost:8000/conversations', json={
    'provider': 'openrouter',
    'model': 'openai/gpt-4',
    'apiKey': 'sk-your-key'
})
conversation_id = response.json()['conversation_id']

# Ask question
question_response = requests.post(
    f'http://localhost:8000/conversations/{conversation_id}/question',
    json={
        'question': 'What does this code do?',
        'selectedFiles': ['main.py'],
        'persistent': False
    }
)
```

This API documentation covers the complete FastAPI backend interface used by the Code Chat with AI application. For implementation details, refer to the source code in the `web_backend/` directory.