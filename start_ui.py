#!/usr/bin/env python3
"""
Code Chat with AI - Visibility-Enhanced Launcher

This is a specialized launcher for the Code Chat with AI application that
ensures the GUI window is properly visible and positioned. It addresses
common Tkinter window visibility issues that can occur on certain systems
or window managers.

Key features:
- Forces window to appear on top during startup
- Sets specific window positioning and sizing
- Provides user feedback about window visibility
- Includes comprehensive error handling with user guidance
- Graceful fallback for window manager compatibility issues

Usage:
    python start_ui.py

This launcher is particularly useful when:
- The main application window doesn't appear
- Users experience window positioning issues
- System window managers interfere with Tkinter window display
- Debugging window visibility problems

The launcher uses Tkinter's window management features to ensure
reliable window display across different platforms and configurations.
"""

import tkinter as tk
import sys
import os

def main():
    """
    Start the Code Chat application with enhanced window visibility.

    This function creates a Tkinter root window and applies several
    visibility-enhancing techniques to ensure the application window
    appears properly on screen. It handles window positioning, focus,
    and provides user feedback about the startup process.

    The visibility enhancements include:
    - Window positioning at specific coordinates (100, 100)
    - Forced window sizing (1200x900)
    - Topmost window attribute during startup
    - Explicit focus forcing
    - User feedback messages about window status

    Error handling:
    - Catches all exceptions during startup
    - Displays error messages in GUI dialogs when possible
    - Provides console fallback for error reporting
    - Prompts user to press Enter for clean exit on errors

    Returns:
        None - Function runs the Tkinter main loop or exits on error
    """
    try:
        print("Starting Code Chat with AI...")
        
        # Create root window
        root = tk.Tk()
        
        # Force window to front
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        
        # Position window at specific location
        root.geometry("1200x900+100+100")
        
        # Set window properties
        root.title("🤖 Code Chat with AI - Modern Edition")
        
        # Import and create app
        from minicli import SimpleModernCodeChatApp
        app = SimpleModernCodeChatApp(root)
        
        # Force focus
        root.focus_force()
        
        print("Application window should now be visible!")
        print("If you still don't see it, check your taskbar or try Alt+Tab")
        
        # Start the application
        app.run()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error in message box
        try:
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showerror("Startup Error", f"Failed to start application:\n\n{str(e)}")
        except:
            pass
        
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()