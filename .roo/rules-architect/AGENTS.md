# Architect Mode Rules (Non-Obvious Only)

- **Provider Pattern**: AI providers MUST extend [`BaseAIProvider`](../../base_ai.py:23) - supports multiple providers via factory pattern
- **Dual Scanner Architecture**: [`CodebaseScanner`](../../file_scanner.py:9) for compatibility, [`LazyCodebaseScanner`](../../lazy_file_scanner.py:35) for performance - both implement same interface
- **Conversation State**: [`AppState.set_persistent_files()`](../../models.py:157) maintains file context across turns - first conversation files persist automatically
- **Pattern-Based Context**: [`pattern_matcher.is_tool_command()`](../../pattern_matcher.py:223) uses confidence scoring to determine when questions need codebase context
- **Environment Architecture**: [`EnvManager`](../../env_manager.py:25) preserves .env file structure and comments during updates
- **Security Layer**: [`SecurityUtils`](../../security_utils.py:8) provides comprehensive API key masking and sensitive data protection
- **Logging Architecture**: Structured logging with [`@with_context`](../../logger.py:305) decorator, separate files for errors/performance/structured logs
- **Provider Registration**: [`AIProviderFactory.register_provider()`](../../ai.py:47) allows runtime provider registration
- **File Locking**: All JSON operations use atomic writes with backup via [`file_lock.py`](../../file_lock.py:1) to prevent corruption
- **Validation Framework**: [`EnvValidator`](../../env_validator.py:32) provides extensible rule-based environment validation with suggestions