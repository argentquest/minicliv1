# Ask Mode Rules (Non-Obvious Only)

- **Entry Points**: [`minicli.py`](../../minicli.py:1) is main GUI, [`modern_main.py`](../../modern_main.py:1) is launcher, [`start_ui.py`](../../start_ui.py:1) forces window visibility
- **CLI Modes**: `--cli` for standard CLI, `--rich-cli` for enhanced CLI with progress bars and syntax highlighting
- **Provider Architecture**: [`AIProviderFactory`](../../ai.py:11) manages multiple AI providers (OpenRouter, Tachyon), not just OpenAI
- **File Scanning**: Two scanners - [`CodebaseScanner`](../../file_scanner.py:9) for small projects, [`LazyCodebaseScanner`](../../lazy_file_scanner.py:35) for large ones
- **Conversation Context**: [`AppState.persistent_selected_files`](../../models.py:123) maintains file context across conversation turns
- **Tool Commands**: TOOL_* environment variables define prompts that trigger automatic codebase context inclusion
- **Environment Management**: [`EnvManager`](../../env_manager.py:25) preserves comments and formatting when updating .env files
- **Pattern Matching**: [`ToolCommandPatternMatcher`](../../pattern_matcher.py:18) uses ML-like confidence scoring to detect code analysis requests
- **Security**: All API keys are masked in logs using [`SecurityUtils`](../../security_utils.py:8) - never logs raw keys