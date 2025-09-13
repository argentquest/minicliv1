#!/usr/bin/env python3
"""
Modern Code Chat with AI - Primary Application Launcher

This is the primary entry point for the Code Chat with AI desktop application.
It provides a clean, simple launcher that initializes the main application
with proper error handling for missing dependencies and startup failures.

The application features:
- Modern GUI with tabbed interface for conversation management
- Support for multiple AI providers (OpenAI, Anthropic, etc.)
- Advanced codebase scanning with lazy loading for performance
- Customizable system messages and conversation history
- Theme support and secure API key management

Usage:
    python modern_main.py

This launcher handles:
- Dependency validation and user-friendly error messages
- Graceful error recovery with GUI error dialogs
- Clean application initialization and startup
"""

import tkinter as tk
from tkinter import messagebox
import sys

def main():
    """
    Main entry point for the modern Code Chat application.

    Initializes the Tkinter root window, creates the main application instance,
    and starts the GUI event loop. Includes comprehensive error handling for
    dependency issues and startup failures.

    Handles two types of errors:
    1. ImportError: Missing dependencies with installation instructions
    2. General exceptions: Application startup failures with error details

    The function ensures that error messages are displayed to the user
    through GUI dialogs when possible, falling back to console output.
    """
    try:
        root = tk.Tk()
        
        # Import the simplified modern application class
        from minicli import SimpleModernCodeChatApp

        # Create and run the modern application
        app = SimpleModernCodeChatApp(root)
        app.run()
        
    except ImportError as e:
        # Handle missing dependencies
        error_msg = f"Missing required dependency: {str(e)}\n\nPlease install dependencies with:\npip install -r requirements.txt"
        
        # Show error in GUI if possible, otherwise print to console
        try:
            root = tk.Tk()
            root.withdraw()  # Hide main window
            messagebox.showerror("Dependency Error", error_msg)
        except:
            print(f"Error: {error_msg}", file=sys.stderr)
        
        sys.exit(1)
        
    except Exception as e:
        # Handle other startup errors
        error_msg = f"Application startup failed: {str(e)}"
        
        try:
            root = tk.Tk()
            root.withdraw()  # Hide main window
            messagebox.showerror("Startup Error", error_msg)
        except:
            print(f"Error: {error_msg}", file=sys.stderr)
        
        sys.exit(1)

if __name__ == "__main__":
    main()