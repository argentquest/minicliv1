# Comprehensive Testing Guide

This guide covers testing all components of the Code Chat AI application, including AI providers, file scanning, CLI interfaces, and integration testing.

## Quick Configuration Test

1. **Run the configuration validation:**
    ```bash
    cd C:\Code2025\minicli
    python codechat-rich.py config --validate
    ```

    This will verify:
    - Environment variables are loaded correctly
    - AI provider configuration is valid
    - File paths and permissions are correct
    - Required dependencies are available

## Full Application Test

### Step 1: Launch the Application
```bash
python minicli.py
# OR
python start_ui.py
```

### Step 2: Configure Provider
The app supports multiple AI providers. Configure your preferred provider in `.env`:

**For OpenRouter (default):**
```
PROVIDER=openrouter
API_KEY=sk-or-v1-your-openrouter-key-here
DEFAULT_MODEL=openai/gpt-4
```

**For Tachyon:**
```
PROVIDER=tachyon
API_KEY=your-tachyon-key-here
DEFAULT_MODEL=tachyon-model-name
```

### Step 3: Test Basic Functionality

1. **Select Directory:**
   - Click "Browse" button
   - Select a directory containing Python files
   - Verify files appear in the left panel
   - Select some files for analysis

2. **Ask a Simple Question:**
   - Type in the question box: "What does this code do?"
   - Click "Send Question" button

3. **Verify Provider Integration:**
    - Check the status bar at the bottom
    - Should show: `Ready • [Provider Name] • Input: X tokens • Output: Y tokens • Total: Z • Time: X.XXs`
    - For OpenRouter: Shows "Openrouter" as provider name
    - For Tachyon: Shows "Tachyon" as provider name
    - Verify response appears in the response area

### Step 4: Test Features

1. **Token Counting:**
   - Status bar should show input, output, and total tokens
   - Time should show execution duration

2. **Tool Variables:**
   - Use the "Quick Commands" dropdown
   - Should show actual command text instead of variable names
   - Try injecting a tool command

3. **Conversation History:**
   - Switch to "History" tab
   - Verify conversation is tracked
   - Try follow-up questions

### Step 5: Test Provider Switching

**Test OpenRouter to Tachyon switching:**
1. Update `.env`:
   ```
   PROVIDER=tachyon
   API_KEY=your-tachyon-key-here
   DEFAULT_MODEL=tachyon-model-name
   ```

2. Restart the app and verify:
   - Status bar shows "Tachyon" as provider
   - App attempts to connect to Tachyon service
   - Error handling works gracefully if Tachyon is unavailable

**Test Tachyon to OpenRouter switching:**
1. Switch back to OpenRouter configuration
2. Verify the app successfully connects and processes requests

## Expected Results

### ✅ Success Indicators:
- App launches without errors
- AI provider API calls succeed (OpenRouter or Tachyon)
- Token counts displayed in status bar
- Response time shown
- Status shows correct provider name ("Openrouter" or "Tachyon")
- File scanning works correctly
- System message selection functions
- Conversation history is maintained

### ❌ Common Issues:
- **"API key not configured"**: Check `.env` file has `API_KEY`
- **"Invalid API response"**: Check OpenRouter API key is valid
- **"Connection error"**: Check internet connection
- **No token info**: Check provider configuration

## Environment Variables Used

```bash
# Required
API_KEY=your_api_key_here
DEFAULT_MODEL=provider/model-name
MODELS=provider/model1,provider/model2,provider/model3

# Provider Configuration
PROVIDER=openrouter  # or tachyon
OPENROUTER_API_KEY=sk-or-v1-...  # Alternative OpenRouter key

# Optional Settings
MAX_TOKENS=4000
TEMPERATURE=0.7
UI_THEME=auto
IGNORE_FOLDERS=venv,.venv,node_modules,.git
DIR_SAVE=results
```

## Troubleshooting

1. **Check Console Output:**
    - Look for error messages in the terminal where you launched the app
    - Check log files in the `logs/` directory

2. **Verify Environment:**
    - Run `python codechat-rich.py config --validate` to check configuration
    - Run `python codechat-rich.py config --show` to display current settings

3. **Test API Key:**
    - For OpenRouter: Verify key starts with `sk-or-v1-`
    - For Tachyon: Verify your Tachyon API key is correct
    - Test with `python codechat-rich.py models --test model-name`

4. **Check Network:**
    - Ensure you can access provider endpoints
    - OpenRouter: https://openrouter.ai/
    - Tachyon: Verify your Tachyon service URL is accessible

## Advanced Testing

### Model Testing
Test different models by updating `DEFAULT_MODEL` in `.env`:

**OpenRouter Models:**
- `openai/gpt-3.5-turbo` - Fast, cost-effective
- `openai/gpt-4` - High-quality analysis
- `anthropic/claude-3-sonnet` - Balanced performance
- `anthropic/claude-3-opus` - Maximum quality
- `google/gemini-pro` - Google's latest model
- `deepseek/deepseek-chat` - Cost-effective alternative
- `x-ai/grok-2` - Specialized coding assistant

**Tachyon Models:**
- Configure according to your Tachyon service documentation

### CLI Testing
Test all CLI modes:
```bash
# Standard CLI
python minicli.py --cli --folder ./src --question "Analyze this code"

# Rich CLI
python codechat-rich.py analyze ./src "Analyze this code"

# Interactive Rich CLI
python codechat-rich.py interactive

# Configuration validation
python codechat-rich.py config --validate
```

### File Scanner Testing
Test different scanning scenarios:
- Large codebases with lazy scanner
- Various file types and extensions
- Ignore folder functionality
- File size limits