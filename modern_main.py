#!/usr/bin/env python3
"""
Modern Code Chat with AI - Beautiful Edition

A stunning desktop application for chatting with AI models about codebases.
Features modern UI, dark/light themes, animations, and enhanced user experience.
"""

import tkinter as tk
import sys
import os

def main():
    """Main entry point for the modern application."""
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
            tk.messagebox.showerror("Dependency Error", error_msg)
        except:
            print(f"Error: {error_msg}", file=sys.stderr)
        
        sys.exit(1)
        
    except Exception as e:
        # Handle other startup errors
        error_msg = f"Application startup failed: {str(e)}"
        
        try:
            root = tk.Tk()
            root.withdraw()  # Hide main window
            tk.messagebox.showerror("Startup Error", error_msg)
        except:
            print(f"Error: {error_msg}", file=sys.stderr)
        
        sys.exit(1)

if __name__ == "__main__":
    main()