# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build/Test Commands

```bash
# Run tests (single test)
venv/Scripts/python.exe -m pytest tests/test_specific.py::TestClass::test_method -v

# Run all tests
venv/Scripts/python.exe -m pytest tests/ --tb=no -q

# Run with coverage
python -m pytest --cov=. --cov-report=html --cov-exclude=tests/* --cov-exclude=subfolder/*

# Launch application
python modern_main.py
python start_ui.py  # Force window visibility
python minicli.py --cli  # CLI mode
python codechat-rich.py  # Rich CLI mode
```

## Critical Project-Specific Patterns

- **Provider Pattern**: AI providers MUST extend [`BaseAIProvider`](base_ai.py:23) and implement all abstract methods
- **Lazy Loading**: Use [`LazyCodebaseScanner`](lazy_file_scanner.py:35) for large codebases, [`CodebaseScanner`](file_scanner.py:9) for small ones
- **File Locking**: ALWAYS use [`safe_json_save()`](file_lock.py) and [`safe_json_load()`](file_lock.py) for JSON operations
- **Security**: Use [`SecurityUtils.mask_api_key()`](security_utils.py:27) for logging, never log raw API keys
- **Environment**: Use [`env_manager.update_single_var()`](env_manager.py:253) to update .env files safely
- **Pattern Matching**: [`pattern_matcher.is_tool_command()`](pattern_matcher.py:223) determines if questions need codebase context

## Non-Standard Architecture

- **Persistent Files**: First conversation turn files persist across subsequent turns via [`AppState.set_persistent_files()`](models.py:157)
- **Dual Scanners**: Standard scanner for compatibility, lazy scanner for performance - both implement same interface
- **Provider Factory**: [`AIProviderFactory.create_provider()`](ai.py:20) creates provider instances, supports registration
- **Context Logging**: Use [`@with_context`](logger.py:305) decorator and [`logger.set_context()`](logger.py:190) for structured logging
- **Tool Commands**: Questions matching TOOL_* env vars automatically get codebase context via pattern matching

## Testing Requirements

- Tests MUST be in same directory as source files for vitest compatibility
- Use [`conftest.py`](tests/conftest.py:1) fixtures for consistent test setup
- Mock AI responses using [`mock_requests_post`](tests/conftest.py:104) fixture
- Test files follow `test_*.py` pattern with `Test*` classes