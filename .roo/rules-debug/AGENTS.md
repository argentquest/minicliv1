# Debug Mode Rules (Non-Obvious Only)

- **Structured Logging**: Use [`logger.set_context()`](../../logger.py:190) to add debug context, logs go to `logs/structured.log`
- **Performance Logging**: Use [`@log_performance`](../../logger.py:315) decorator, metrics go to `logs/performance.log`
- **Security Masking**: [`SecurityUtils.mask_api_key()`](../../security_utils.py:27) prevents API key leaks in logs
- **Cache Debugging**: [`LazyCodebaseScanner.get_cache_stats()`](../../lazy_file_scanner.py:337) shows cache hit rates and performance
- **Provider Debug**: [`AIProcessor.get_provider_debug_info()`](../../ai.py:131) returns masked provider details
- **Pattern Analysis**: [`pattern_matcher.get_analysis_details()`](../../pattern_matcher.py:238) shows why questions trigger codebase context
- **Environment Validation**: [`env_validator.get_validation_summary()`](../../env_validator.py:265) provides detailed config validation
- **File Lock Debugging**: File operations use atomic writes with backup - check for `.backup` files on corruption
- **Error Sanitization**: [`SecurityUtils.sanitize_log_message()`](../../security_utils.py:168) removes sensitive data from error messages