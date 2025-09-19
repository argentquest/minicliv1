"""
Simplified modern UI components that are more compatible with different tkinter versions.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Callable, List, Optional, Dict, Any
import json
import os
import time
import threading
from datetime import datetime

from theme import theme_manager
from icons import icon_manager
from code_fragment_parser import CodeFragmentParser, show_code_fragments_dialog

class SimpleModernButton(tk.Button):
    """Simplified modern button with basic styling and tooltip support."""
    
    def __init__(self, parent, text="", command=None, style_type='secondary', 
                 icon_action=None, tooltip=None, **kwargs):
        
        # Add icon if specified
        if icon_action:
            text = icon_manager.format_button_text(text, icon_action)
        
        # Basic styling without problematic options
        theme = theme_manager.get_current_theme()
        
        if style_type == 'primary':
            config = {
                'text': text,
                'command': command,
                'bg': theme.colors['primary'],
                'fg': 'white',
                'relief': 'flat',
                'borderwidth': 0,
                'cursor': 'hand2',
                'font': ('Segoe UI', 9, 'bold'),
                **kwargs
            }
        elif style_type == 'accent':
            config = {
                'text': text,
                'command': command,
                'bg': theme.colors['accent'],
                'fg': 'white',
                'relief': 'flat',
                'borderwidth': 0,
                'cursor': 'hand2',
                'font': ('Segoe UI', 9, 'bold'),
                **kwargs
            }
        else:
            config = {
                'text': text,
                'command': command,
                'bg': theme.colors['bg_tertiary'],
                'fg': theme.colors['text_primary'],
                'relief': 'flat',
                'borderwidth': 1,
                'cursor': 'hand2',
                'font': ('Segoe UI', 9),
                **kwargs
            }
        
        super().__init__(parent, **config)
        
        # Store original colors for hover effects
        self.original_bg = config['bg']
        self.style_type = style_type
        
        # Add hover effects
        self._setup_hover_effects()
        
        # Add tooltip if provided
        if tooltip:
            self._add_tooltip(tooltip)
    
    def _setup_hover_effects(self):
        """Add hover effects to the button."""
        theme = theme_manager.get_current_theme()
        
        if self.style_type == 'primary':
            hover_color = theme.colors['primary_hover']
        elif self.style_type == 'accent':
            hover_color = theme.colors['accent_hover']
        else:
            hover_color = theme.colors['hover']
        
        def on_enter(e):
            self.configure(bg=hover_color)
            
        def on_leave(e):
            self.configure(bg=self.original_bg)
            
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
    
    def _add_tooltip(self, text):
        """Add tooltip to the button."""
        self.tooltip_text = text
        self.tooltip_window = None
        self.tooltip_timer = None
        
        def show_tooltip(event):
            if self.tooltip_window:
                return
                
            x = event.x_root + 15
            y = event.y_root + 10
            
            self.tooltip_window = tk.Toplevel(self)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.configure(bg='#2d2d2d')
            self.tooltip_window.geometry(f"+{x}+{y}")
            
            # Add shadow effect
            self.tooltip_window.attributes('-topmost', True)
            
            label = tk.Label(self.tooltip_window, text=text,
                           bg='#2d2d2d', fg='white',
                           font=('Segoe UI', 9),
                           relief='solid', bd=1,
                           padx=10, pady=5)
            label.pack()
            
        def hide_tooltip():
            if self.tooltip_timer:
                self.after_cancel(self.tooltip_timer)
                self.tooltip_timer = None
            if self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None
        
        def on_enter(event):
            # Start timer for tooltip
            hide_tooltip()  # Cancel any existing
            self.tooltip_timer = self.after(800, lambda: show_tooltip(event))
            
        def on_leave(event):
            hide_tooltip()
        
        # Bind tooltip events without conflicting with hover
        self.bind("<Enter>", on_enter, add='+')
        self.bind("<Leave>", on_leave, add='+')

class SimpleModernLabel(tk.Label):
    """Simplified modern label."""
    
    def __init__(self, parent, text="", style_type='body', **kwargs):
        theme = theme_manager.get_current_theme()
        
        config = {
            'text': text,
            'bg': theme.colors['bg_primary'],
            **kwargs
        }
        
        super().__init__(parent, **config)

class SimpleFilesList(tk.Frame):
    """Simplified enhanced file list."""
    
    def __init__(self, parent, title="Included Files", selection_callback=None):
        super().__init__(parent)
        theme = theme_manager.get_current_theme()
        self.configure(bg=theme.colors['bg_primary'])
        
        self.selection_callback = selection_callback
        self.file_paths = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the file list widgets."""
        theme = theme_manager.get_current_theme()
        
        # Title frame
        title_frame = tk.Frame(self, bg=theme.colors['bg_secondary'], relief='flat', bd=1)
        title_frame.pack(fill='x', padx=5, pady=5)
        
        # Title
        title_label = SimpleModernLabel(title_frame, text="📁 Included Files")
        title_label.pack(side='left', padx=10, pady=10)
        
        # Selection count
        self.selection_label = SimpleModernLabel(title_frame, text="0 selected")
        self.selection_label.pack(side='right', padx=10, pady=10)
        
        # Button frame
        button_frame = tk.Frame(self, bg=theme.colors['bg_secondary'])
        button_frame.pack(fill='x', padx=5, pady=(0, 5))
        
        # Selection buttons
        self.select_all_btn = SimpleModernButton(button_frame, text="Select All", 
                                               command=self.select_all, icon_action='select_all')
        self.select_all_btn.pack(side='left', padx=10, pady=5)
        
        self.select_none_btn = SimpleModernButton(button_frame, text="Select None", 
                                                command=self.select_none, icon_action='select_none')
        self.select_none_btn.pack(side='left', padx=(5, 10), pady=5)
        
        # File list frame
        list_frame = tk.Frame(self, bg=theme.colors['bg_secondary'], relief='flat', bd=1)
        list_frame.pack(fill='both', expand=True, padx=5, pady=(0, 5))
        
        # Create listbox with scrollbar
        self.listbox = tk.Listbox(list_frame, selectmode='extended',
                                 bg=theme.colors['bg_secondary'],
                                 relief='flat', borderwidth=0)
        self.listbox.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y', pady=10, padx=(0, 10))
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # Bind selection events
        self.listbox.bind('<<ListboxSelect>>', self._on_selection_change)
    
    def add_files(self, files: List[str], file_paths: List[str] = None):
        """Add files to the list."""
        self.file_paths = file_paths if file_paths else files
        
        # Clear existing items
        self.listbox.delete(0, tk.END)
        
        # Add files with icons
        for display_name in files:
            filename_with_icon = icon_manager.format_file_text(display_name)
            self.listbox.insert(tk.END, filename_with_icon)
        
        # Select all by default
        self.select_all()
    
    def select_all(self):
        """Select all files."""
        self.listbox.selection_set(0, tk.END)
        self._update_selection_display()
        if self.selection_callback:
            self.selection_callback()
    
    def select_none(self):
        """Deselect all files."""
        self.listbox.selection_clear(0, tk.END)
        self._update_selection_display()
        if self.selection_callback:
            self.selection_callback()
    
    def get_selected_file_paths(self) -> List[str]:
        """Get full paths of selected files."""
        selected_indices = list(self.listbox.curselection())
        return [self.file_paths[i] for i in selected_indices if i < len(self.file_paths)]
    
    def get_selection_count(self) -> int:
        """Get number of selected files."""
        return len(self.listbox.curselection())
    
    def _on_selection_change(self, event):
        """Handle selection changes."""
        self._update_selection_display()
        if self.selection_callback:
            self.selection_callback()
    
    def _update_selection_display(self):
        """Update selection count display."""
        count = self.get_selection_count()
        total = self.listbox.size()
        if total == 0:
            self.selection_label.configure(text="0 selected")
        else:
            self.selection_label.configure(text=f"{count}/{total} selected")

