"""
Enhanced settings dialog for editing .env file variables.
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List
import os

from theme import theme_manager
from icons import icon_manager
from env_manager import env_manager
from simple_modern_ui import SimpleModernButton, SimpleModernLabel, show_simple_toast

class EnvSettingsDialog:
    """Enhanced settings dialog for editing .env variables."""
    
    def __init__(self, parent, save_callback=None):
        self.parent = parent
        self.save_callback = save_callback
        self.env_vars = {}
        self.entry_widgets = {}
        
        self._create_dialog()
        self._load_env_data()
    
    def _create_dialog(self):
        """Create the settings dialog window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("⚙️ Environment Settings")
        self.window.geometry("700x600")
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
        
        # Create header
        self._create_header()
        
        # Create scrollable content area
        self._create_scrollable_content()
        
        # Create buttons
        self._create_buttons()
        
        # Handle key bindings
        self.window.bind('<Control-s>', lambda e: self._save_settings())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def _create_header(self):
        """Create the dialog header."""
        theme = theme_manager.get_current_theme()
        
        header_frame = tk.Frame(self.main_container, bg=theme.colors['bg_secondary'],
                               relief='flat', bd=1)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title and info
        title_container = tk.Frame(header_frame, bg=theme.colors['bg_secondary'])
        title_container.pack(fill='x', padx=20, pady=20)
        
        # Title
        title_label = SimpleModernLabel(title_container, text="⚙️ Environment Settings")
        title_label.pack(anchor='w')
        
        # Subtitle
        subtitle_text = "Configure your application settings by editing the .env file variables below:"
        subtitle_label = SimpleModernLabel(title_container, text=subtitle_text)
        subtitle_label.pack(anchor='w', pady=(5, 0))
        
        # File path info
        env_path = os.path.abspath(env_manager.env_path)
        path_text = f"📄 File: {env_path}"
        path_label = SimpleModernLabel(title_container, text=path_text)
        path_label.pack(anchor='w', pady=(5, 0))
    
    def _create_scrollable_content(self):
        """Create scrollable content area for environment variables."""
        theme = theme_manager.get_current_theme()
        
        # Create frame for scrollable content
        content_frame = tk.Frame(self.main_container, bg=theme.colors['bg_primary'])
        content_frame.pack(fill='both', expand=True)
        
        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(content_frame, bg=theme.colors['bg_primary'],
                               highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(content_frame, orient='vertical', 
                                      command=self.canvas.yview)
        
        # Create scrollable frame
        self.scrollable_frame = tk.Frame(self.canvas, bg=theme.colors['bg_primary'])
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self._bind_mousewheel()
    
    def _bind_mousewheel(self):
        """Bind mousewheel events to canvas."""
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', bind_to_mousewheel)
        self.canvas.bind('<Leave>', unbind_from_mousewheel)
    
    def _create_buttons(self):
        """Create dialog buttons."""
        theme = theme_manager.get_current_theme()
        
        button_frame = tk.Frame(self.main_container, bg=theme.colors['bg_secondary'],
                               relief='flat', bd=1)
        button_frame.pack(fill='x', pady=(20, 0))
        
        # Button container
        button_container = tk.Frame(button_frame, bg=theme.colors['bg_secondary'])
        button_container.pack(pady=15)
        
        # Save button
        self.save_btn = SimpleModernButton(button_container, text="Save Changes", 
                                         command=self._save_settings,
                                         style_type='primary', icon_action='save')
        self.save_btn.pack(side='left', padx=(0, 10))
        
        # Cancel button
        cancel_btn = SimpleModernButton(button_container, text="Cancel", 
                                      command=self.window.destroy)
        cancel_btn.pack(side='left', padx=(0, 10))
        
        # Reset button
        reset_btn = SimpleModernButton(button_container, text="Reset to Defaults", 
                                     command=self._reset_to_defaults,
                                     icon_action='refresh')
        reset_btn.pack(side='left')
        
        # Help text
        help_text = "💡 Tip: Use Ctrl+S to save, Escape to cancel"
        help_label = SimpleModernLabel(button_frame, text=help_text)
        help_label.pack(pady=(0, 15))
    
    def _load_env_data(self):
        """Load environment data and create input fields."""
        # Load environment variables
        self.env_vars = env_manager.load_env_file()
        descriptions = env_manager.get_env_descriptions()
        
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.entry_widgets.clear()
        
        theme = theme_manager.get_current_theme()
        
        # Create input fields for each environment variable
        row = 0
        for key, value in self.env_vars.items():
            # Create container for this env var
            var_frame = tk.Frame(self.scrollable_frame, bg=theme.colors['bg_secondary'],
                                relief='flat', bd=1)
            var_frame.pack(fill='x', pady=5, padx=5)
            
            # Create content frame
            content_frame = tk.Frame(var_frame, bg=theme.colors['bg_secondary'])
            content_frame.pack(fill='x', padx=15, pady=15)
            
            # Variable name and description
            name_frame = tk.Frame(content_frame, bg=theme.colors['bg_secondary'])
            name_frame.pack(fill='x', pady=(0, 8))
            
            # Variable name
            name_label = SimpleModernLabel(name_frame, text=f"🔧 {key}")
            name_label.pack(side='left')
            
            # Description
            description = descriptions.get(key, "")
            if description:
                desc_label = SimpleModernLabel(name_frame, text=f"- {description}")
                desc_label.pack(side='left', padx=(10, 0))
            
            # Input field
            if key == 'API_KEY':
                # Special handling for API key (password field)
                entry = tk.Entry(content_frame, show="*", width=80,
                               bg=theme.colors['bg_tertiary'], relief='flat', bd=1)
            elif key in ['MODELS', 'IGNORE_FOLDERS'] and ',' in value:
                # Multi-line for comma-separated values
                entry = tk.Text(content_frame, height=3, width=80, wrap='word',
                               bg=theme.colors['bg_tertiary'], relief='flat', bd=1)
                # Format comma-separated values on separate lines
                formatted_value = value.replace(',', ',\n')
                entry.insert('1.0', formatted_value)
            else:
                # Regular entry field
                entry = tk.Entry(content_frame, width=80,
                               bg=theme.colors['bg_tertiary'], relief='flat', bd=1)
            
            entry.pack(fill='x', pady=(0, 5))
            
            # Set value for regular entry fields
            if isinstance(entry, tk.Entry):
                entry.insert(0, value)
            
            # Store reference to entry widget
            self.entry_widgets[key] = entry
            
            # Add validation info for special fields
            if key in ['MAX_TOKENS', 'TEMPERATURE', 'UI_THEME']:
                if key == 'MAX_TOKENS':
                    info_text = "ℹ️ Enter a number between 1 and 4000"
                elif key == 'TEMPERATURE':
                    info_text = "ℹ️ Enter a decimal between 0.0 and 1.0"
                elif key == 'UI_THEME':
                    info_text = "ℹ️ Enter 'light' or 'dark'"
                
                info_label = SimpleModernLabel(content_frame, text=info_text)
                info_label.pack(anchor='w')
            
            row += 1
        
        # Add new variable section
        self._create_add_new_section()
        
        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _create_add_new_section(self):
        """Create section for adding new environment variables."""
        theme = theme_manager.get_current_theme()
        
        # Add new variable section
        add_frame = tk.Frame(self.scrollable_frame, bg=theme.colors['bg_accent'],
                            relief='flat', bd=1)
        add_frame.pack(fill='x', pady=(20, 5), padx=5)
        
        add_content = tk.Frame(add_frame, bg=theme.colors['bg_accent'])
        add_content.pack(fill='x', padx=15, pady=15)
        
        # Title
        add_title = SimpleModernLabel(add_content, text="➕ Add New Variable")
        add_title.pack(anchor='w', pady=(0, 10))
        
        # Key input
        key_frame = tk.Frame(add_content, bg=theme.colors['bg_accent'])
        key_frame.pack(fill='x', pady=(0, 5))
        
        SimpleModernLabel(key_frame, text="Variable Name:").pack(side='left')
        self.new_key_entry = tk.Entry(key_frame, width=30,
                                     bg=theme.colors['bg_tertiary'], relief='flat', bd=1)
        self.new_key_entry.pack(side='left', padx=(10, 0))
        
        # Value input
        value_frame = tk.Frame(add_content, bg=theme.colors['bg_accent'])
        value_frame.pack(fill='x', pady=(0, 10))
        
        SimpleModernLabel(value_frame, text="Value:").pack(side='left')
        self.new_value_entry = tk.Entry(value_frame, width=50,
                                       bg=theme.colors['bg_tertiary'], relief='flat', bd=1)
        self.new_value_entry.pack(side='left', padx=(10, 0))
        
        # Add button
        add_btn = SimpleModernButton(add_content, text="Add Variable", 
                                   command=self._add_new_variable,
                                   icon_action='new')
        add_btn.pack(anchor='w')
    
    def _add_new_variable(self):
        """Add a new environment variable."""
        key = self.new_key_entry.get().strip()
        value = self.new_value_entry.get().strip()
        
        if not key:
            show_simple_toast(self.window, "Please enter a variable name", "warning")
            return
        
        if key in self.env_vars:
            show_simple_toast(self.window, f"Variable '{key}' already exists", "warning")
            return
        
        # Add to env_vars and reload the display
        self.env_vars[key] = value
        self._load_env_data()
        
        # Clear the input fields
        self.new_key_entry.delete(0, tk.END)
        self.new_value_entry.delete(0, tk.END)
        
        show_simple_toast(self.window, f"Added variable '{key}'", "info")
    
    def _save_settings(self):
        """Save the environment settings."""
        try:
            # Collect values from all entry widgets
            new_env_vars = {}
            
            for key, entry in self.entry_widgets.items():
                if isinstance(entry, tk.Text):
                    # Handle text widgets (multi-line)
                    value = entry.get('1.0', tk.END).strip()
                    # Convert back to comma-separated format
                    if key in ['MODELS', 'IGNORE_FOLDERS']:
                        value = ','.join([line.strip() for line in value.split('\n') if line.strip()])
                else:
                    # Handle entry widgets
                    value = entry.get().strip()
                
                # Validate the value
                is_valid, error_msg = env_manager.validate_env_var(key, value)
                if not is_valid:
                    show_simple_toast(self.window, f"Invalid {key}: {error_msg}", "error")
                    return
                
                new_env_vars[key] = value
            
            # Save to .env file
            if env_manager.save_env_file(new_env_vars):
                # Reload environment variables in the main app
                if self.save_callback:
                    self.save_callback(new_env_vars)
                
                self.window.destroy()
                show_simple_toast(self.parent, "Environment settings saved successfully! ✅", "info")
            else:
                show_simple_toast(self.window, "Failed to save .env file", "error")
                
        except Exception as e:
            show_simple_toast(self.window, f"Error saving settings: {str(e)}", "error")
    
    def _reset_to_defaults(self):
        """Reset environment variables to defaults."""
        result = messagebox.askyesno(
            "Reset to Defaults",
            "This will reset all environment variables to their default values. Are you sure?",
            parent=self.window
        )
        
        if result:
            # Backup current .env file
            try:
                import shutil
                backup_path = f"{env_manager.env_path}.backup"
                shutil.copy2(env_manager.env_path, backup_path)
            except:
                pass
            
            # Remove current .env file and create default
            try:
                if os.path.exists(env_manager.env_path):
                    os.remove(env_manager.env_path)
                env_manager._create_default_env()
                self._load_env_data()
                show_simple_toast(self.window, "Reset to default values", "info")
            except Exception as e:
                show_simple_toast(self.window, f"Error resetting: {str(e)}", "error")