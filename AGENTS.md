# Repository Guidelines

## Project Structure & Module Organization
- Core CLI and UI entry points (`minicli.py`, `modern_main.py`, `start_ui.py`) sit at the repo root with helpers such as `logger.py`, `env_manager.py`, and `pattern_matcher.py`.
- Provider implementations live in `providers/`; each subclass `BaseAIProvider` while shared contracts stay in `base_ai.py` and `ai.py`.
- Generated outputs belong in `results/` or `logs/`; keep tracked artifacts reproducible and lightweight.
- Tests mirror modules under `tests/`; place fixtures beside the suites that need them.

## Build, Test, and Development Commands
- `venv/Scripts/python.exe -m pytest tests/ --tb=no -q` runs the full suite with concise reporting.
- `venv/Scripts/python.exe -m pytest tests/test_specific.py::TestClass::test_method -v` targets a single failure with verbose output.
- `python -m pytest --cov=. --cov-report=html --cov-exclude=tests/* --cov-exclude=subfolder/*` produces coverage data used in CI.
- `python modern_main.py` starts the desktop UI; use `python start_ui.py` to force the window and `python minicli.py --cli` for headless mode.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation, type hints on public APIs, and descriptive snake_case modules/functions; classes stay in PascalCase.
- Name providers after their services (e.g., `OpenRouterProvider`) and register them through `AIProviderFactory.create_provider`.
- Reuse `LazyCodebaseScanner` or `CodebaseScanner` instead of duplicating traversal logic, and document non-obvious behavior with brief docstrings.

## Testing Guidelines
- Pytest drives validation; adhere to `pytest.ini` patterns (`test_*.py`, `Test*` classes, `test_*` methods).
- Mark long or external calls with `@pytest.mark` (`unit`, `integration`, `slow`) to keep defaults fast.
- Review `htmlcov/index.html` before merging and close remaining gaps when coverage slips.

## Commit & Pull Request Guidelines
- Keep commit messages short and imperative (history examples: “Cleanup”, “Remove IDE folders”); squash noisy WIP commits.
- Pull requests should state intent, list impacted modules, reference issues when available, and attach UI screenshots for user-facing changes.
- Run the CI-equivalent commands locally, call out follow-ups, and request review from maintainers of the touched areas.

## Security & Configuration Tips
- Never log secrets; mask them with `SecurityUtils.mask_api_key()` and update `.env` values via `env_manager.update_single_var()`.
- Persist JSON through `safe_json_save()` / `safe_json_load()` to avoid corruption in concurrent runs.
- Honor contextual routing by checking `pattern_matcher.is_tool_command()` and remember first-turn persistence via `AppState.set_persistent_files()`.
