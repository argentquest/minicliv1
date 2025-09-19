"""
Context Selection Dialog

A popup dialog for selecting files that will be used as context for AI conversations.
Replaces the left panel file selection with a modal dialog approach.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Callable, Optional
import os

from theme import theme_manager
from simple_modern_ui import SimpleModernButton, SimpleModernLabel, SimpleFilesList
from lazy_file_scanner import CodebaseScanner, LazyCodebaseScanner


class ContextDialog:
    """Dialog for selecting context files."""
    
    def __init__(self, parent, current_context: List[str] = None, context_change_callback: Optional[Callable] = None):
        """
        Initialize the context dialog.
        
        Args:
            parent: Parent window
            current_context: Currently selected context files
            context_change_callback: Callback when context changes
        """
        self.parent = parent
        self.context_change_callback = context_change_callback
        self.current_context = current_context or []
        self.new_context = []
        self.scanner = CodebaseScanner()
        self.lazy_scanner = None
        
        # Dialog window
        self.dialog = None
        self.result = None  # Will be 'ok', 'cancel', or None
        
        # UI components
        self.files_list = None
        self.dir_label = None
        self.selected_directory = ""
        self.codebase_files = []
        
        self._create_dialog()
        
    def _create_dialog(self):
        """Create the context dialog window."""
        theme = theme_manager.get_current_theme()
        
        # Create dialog window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Context Files")
        self.dialog.geometry("500x500")
        self.dialog.resizable(True, True)
        self.dialog.configure(bg=theme.colors['bg_primary'])
        
        # Modern styling
        try:
            # Try to remove window decorations for custom styling
            self.dialog.overrideredirect(False)  # Keep decorations for now
            # Add subtle border effect
            self.dialog.configure(relief='flat', bd=2, highlightbackground='#E0E0E0', highlightthickness=1)
        except:
            pass
        
        # Make it modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self._center_dialog()
        
        # Create UI components
        self._create_dialog_ui()
        
        # Load current context if any
        if self.current_context:
            self._load_current_context()
            
    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Use our explicitly set dialog size
        dialog_width = 500
        dialog_height = 500
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Ensure dialog doesn't go off screen
        x = max(0, x)
        y = max(0, y)
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
    def _create_dialog_ui(self):
        """Create the dialog UI components."""
        theme = theme_manager.get_current_theme()
        
        # Main container with modern styling
        main_frame = tk.Frame(self.dialog, bg=theme.colors['bg_primary'], relief='flat')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Configure grid weights
        main_frame.rowconfigure(2, weight=1)  # Files list area
        main_frame.columnconfigure(0, weight=1)
        
        # Title with modern styling
        title_label = SimpleModernLabel(main_frame, text="🗂️ Select Context Files")
        title_label.configure(font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, sticky='w', pady=(0, 20))
        
        # Directory selection section
        self._create_directory_section(main_frame)
        
        # Files list
        self.files_list = SimpleFilesList(main_frame, 
                                         selection_callback=self._on_file_selection_change)
        self.files_list.grid(row=2, column=0, sticky='nsew', pady=(10, 0))
        
        # Current context info
        self._create_context_info(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
        
    def _create_directory_section(self, parent):
        """Create directory selection section."""
        theme = theme_manager.get_current_theme()
        
        dir_frame = tk.Frame(parent, bg=theme.colors['bg_secondary'], relief='flat', bd=0)
        dir_frame.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        
        # Add subtle rounded appearance
        dir_frame.configure(relief='raised', bd=1)
        
        dir_container = tk.Frame(dir_frame, bg=theme.colors['bg_secondary'])
        dir_container.pack(fill='x', padx=15, pady=15)
        
        # Directory info
        dir_info_frame = tk.Frame(dir_container, bg=theme.colors['bg_secondary'])
        dir_info_frame.pack(fill='x', pady=(0, 10))
        
        SimpleModernLabel(dir_info_frame, text="📁 Codebase Directory:").pack(side='left')
        
        self.dir_label = SimpleModernLabel(dir_info_frame, text="No directory selected")
        self.dir_label.pack(side='left', padx=(10, 0))
        
        # Directory buttons
        button_frame = tk.Frame(dir_container, bg=theme.colors['bg_secondary'])
        button_frame.pack()
        
        browse_btn = SimpleModernButton(button_frame, text="Browse", 
                                      command=self._select_directory, 
                                      style_type='primary', icon_action='folder',
                                      tooltip="Browse and select a directory containing your code files")
        browse_btn.pack(side='left', padx=(0, 10))
        
        refresh_btn = SimpleModernButton(button_frame, text="Refresh", 
                                       command=self._refresh_codebase,
                                       icon_action='refresh',
                                       tooltip="Refresh the file list from the current directory")
        refresh_btn.pack(side='left')
        
    def _create_context_info(self, parent):
        """Create current context information display."""
        theme = theme_manager.get_current_theme()
        
        info_frame = tk.Frame(parent, bg=theme.colors['bg_secondary'], relief='solid', bd=1)
        info_frame.grid(row=3, column=0, sticky='ew', pady=(10, 0))
        
        info_container = tk.Frame(info_frame, bg=theme.colors['bg_secondary'])
        info_container.pack(fill='x', padx=15, pady=10)
        
        # Current context label
        context_label = SimpleModernLabel(info_container, text="Current Context:")
        context_label.pack(anchor='w', pady=(0, 5))
        
        # Context files display
        self.context_display = tk.Text(info_container, height=3, wrap=tk.WORD,
                                      bg=theme.colors['bg_primary'],
                                      fg=theme.colors['text_secondary'],
                                      font=("Arial", 9),
                                      state='disabled')
        self.context_display.pack(fill='x')
        
        self._update_context_display()
        
    def _create_buttons(self, parent):
        """Create dialog buttons."""
        theme = theme_manager.get_current_theme()
        
        button_frame = tk.Frame(parent, bg=theme.colors['bg_primary'])
        button_frame.grid(row=4, column=0, sticky='ew', pady=(15, 0))
        
        # Left side - Clear button
        clear_btn = SimpleModernButton(button_frame, text="Clear Selected", 
                                     command=self._clear_selection,
                                     style_type='secondary',
                                     tooltip="Clear all selected files from the context")
        clear_btn.pack(side='left')
        
        # Right side - OK/Cancel buttons
        right_buttons = tk.Frame(button_frame, bg=theme.colors['bg_primary'])
        right_buttons.pack(side='right')
        
        cancel_btn = SimpleModernButton(right_buttons, text="Cancel", 
                                      command=self._on_cancel,
                                      style_type='secondary',
                                      tooltip="Cancel without saving changes")
        cancel_btn.pack(side='right', padx=(10, 0))
        
        ok_btn = SimpleModernButton(right_buttons, text="OK", 
                                   command=self._on_ok,
                                   style_type='primary',
                                   tooltip="Save selected files as context")
        ok_btn.pack(side='right')
        
    def _select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(title="Select Codebase Directory", parent=self.dialog)
        if directory:
            self.selected_directory = directory
            self.dir_label.configure(text=directory)
            self._refresh_codebase()
            
    def _refresh_codebase(self):
        """Refresh the codebase file list."""
        if not self.selected_directory:
            messagebox.showwarning("No Directory", "Please select a directory first", parent=self.dialog)
            return
        
        try:
            # Validate directory
            is_valid, error_msg = self.scanner.validate_directory(self.selected_directory)
            if not is_valid:
                messagebox.showerror("Invalid Directory", error_msg, parent=self.dialog)
                return
            
            # Scan files
            files = self.scanner.scan_directory(self.selected_directory)
            self.codebase_files = files
            
            # Update files list display
            relative_paths = self.scanner.get_relative_paths(files, self.selected_directory)
            self.files_list.add_files(relative_paths, files)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error scanning files: {str(e)}", parent=self.dialog)
            
    def _on_file_selection_change(self):
        """Handle file selection changes."""
        # This can be used to update UI based on selection if needed
        pass
        
    def _load_current_context(self):
        """Load and display current context files."""
        if self.current_context:
            # Try to determine directory from first file
            first_file = self.current_context[0]
            directory = os.path.dirname(first_file)
            
            # Find common parent directory
            common_dir = os.path.commonpath(self.current_context) if len(self.current_context) > 1 else directory
            if os.path.isfile(common_dir):
                common_dir = os.path.dirname(common_dir)
                
            self.selected_directory = common_dir
            self.dir_label.configure(text=common_dir)
            
            # Load files and pre-select current context
            self._refresh_codebase()
            
            # Pre-select current context files
            if hasattr(self.files_list, 'select_files'):
                self.files_list.select_files(self.current_context)
                
    def _update_context_display(self):
        """Update the context display text."""
        self.context_display.config(state='normal')
        self.context_display.delete('1.0', tk.END)
        
        if self.current_context:
            context_text = f"{len(self.current_context)} files selected:\\n"
            for file_path in self.current_context[:5]:  # Show first 5 files
                filename = os.path.basename(file_path)
                context_text += f"• {filename}\\n"
            if len(self.current_context) > 5:
                context_text += f"• ... and {len(self.current_context) - 5} more files"
        else:
            context_text = "No context files selected. You can chat without context or select files for analysis."
            
        self.context_display.insert('1.0', context_text)
        self.context_display.config(state='disabled')
        
    def _clear_selection(self):
        """Clear all selected files."""
        if hasattr(self.files_list, 'clear_selection'):
            self.files_list.clear_selection()
            
    def _on_ok(self):
        """Handle OK button click."""
        # Get selected files
        selected_files = self.files_list.get_selected_file_paths() if self.files_list else []
        
        # Check if context changed
        context_changed = set(selected_files) != set(self.current_context)
        
        if context_changed and self.context_change_callback:
            # Ask for confirmation if context changed and there's existing conversation
            if self.current_context or selected_files:
                result = messagebox.askyesno(
                    "Context Changed", 
                    "Changing context will clear the conversation history. Continue?",
                    parent=self.dialog
                )
                if not result:
                    return
                    
            # Update context
            self.new_context = selected_files
            self.context_change_callback(self.new_context)
            
        self.result = 'ok'
        self.dialog.destroy()
        
    def _on_cancel(self):
        """Handle Cancel button click."""
        self.result = 'cancel'
        self.dialog.destroy()
        
    def show(self):
        """Show the dialog and wait for result."""
        self.dialog.wait_window()
        return self.result, self.new_context


def show_context_dialog(parent, current_context: List[str] = None, context_change_callback: Optional[Callable] = None):
    """
    Show the context selection dialog.
    
    Args:
        parent: Parent window
        current_context: Currently selected context files
        context_change_callback: Callback when context changes
        
    Returns:
        tuple: (result, new_context) where result is 'ok', 'cancel', or None
    """
    dialog = ContextDialog(parent, current_context, context_change_callback)
    return dialog.show()