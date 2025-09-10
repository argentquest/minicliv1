# OpenRouter Integration Testing Guide

## Quick Configuration Test

1. **Run the configuration test:**
   ```bash
   cd C:\Code2025\minicli
   python test_openrouter.py
   ```
   
   This will verify:
   - Environment variables are loaded correctly
   - AI processor initializes with OpenRouter
   - Provider configuration is correct
   - Token support is enabled

## Full Application Test

### Step 1: Launch the Application
```bash
python minicli.py
# OR
python start_ui.py
```

### Step 2: Configure Provider (Optional)
The app should automatically use OpenRouter since `PROVIDER` defaults to "openrouter" in the code.

To explicitly test with OpenRouter, you can add this to your `.env` file:
```
PROVIDER=openrouter
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
   - Should show: `Ready • Openrouter • Input: X tokens • Output: Y tokens • Total: Z • Time: X.XXs`
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

Add to `.env`:
```
PROVIDER=tachyon
```

Restart the app and verify it attempts to use Tachyon (will likely fail without proper Tachyon URL).

## Expected Results

### ✅ Success Indicators:
- App launches without errors
- OpenRouter API calls succeed
- Token counts displayed in status bar
- Response time shown
- Status shows "Openrouter" provider name

### ❌ Common Issues:
- **"API key not configured"**: Check `.env` file has `API_KEY`
- **"Invalid API response"**: Check OpenRouter API key is valid
- **"Connection error"**: Check internet connection
- **No token info**: Check provider configuration

## Environment Variables Used

```bash
API_KEY=your_openrouter_api_key
PROVIDER=openrouter  # or tachyon
DEFAULT_MODEL=x-ai/grok-code-fast-1
MODELS=deepseek/deepseek-chat-v3.1,google/gemini-2.5-flash,x-ai/grok-code-fast-1
```

## Troubleshooting

1. **Check Console Output:**
   - Look for error messages in the terminal where you launched the app

2. **Verify Environment:**
   - Run `python test_openrouter.py` first

3. **Test API Key:**
   - Try making a direct API call to OpenRouter to verify the key works

4. **Check Network:**
   - Ensure you can access https://openrouter.ai/

## Advanced Testing

Test different models by updating `DEFAULT_MODEL` in `.env`:
- `deepseek/deepseek-chat-v3.1`
- `google/gemini-2.5-flash` 
- `x-ai/grok-code-fast-1`

Each should work with the same OpenRouter provider configuration.