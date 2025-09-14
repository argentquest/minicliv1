# Contributing to Code Chat AI

Thank you for your interest in contributing to Code Chat AI! We welcome contributions from the community. This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** from `main`
4. **Make your changes** following our guidelines
5. **Test your changes** thoroughly
6. **Submit a pull request**

## Contribution Workflow

```mermaid
flowchart TD
    A[Identify Issue/Feature] --> B{Fork Repository}
    B --> C[Clone Fork Locally]
    C --> D[Create Feature Branch<br/>git checkout -b feature/name]
    D --> E[Set Up Development Environment]
    E --> F[Make Code Changes]
    F --> G[Follow Code Style Guidelines]
    G --> H[Write/Update Tests]
    H --> I[Run Test Suite<br/>python -m pytest tests/]
    I --> J{Tests Pass?}
    J -->|No| K[Fix Issues]
    K --> I
    J -->|Yes| L[Update Documentation]
    L --> M[Commit Changes<br/>git commit -m "Add: feature description"]
    M --> N[Push to Fork<br/>git push origin feature/name]
    N --> O[Create Pull Request]
    O --> P[PR Review Process]
    P --> Q{Approved?}
    Q -->|No| R[Address Review Comments]
    R --> F
    Q -->|Yes| S[Merge to Main]
    S --> T[Contribution Complete]

    style A fill:#e1f5fe
    style T fill:#c8e6c9
```

## 📋 Development Setup

### Prerequisites
- Python 3.7 or higher
- Git
- API key from [OpenRouter](https://openrouter.ai/) or your preferred AI provider

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/code-chat-ai.git
cd code-chat-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Copy environment template
cp .envTemplate .env
# Edit .env with your API keys
```

### Running the Application
```bash
# GUI Mode
python modern_main.py

# CLI Mode
python codechat-rich.py interactive

# Run tests
python -m pytest tests/ -v
```

## 🛠️ Development Guidelines

### Code Style
- Follow [PEP 8](https://pep8.org/) guidelines
- Use type hints where appropriate
- Add docstrings for all public methods
- Keep line length under 88 characters
- Use meaningful variable and function names

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Reference issue numbers when applicable
- Example: `Fix: Resolve memory leak in file scanner (#123)`

### Testing
- Write tests for new features
- Ensure all existing tests pass
- Aim for good test coverage
- Test both GUI and CLI interfaces

## 🏗️ Architecture Guidelines

### Provider Pattern
AI providers MUST extend `BaseAIProvider` and implement all abstract methods:

```python
from base_ai import BaseAIProvider

class MyProvider(BaseAIProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)

    def send_request(self, messages: List[Dict], **kwargs) -> Dict:
        # Implementation here
        pass
```

### File Handling
- Use `safe_json_save()` and `safe_json_load()` for JSON operations
- Use `LazyCodebaseScanner` for large codebases, `CodebaseScanner` for small ones
- Always mask API keys in logs using `SecurityUtils.mask_api_key()`

### Error Handling
- Use structured logging with `@with_context` decorator
- Provide meaningful error messages
- Handle network timeouts gracefully
- Validate user input thoroughly

## 📝 Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following the guidelines above
3. **Test thoroughly** - run the full test suite
4. **Update documentation** if needed
5. **Submit a pull request** with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots for UI changes
   - Test results

### PR Review Process
- All PRs require review before merging
- CI checks must pass
- At least one maintainer approval required
- Reviewers may request changes

## 🐛 Reporting Issues

### Bug Reports
- Use the bug report template
- Include steps to reproduce
- Provide system information
- Include error messages and logs

### Feature Requests
- Use the feature request template
- Describe the problem you're trying to solve
- Explain why this feature would be valuable
- Consider alternative solutions

## 📚 Documentation

- Update README.md for new features
- Add docstrings to new functions/classes
- Update CLI_USAGE.md for CLI changes
- Update TESTING_GUIDE.md for testing changes

## 🤝 Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

## 🙏 Recognition

Contributors will be recognized in the project documentation and release notes. Thank you for helping make Code Chat AI better!

---

For questions or help, please open an issue or join our community discussions.