#!/usr/bin/env python3
"""
Startup script to ensure UI is visible.
"""

import tkinter as tk
import sys
import os

def main():
    """Start the UI with forced visibility."""
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