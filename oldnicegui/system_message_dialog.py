"""
System message editor dialog for customizing AI behavior.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os

from theme import theme_manager
from icons import icon_manager
from simple_modern_ui import SimpleModernButton, SimpleModernLabel, show_simple_toast
from system_message_manager import system_message_manager

class SystemMessageDialog:
    """Dialog for editing custom system messages."""
    
    def __init__(self, parent):
        self.parent = parent
        
        self._create_dialog()
        self._load_current_message()
    
    def _create_dialog(self):
        """Create the system message editor dialog."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🤖 Custom System Message")
        self.window.geometry("800x700")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Apply theme
        theme = theme_manager.get_current_theme()
        self.window.configure(bg=theme.colors['bg_primary'])
        
        # Center the dialog
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # Main container
        self.main_container = tk.Frame(self.window, bg=theme.colors['bg_primary'])
        self.main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create sections
        self._create_header()
        self._create_editor()
        self._create_buttons()
        
        # Handle key bindings
        self.window.bind('<Control-s>', lambda e: self._save_message())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def _create_header(self):
        """Create the dialog header."""
        theme = theme_manager.get_current_theme()
        
        header_frame = tk.Frame(self.main_container, bg=theme.colors['bg_secondary'],
                               relief='flat', bd=1)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Header content
        header_content = tk.Frame(header_frame, bg=theme.colors['bg_secondary'])
        header_content.pack(fill='x', padx=20, pady=20)
        
        # Title
        title_label = SimpleModernLabel(header_content, text="🤖 Custom System Message")
        title_label.pack(anchor='w')
        
        # Info
        info_text = ("Customize how the AI behaves by creating a custom system message. "
                    "Use {codebase_content} where you want the code to be inserted.")
        info_label = SimpleModernLabel(header_content, text=info_text)
        info_label.pack(anchor='w', pady=(5, 0))
        
        # File info
        info = system_message_manager.get_system_message_info()
        if info['has_custom']:
            file_text = f"📄 Using custom message from: {info['file_path']}"
            status_color = theme.colors['success']
        else:
            file_text = f"📄 No custom message found. Will create: {info['file_path']}"
            status_color = theme.colors['text_secondary']
        
        file_label = SimpleModernLabel(header_content, text=file_text)
        file_label.pack(anchor='w', pady=(5, 0))
    
    def _create_editor(self):
        """Create the message editor."""
        theme = theme_manager.get_current_theme()
        
        # Editor frame
        editor_frame = tk.Frame(self.main_container, bg=theme.colors['bg_secondary'],
                               relief='flat', bd=1)
        editor_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Editor header
        editor_header = tk.Frame(editor_frame, bg=theme.colors['bg_secondary'])
        editor_header.pack(fill='x', padx=20, pady=(20, 10))
        
        # Tab selection
        self.tab_var = tk.StringVar(value="custom")
        
        tab_frame = tk.Frame(editor_header, bg=theme.colors['bg_secondary'])
        tab_frame.pack(fill='x')
        
        # Custom tab
        custom_radio = tk.Radiobutton(tab_frame, text="✏️ Custom Message", 
                                     variable=self.tab_var, value="custom",
                                     command=self._switch_tab,
                                     bg=theme.colors['bg_secondary'], 
                                     activebackground=theme.colors['bg_secondary'])
        custom_radio.pack(side='left', padx=(0, 20))
        
        # Default tab
        default_radio = tk.Radiobutton(tab_frame, text="📋 Default Message", 
                                      variable=self.tab_var, value="default",
                                      command=self._switch_tab,
                                      bg=theme.colors['bg_secondary'], 
                                      activebackground=theme.colors['bg_secondary'])
        default_radio.pack(side='left', padx=(0, 20))
        
        # Example tab
        example_radio = tk.Radiobutton(tab_frame, text="💡 Example Message", 
                                      variable=self.tab_var, value="example",
                                      command=self._switch_tab,
                                      bg=theme.colors['bg_secondary'], 
                                      activebackground=theme.colors['bg_secondary'])
        example_radio.pack(side='left')
        
        # Editor area
        editor_container = tk.Frame(editor_frame, bg=theme.colors['bg_secondary'])
        editor_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Text editor
        self.text_editor = scrolledtext.ScrolledText(
            editor_container, 
            wrap='word',
            bg=theme.colors['bg_tertiary'],
            relief='flat', 
            borderwidth=1,
            font=('Consolas', 10)
        )
        self.text_editor.pack(fill='both', expand=True)
        
        # Help text
        help_frame = tk.Frame(editor_frame, bg=theme.colors['bg_secondary'])
        help_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        help_text = ("💡 Tips:\n"
                    "• Use {codebase_content} placeholder where you want the code inserted\n"
                    "• Without {codebase_content}, code will be automatically appended\n"
                    "• Be specific about how you want the AI to analyze and respond")
        help_label = SimpleModernLabel(help_frame, text=help_text)
        help_label.pack(anchor='w')
    
    def _create_buttons(self):
        """Create dialog buttons."""
        theme = theme_manager.get_current_theme()
        
        button_frame = tk.Frame(self.main_container, bg=theme.colors['bg_secondary'],
                               relief='flat', bd=1)
        button_frame.pack(fill='x')
        
        # Button container
        button_container = tk.Frame(button_frame, bg=theme.colors['bg_secondary'])
        button_container.pack(pady=20)
        
        # Save button
        self.save_btn = SimpleModernButton(button_container, text="Save Custom Message", 
                                         command=self._save_message,
                                         style_type='primary', icon_action='save')
        self.save_btn.pack(side='left', padx=(0, 10))
        
        # Load example button
        example_btn = SimpleModernButton(button_container, text="Load Example", 
                                       command=self._load_example,
                                       icon_action='import')
        example_btn.pack(side='left', padx=(0, 10))
        
        # Delete custom button
        self.delete_btn = SimpleModernButton(button_container, text="Use Default", 
                                           command=self._delete_custom,
                                           icon_action='delete')
        self.delete_btn.pack(side='left', padx=(0, 10))
        
        # Cancel button
        cancel_btn = SimpleModernButton(button_container, text="Cancel", 
                                      command=self.window.destroy)
        cancel_btn.pack(side='left')
        
        # Help text
        help_text = "💡 Ctrl+S to save, Escape to cancel"
        help_label = SimpleModernLabel(button_frame, text=help_text)
        help_label.pack(pady=(0, 20))
    
    def _load_current_message(self):
        """Load the current system message into the editor."""
        info = system_message_manager.get_system_message_info()
        
        if info['has_custom']:
            self.text_editor.insert('1.0', info['custom_message'])
            self.save_btn.configure(text="Update Custom Message")
            self.delete_btn.configure(state='normal')
        else:
            self.text_editor.insert('1.0', "")
            self.save_btn.configure(text="Save Custom Message")
            self.delete_btn.configure(state='disabled')
    
    def _switch_tab(self):
        """Switch between different message views."""
        tab = self.tab_var.get()
        info = system_message_manager.get_system_message_info()
        
        # Clear current content
        self.text_editor.delete('1.0', tk.END)
        
        if tab == "custom":
            if info['has_custom']:
                self.text_editor.insert('1.0', info['custom_message'])
            self.text_editor.configure(state='normal')
            self.save_btn.configure(state='normal')
            self.delete_btn.configure(state='normal' if info['has_custom'] else 'disabled')
            
        elif tab == "default":
            self.text_editor.insert('1.0', info['default_message'])
            self.text_editor.configure(state='disabled')
            self.save_btn.configure(state='disabled')
            self.delete_btn.configure(state='disabled')
            
        elif tab == "example":
            example_content = system_message_manager.create_example_system_message()
            self.text_editor.insert('1.0', example_content)
            self.text_editor.configure(state='disabled')
            self.save_btn.configure(state='disabled')
            self.delete_btn.configure(state='disabled')
    
    def _load_example(self):
        """Load example message into the custom editor."""
        self.tab_var.set("custom")
        self.text_editor.configure(state='normal')
        self.text_editor.delete('1.0', tk.END)
        
        example_content = system_message_manager.create_example_system_message()
        self.text_editor.insert('1.0', example_content)
        
        self.save_btn.configure(state='normal', text="Save Custom Message")
        info = system_message_manager.get_system_message_info()
        self.delete_btn.configure(state='normal' if info['has_custom'] else 'disabled')
    
    def _save_message(self):
        """Save the custom system message."""
        content = self.text_editor.get('1.0', tk.END).strip()
        
        if not content:
            show_simple_toast(self.window, "Please enter a system message", "warning")
            return
        
        try:
            if system_message_manager.save_custom_system_message(content):
                self.window.destroy()
                show_simple_toast(self.parent, "Custom system message saved! 🤖", "info")
            else:
                show_simple_toast(self.window, "Failed to save system message", "error")
        except Exception as e:
            show_simple_toast(self.window, f"Error saving: {str(e)}", "error")
    
    def _delete_custom(self):
        """Delete custom system message and revert to default."""
        result = messagebox.askyesno(
            "Use Default Message",
            "This will delete your custom system message and use the default. Are you sure?",
            parent=self.window
        )
        
        if result:
            try:
                if system_message_manager.delete_custom_system_message():
                    self.window.destroy()
                    show_simple_toast(self.parent, "Reverted to default system message", "info")
                else:
                    show_simple_toast(self.window, "Failed to delete custom message", "error")
            except Exception as e:
                show_simple_toast(self.window, f"Error deleting: {str(e)}", "error")