#!/usr/bin/env python3
"""
Enhanced UI Launcher - Forces Window Visibility

This launcher ensures the Code Chat AI application window is always visible
and properly positioned, addressing common Tkinter window visibility issues
on various operating systems.

Features:
- Forces window to stay on top during initialization
- Centers window on screen
- Ensures proper window focus and visibility
- Enhanced error handling with detailed logging
- Automatic window positioning and sizing

Usage:
    python start_ui.py

This launcher is particularly useful when the main application window
doesn't appear or stays hidden behind other windows.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import traceback
import time

def force_window_visibility(root, title="Code Chat AI"):
    """
    Force the Tkinter window to be visible and properly positioned.

    Args:
        root: Tkinter root window
        title: Window title
    """
    try:
        # Set window properties for visibility
        root.title(title)
        root.attributes('-topmost', True)  # Keep on top during init
        root.lift()  # Bring to front
        root.focus_force()  # Force focus

        # Set window size and position
        window_width = 1200
        window_height = 800

        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate center position
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)

        # Set window geometry
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Force update and small delay to ensure visibility
        root.update()
        time.sleep(0.1)

        # Remove always-on-top after initialization
        root.attributes('-topmost', False)

        return True

    except Exception as e:
        print(f"Warning: Could not force window visibility: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point with enhanced window visibility forcing.

    This function creates the Tkinter application with additional steps
    to ensure the window is visible and properly positioned on screen.
    """
    root = None

    try:
        print("🚀 Starting Code Chat AI with enhanced UI visibility...")

        # Create root window
        root = tk.Tk()

        # Force window visibility before importing the main application
        force_window_visibility(root, "Code Chat AI - Initializing...")

        print("✅ Window visibility forced successfully")

        # Import the main application
        print("📦 Loading application modules...")
        from minicli import SimpleModernCodeChatApp

        # Update window title
        root.title("Code Chat AI")

        print("🏗️  Creating application instance...")
        app = SimpleModernCodeChatApp(root)

        # Ensure window stays visible after app creation
        root.lift()
        root.focus_force()

        print("🎯 Application initialized successfully")
        print("💡 Window should now be visible and focused")

        # Start the application
        app.run()

    except ImportError as e:
        # Handle missing dependencies
        error_msg = f"Missing required dependency: {str(e)}\n\nPlease install dependencies with:\npip install -r requirements.txt"

        print(f"❌ Import Error: {error_msg}", file=sys.stderr)

        # Show error in GUI if possible
        try:
            if root is None:
                root = tk.Tk()
                root.withdraw()

            force_window_visibility(root, "Dependency Error")
            messagebox.showerror("Dependency Error", error_msg)
        except Exception as gui_error:
            print(f"Could not show GUI error dialog: {gui_error}", file=sys.stderr)
            print(f"Error: {error_msg}", file=sys.stderr)

        sys.exit(1)

    except Exception as e:
        # Handle other startup errors
        error_details = traceback.format_exc()
        error_msg = f"Application startup failed: {str(e)}\n\nDetails:\n{error_details}"

        print(f"❌ Startup Error: {error_msg}", file=sys.stderr)

        # Show error in GUI if possible
        try:
            if root is None:
                root = tk.Tk()
                root.withdraw()

            force_window_visibility(root, "Startup Error")
            messagebox.showerror("Startup Error", str(e))
        except Exception as gui_error:
            print(f"Could not show GUI error dialog: {gui_error}", file=sys.stderr)
            print(f"Error: {error_msg}", file=sys.stderr)

        sys.exit(1)

if __name__ == "__main__":
    main()