class SimpleChatArea(tk.Frame):
    """Simplified chat area."""
    
    def __init__(self, parent, send_callback=None):
        super().__init__(parent)
        theme = theme_manager.get_current_theme()
        self.configure(bg=theme.colors['bg_primary'])
        self.send_callback = send_callback
        self.tool_vars = {}  # Store TOOL environment variables
        self.current_response = ""  # Store current response text for code fragment parsing
        
        self._load_tool_variables()
        self._create_widgets()
    
    def _load_tool_variables(self):
        """Load TOOL environment variables."""
        try:
            from env_manager import env_manager
            all_vars = env_manager.load_env_file()
            self.tool_vars = {key: value for key, value in all_vars.items() if key.startswith('TOOL')}
        except Exception as e:
            print(f"Error loading TOOL variables: {e}")
            self.tool_vars = {}
    
    def _create_widgets(self):
        """Create the chat widgets with horizontal layout and resizable splitter."""
        theme = theme_manager.get_current_theme()
        
        # Create main horizontal container with PanedWindow for resizable splitter
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, 
                                          bg=theme.colors['bg_primary'],
                                          sashwidth=8, sashrelief='raised',
                                          sashpad=2)
        self.paned_window.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Question section (left side)
        question_frame = tk.Frame(self.paned_window, bg=theme.colors['bg_secondary'], relief='flat', bd=1)
        
        # Question header
        q_header = tk.Frame(question_frame, bg=theme.colors['bg_secondary'])
        q_header.pack(fill='x', padx=10, pady=10)
        
        q_label = SimpleModernLabel(q_header, text="💬 Your Question")
        q_label.pack(side='left')
        
        # Add hint for Enter key functionality
        hint_frame = tk.Frame(q_header, bg=theme.colors['bg_secondary'])
        hint_frame.pack(fill='x', expand=True, padx=(20, 0))
        
        hint_label = tk.Label(hint_frame, text="Press Enter to send • Ctrl+Enter for new line",
                             bg=theme.colors['bg_secondary'], 
                             fg=theme.colors['text_secondary'],
                             font=('Arial', 8), anchor='center')
        hint_label.pack(fill='x')
        
        # TOOL commands section
        if self.tool_vars:
            self._create_tool_section(question_frame, theme)
        
        # Question text area
        self.question_text = scrolledtext.ScrolledText(question_frame, wrap='word',
                                                      bg=theme.colors['bg_secondary'],
                                                      relief='flat', borderwidth=0)
        self.question_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Bind Enter key to send question (Ctrl+Enter for new line)
        self.question_text.bind('<Return>', self._on_enter_key)
        self.question_text.bind('<Control-Return>', self._on_ctrl_enter)
        
        # Enhanced copy/paste bindings for question text
        self._setup_question_bindings()
        
        # Response section (right side)
        response_frame = tk.Frame(self.paned_window, bg=theme.colors['bg_secondary'], relief='flat', bd=1)
        
        # Response header
        r_header = tk.Frame(response_frame, bg=theme.colors['bg_secondary'])
        r_header.pack(fill='x', padx=10, pady=10)
        
        r_label = SimpleModernLabel(r_header, text="🤖 AI Response")
        r_label.pack(side='left')
        
        # Code fragments button (initially hidden)
        self.code_fragments_btn = SimpleModernButton(r_header, text="📋 Code Fragments", 
                                                   command=self._show_code_fragments,
                                                   style_type='secondary')
        self.code_fragments_btn.pack(side='right')
        self.code_fragments_btn.pack_forget()  # Hide initially
        
        # Response text area (using normal state to allow selection, but prevent editing)
        self.response_text = scrolledtext.ScrolledText(response_frame, wrap='word', 
                                                      bg=theme.colors['bg_tertiary'],
                                                      relief='flat', borderwidth=0)
        self.response_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Add both frames to the PanedWindow
        self.paned_window.add(question_frame, minsize=300)  # Minimum width for question side
        self.paned_window.add(response_frame, minsize=300)  # Minimum width for response side
        
        # Bind double-click on splitter to reset to 50/50
        self.paned_window.bind('<Double-Button-1>', lambda e: self.reset_splitter())
        
        # Set initial split ratio (50/50)
        self.paned_window.update_idletasks()
        width = self.paned_window.winfo_reqwidth()
        if width > 0:
            self.paned_window.sash_place(0, width // 2, 0)
        
        # Make text read-only by binding key events
        self._setup_readonly_response()
        
        # Enhanced copy bindings for response text
        self._setup_response_bindings()
    
    def reset_splitter(self):
        """Reset the splitter to 50/50 split."""
        if hasattr(self, 'paned_window'):
            self.paned_window.update_idletasks()
            width = self.paned_window.winfo_width()
            if width > 0:
                self.paned_window.sash_place(0, width // 2, 0)
    
    def set_splitter_ratio(self, ratio: float):
        """Set the splitter to a specific ratio (0.0 to 1.0)."""
        if hasattr(self, 'paned_window') and 0.0 <= ratio <= 1.0:
            self.paned_window.update_idletasks()
            width = self.paned_window.winfo_width()
            if width > 0:
                position = int(width * ratio)
                self.paned_window.sash_place(0, position, 0)
    
    def get_splitter_ratio(self) -> float:
        """Get the current splitter ratio (0.0 to 1.0)."""
        if hasattr(self, 'paned_window'):
            try:
                width = self.paned_window.winfo_width()
                if width > 0:
                    sash_pos = self.paned_window.sash_coord(0)[0]
                    return sash_pos / width
            except:
                pass
        return 0.5  # Default 50/50
    
    def get_question(self) -> str:
        """Get the current question text."""
        return self.question_text.get("1.0", tk.END).strip()
    
    def clear_question(self):
        """Clear the question text area."""
        self.question_text.delete("1.0", tk.END)
    
    def set_response(self, response: str):
        """Set the response text."""
        self.response_text.delete("1.0", tk.END)
        self.response_text.insert("1.0", response)
        
        # Store response text for code fragment parsing
        self.current_response = response
        
        # Show/hide code fragments button based on detection
        if CodeFragmentParser.has_code_fragments(response):
            self.code_fragments_btn.pack(side='right')
        else:
            self.code_fragments_btn.pack_forget()
    
    def clear_response(self):
        """Clear the response text area."""
        self.response_text.delete("1.0", tk.END)
        self.current_response = ""
        self.code_fragments_btn.pack_forget()  # Hide button when clearing
    
    def _on_enter_key(self, event):
        """Handle Enter key in question text area."""
        if self.send_callback:
            # Prevent the default behavior (inserting newline)
            self.send_callback()
            return 'break'
        return None
    
    def _on_ctrl_enter(self, event):
        """Handle Ctrl+Enter for inserting newline."""
        # Allow the default behavior (insert newline)
        return None
    
    def _setup_question_bindings(self):
        """Setup enhanced copy/paste bindings for question text area."""
        # Standard copy/paste bindings
        self.question_text.bind('<Control-c>', self._copy_question)
        self.question_text.bind('<Control-v>', self._paste_question)
        self.question_text.bind('<Control-x>', self._cut_question)
        self.question_text.bind('<Control-a>', self._select_all_question)
    
    def _setup_readonly_response(self):
        """Make response text area read-only while allowing selection."""
        def prevent_edit(event):
            # Allow selection and copy operations, prevent everything else
            if event.keysym in ['c', 'C'] and event.state & 0x4:  # Ctrl+C
                return None
            if event.keysym in ['a', 'A'] and event.state & 0x4:  # Ctrl+A
                return None
            if event.type in ['2', '4']:  # KeyPress or KeyRelease for navigation keys
                if event.keysym in ['Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Page_Up', 'Page_Down']:
                    return None
            if event.type == '4':  # ButtonPress for mouse selection
                return None
            if event.type == '6':  # Motion for mouse drag selection
                return None
            return 'break'  # Prevent all other operations
        
        # Bind to prevent editing while allowing selection
        self.response_text.bind('<Key>', prevent_edit)
        self.response_text.bind('<Button-1>', lambda e: None)  # Allow mouse clicks
        self.response_text.bind('<B1-Motion>', lambda e: None)  # Allow mouse drag selection
        
    def _setup_response_bindings(self):
        """Setup enhanced copy bindings for response text area."""
        # Standard copy functionality
        self.response_text.bind('<Control-c>', self._copy_response)
        self.response_text.bind('<Control-a>', self._select_all_response)
    
    def _copy_question(self, event=None):
        """Copy selected text from question area."""
        try:
            if self.question_text.selection_present():
                selected_text = self.question_text.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
        except tk.TclError:
            pass
        return 'break'
    
    def _paste_question(self, event=None):
        """Paste text to question area."""
        try:
            clipboard_text = self.selection_get(selection="CLIPBOARD")
            if self.question_text.selection_present():
                self.question_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.question_text.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            pass
        return 'break'
    
    def _cut_question(self, event=None):
        """Cut selected text from question area."""
        try:
            if self.question_text.selection_present():
                selected_text = self.question_text.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
                self.question_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return 'break'
    
    def _select_all_question(self, event=None):
        """Select all text in question area."""
        self.question_text.tag_add(tk.SEL, "1.0", tk.END)
        self.question_text.mark_set(tk.INSERT, "1.0")
        self.question_text.see(tk.INSERT)
        return 'break'
    
    def _copy_response(self, event=None):
        """Copy selected text from response area."""
        try:
            if self.response_text.selection_present():
                selected_text = self.response_text.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
        except tk.TclError:
            pass
        return 'break'
    
    def _select_all_response(self, event=None):
        """Select all text in response area."""
        self.response_text.tag_add(tk.SEL, "1.0", tk.END)
        self.response_text.mark_set(tk.INSERT, "1.0")
        self.response_text.see(tk.INSERT)
        return 'break'
    
    def _show_code_fragments(self):
        """Show code fragments dialog for current response."""
        if hasattr(self, 'current_response') and self.current_response:
            show_code_fragments_dialog(self, self.current_response)
    
    def _create_tool_section(self, parent, theme):
        """Create the TOOL commands section with dropdown and inject button."""
        # Tools header frame
        tools_frame = tk.Frame(parent, bg=theme.colors['bg_secondary'])
        tools_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Tools label
        tools_label = SimpleModernLabel(tools_frame, text="🔧 Quick Commands:")
        tools_label.pack(side='left')
        
        # Tools dropdown
        self.tool_var = tk.StringVar()
        # Use actual tool text as display values, keep mapping to variable names
        self.tool_display_to_key = {}  # Map display text to variable key
        if self.tool_vars:
            tool_options = []
            for key, value in self.tool_vars.items():
                # Truncate long values for display but keep full text
                display_text = value[:60] + "..." if len(value) > 60 else value
                tool_options.append(display_text)
                self.tool_display_to_key[display_text] = key
        else:
            tool_options = ["No TOOL variables found"]
            
        self.tool_combo = ttk.Combobox(tools_frame, textvariable=self.tool_var,
                                      values=tool_options, state="readonly", width=50)
        self.tool_combo.pack(side='left', padx=(10, 10))
        
        if tool_options and tool_options[0] != "No TOOL variables found":
            self.tool_var.set(tool_options[0])  # Set first tool as default
        
        # Inject button
        self.inject_btn = SimpleModernButton(tools_frame, text="Inject", 
                                           command=self._inject_tool_command,
                                           icon_action='paste')
        self.inject_btn.pack(side='left')
        
        # Preview of selected tool command
        self.tool_preview = tk.Label(tools_frame, text="",
                                   bg=theme.colors['bg_secondary'],
                                   fg=theme.colors['text_secondary'],
                                   font=('Arial', 8), wraplength=300)
        self.tool_preview.pack(side='left', padx=(20, 0))
        
        # Bind combobox change to update preview
        self.tool_combo.bind('<<ComboboxSelected>>', self._on_tool_selection_change)
        
        # Update initial preview
        self._on_tool_selection_change()
    
    def _on_tool_selection_change(self, event=None):
        """Update the tool command preview when selection changes."""
        selected_display = self.tool_var.get()
        if selected_display and selected_display != "No TOOL variables found":
            # Get the actual variable key from the display text
            if hasattr(self, 'tool_display_to_key') and selected_display in self.tool_display_to_key:
                selected_tool = self.tool_display_to_key[selected_display]
                command_text = self.tool_vars[selected_tool]
            elif selected_display in self.tool_vars:
                # Fallback for backwards compatibility
                command_text = self.tool_vars[selected_display]
            else:
                self.tool_preview.configure(text="")
                return
                
            # Show preview (truncated if too long)
            if len(command_text) > 50:
                preview = command_text[:50] + "..."
            else:
                preview = command_text
            self.tool_preview.configure(text=f'"{preview}"')
        else:
            self.tool_preview.configure(text="")
    
    def _inject_tool_command(self):
        """Inject the selected tool command at the current cursor position."""
        selected_display = self.tool_var.get()
        if not selected_display or selected_display == "No TOOL variables found":
            return
        
        # Get the actual variable key from the display text
        if hasattr(self, 'tool_display_to_key') and selected_display in self.tool_display_to_key:
            selected_tool = self.tool_display_to_key[selected_display]
            command_text = self.tool_vars[selected_tool]
        else:
            # Fallback for backwards compatibility
            if selected_display in self.tool_vars:
                command_text = self.tool_vars[selected_display]
            else:
                return
        
        try:
            # Get current cursor position
            cursor_pos = self.question_text.index(tk.INSERT)
            
            # Insert line feed, then command text, then another line feed
            injection_text = f"\n{command_text}\n"
            
            # Insert at cursor position
            self.question_text.insert(cursor_pos, injection_text)
            
            # Move cursor to end of injected text
            lines_added = injection_text.count('\n')
            new_cursor_line = int(cursor_pos.split('.')[0]) + lines_added
            self.question_text.mark_set(tk.INSERT, f"{new_cursor_line}.0")
            
            # Focus back to text area
            self.question_text.focus()
            
        except Exception as e:
            print(f"Error injecting tool command: {e}")
    
    def refresh_tool_variables(self):
        """Refresh TOOL variables from environment (call when settings change)."""
        self._load_tool_variables()
        
        # Update dropdown if it exists
        if hasattr(self, 'tool_combo'):
            # Rebuild display options and mapping
            self.tool_display_to_key = {}
            if self.tool_vars:
                tool_options = []
                for key, value in self.tool_vars.items():
                    # Truncate long values for display but keep full text
                    display_text = value[:60] + "..." if len(value) > 60 else value
                    tool_options.append(display_text)
                    self.tool_display_to_key[display_text] = key
            else:
                tool_options = ["No TOOL variables found"]
                
            self.tool_combo['values'] = tool_options
            
            if tool_options and tool_options[0] != "No TOOL variables found":
                self.tool_var.set(tool_options[0])
            else:
                self.tool_var.set("")
            
            self._on_tool_selection_change()

class SimpleStatusBar(tk.Frame):
    """Simplified status bar."""
    
    def __init__(self, parent):
        super().__init__(parent)
        theme = theme_manager.get_current_theme()
        self.configure(bg=theme.colors['bg_secondary'], relief='flat', bd=1)
        
        # Status text
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self, textvariable=self.status_var, 
                                   anchor='w', bg=theme.colors['bg_secondary'])
        self.status_label.pack(side='left', fill='x', expand=True, padx=10, pady=5)
    
    def set_status(self, message: str, status_type: str = 'info'):
        """Set status message with icon."""
        formatted_message = icon_manager.format_status_text(message, status_type)
        self.status_var.set(formatted_message)

def show_simple_toast(parent, message: str, toast_type: str = 'info'):
    """Simple toast using messagebox."""
    if toast_type == 'error':
        messagebox.showerror("Error", message, parent=parent)
    elif toast_type == 'warning':
        messagebox.showwarning("Warning", message, parent=parent)
    else:
        messagebox.showinfo("Info", message, parent=parent)