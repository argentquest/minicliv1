"""
Main entry point for running startcommands as a module.

This file allows the startcommands package to be executed with:
    python -m startcommands

It simply imports and runs the main function from main.py.
"""

from .main import main

if __name__ == "__main__":
    main()