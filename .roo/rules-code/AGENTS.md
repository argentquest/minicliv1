# Code Mode Rules (Non-Obvious Only)

- **Provider Pattern**: AI providers MUST extend [`BaseAIProvider`](../../base_ai.py:23) and implement all abstract methods
- **Lazy Loading**: Use [`LazyCodebaseScanner`](../../lazy_file_scanner.py:35) for large codebases, [`CodebaseScanner`](../../file_scanner.py:9) for small ones
- **File Locking**: ALWAYS use [`safe_json_save()`](../../file_lock.py) and [`safe_json_load()`](../../file_lock.py) for JSON operations
- **Security**: Use [`SecurityUtils.mask_api_key()`](../../security_utils.py:27) for logging, never log raw API keys
- **Environment**: Use [`env_manager.update_single_var()`](../../env_manager.py:253) to update .env files safely
- **Pattern Matching**: [`pattern_matcher.is_tool_command()`](../../pattern_matcher.py:223) determines if questions need codebase context
- **Provider Factory**: [`AIProviderFactory.create_provider()`](../../ai.py:20) creates provider instances, supports registration
- **Context Logging**: Use [`@with_context`](../../logger.py:305) decorator and [`logger.set_context()`](../../logger.py:190) for structured logging
- **Persistent Files**: First conversation turn files persist across subsequent turns via [`AppState.set_persistent_files()`](../../models.py:157)
- **Tool Commands**: Questions matching TOOL_* env vars automatically get codebase context via pattern matching