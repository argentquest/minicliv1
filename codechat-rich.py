#!/usr/bin/env python3
"""
Rich + Typer Enhanced CLI Entry Point for Code Chat AI
Provides a standalone, beautiful command-line interface that can be called directly.

Usage:
    python codechat-rich.py analyze ./src "Explain what this code does"
    python codechat-rich.py config --validate
    python codechat-rich.py models --test gpt-4
"""

if __name__ == "__main__":
    try:
        from cli_rich import app
        app()
    except ImportError as e:
        print(f"ERROR: Missing dependencies for Rich CLI: {e}")
        print("Please install required packages:")
        print("  pip install rich typer")
        exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)