"""
Question History UI Component

A tkinter interface with question history at the top and input at the bottom.
Shows submitted questions with status indicators and provides a simple input area.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Callable, Optional

from theme import theme_manager
from simple_modern_ui import SimpleModernButton, SimpleModernLabel
from models import QuestionStatus


class QuestionHistoryArea:
    """Displays the history of questions with their status."""
    
    def __init__(self, parent):
        """Initialize the question history display area."""
        self.parent = parent
        self.theme = theme_manager.get_current_theme()
        
        # Create main frame
        self.frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        
        # Create scrollable area for questions
        self._create_scrollable_area()
        
        # Store question widgets for updates
        self.question_widgets = []
        
    def _create_scrollable_area(self):
        """Create a scrollable area for the question history."""
        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(self.frame, bg=self.theme.colors['bg_primary'], 
                               highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", 
                                      command=self.canvas.yview)
        
        # Scrollable frame that will contain the questions
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.theme.colors['bg_primary'])
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, 
                                                      anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack components
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel scrolling
        self._bind_mousewheel()
        
        # Configure canvas window width
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
    def _bind_mousewheel(self):
        """Bind mousewheel events for scrolling."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        # Bind to multiple widgets for better coverage
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
    def _on_canvas_configure(self, event):
        """Handle canvas resize to adjust scrollable frame width."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def add_question(self, question_status: QuestionStatus):
        """Add a new question to the history display."""
        # Create widget info entry first
        widget_info = {
            'frame': None,
            'status': question_status,
            'status_label': None,
            'response_text': None,
            'is_expanded': False,
            'original_height': None,
            'question_index': len(self.question_widgets)  # Store index for deletion
        }
        self.question_widgets.append(widget_info)
        
        # Create the actual widget
        question_frame, status_label = self._create_question_widget(question_status)
        widget_info['frame'] = question_frame
        widget_info['status_label'] = status_label
        
        # Scroll to bottom to show new question
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        
    def _create_question_widget(self, question_status: QuestionStatus):
        """Create a widget for displaying a single question."""
        # Main question frame
        question_frame = tk.Frame(self.scrollable_frame, 
                                 bg=self.theme.colors['bg_secondary'],
                                 relief='solid', bd=1)
        question_frame.pack(fill='x', padx=3, pady=1)
        
        # Header with question and status
        header_frame = tk.Frame(question_frame, bg=self.theme.colors['bg_secondary'])
        header_frame.pack(fill='x', padx=5, pady=3)
        
        # Question text (left side) - expanded layout for better left alignment
        question_container = tk.Frame(header_frame, bg=self.theme.colors['bg_secondary'])
        question_container.pack(side='left', fill='both', expand=True)
        
        question_label = tk.Label(question_container, 
                                 text=f"Q: {question_status.question}",
                                 bg=self.theme.colors['bg_secondary'],
                                 fg=self.theme.colors['text_primary'],
                                 font=("Arial", 10, "bold"),
                                 wraplength=500,
                                 justify='left',
                                 anchor='w')
        question_label.pack(side='left', anchor='w', fill='x', expand=True)
        
        # Action icons (middle)
        action_frame = tk.Frame(header_frame, bg=self.theme.colors['bg_secondary'])
        action_frame.pack(side='right', padx=(10, 10))
        
        # Store widget references for later use
        widget_refs = {
            'question_frame': question_frame,
            'question_status': question_status,
            'action_frame': action_frame
        }
        
        self._create_action_icons(action_frame, widget_refs)
        
        # Status and timestamp (right side)
        status_frame = tk.Frame(header_frame, bg=self.theme.colors['bg_secondary'])
        status_frame.pack(side='right')
        
        # Statistics (only show when completed)
        if question_status.status == "completed" and question_status.tokens_used > 0:
            stats_text = f"{question_status.tokens_used} tokens • {question_status.processing_time:.1f}s"
            if question_status.model_used:
                model_short = question_status.model_used.split('/')[-1]  # Get just the model name
                stats_text += f" • {model_short}"
            
            stats_label = tk.Label(status_frame,
                                 text=stats_text,
                                 bg=self.theme.colors['bg_secondary'],
                                 fg=self.theme.colors['text_secondary'],
                                 font=("Arial", 8))
            stats_label.pack(side='right', padx=(10, 0))
        
        # Timestamp
        time_label = tk.Label(status_frame,
                             text=question_status.timestamp,
                             bg=self.theme.colors['bg_secondary'],
                             fg=self.theme.colors['text_secondary'],
                             font=("Arial", 8))
        time_label.pack(side='right', padx=(10, 0))
        
        # Status indicator
        status_text, status_color = self._get_status_display(question_status.status)
        status_label = tk.Label(status_frame,
                               text=status_text,
                               bg=self.theme.colors['bg_secondary'],
                               fg=status_color,
                               font=("Arial", 9, "bold"))
        status_label.pack(side='right')
        
        # Response area (initially hidden)
        if question_status.response:
            self._add_response_to_widget(question_frame, question_status.response)
            
        return question_frame, status_label
        
    def _create_action_icons(self, parent, widget_refs):
        """Create action icons for each question."""
        question_frame = widget_refs['question_frame']
        question_status = widget_refs['question_status']
        question_index = len(self.question_widgets) - 1  # Current question index
        
        # Delete icon
        delete_btn = tk.Button(parent, text="🗑️", 
                              bg=self.theme.colors['bg_secondary'],
                              fg=self.theme.colors['text_primary'],
                              font=("Arial", 12),
                              relief='flat',
                              borderwidth=0,
                              cursor='hand2',
                              command=lambda: self._delete_question(question_index))
        delete_btn.pack(side='left', padx=2)
        self._add_tooltip(delete_btn, "Delete Question")
        
        # Expand/Minimize icon (initially expand)
        expand_btn = tk.Button(parent, text="⬆️", 
                              bg=self.theme.colors['bg_secondary'],
                              fg=self.theme.colors['text_primary'],
                              font=("Arial", 12),
                              relief='flat',
                              borderwidth=0,
                              cursor='hand2',
                              command=lambda: self._toggle_expand_question(question_index))
        expand_btn.pack(side='left', padx=2)
        self._add_tooltip(expand_btn, "Expand Question")
        
        # Extract Code icon (only show when completed and has response)
        if question_status.status == "completed" and question_status.response:
            extract_btn = tk.Button(parent, text="💾", 
                                  bg=self.theme.colors['bg_secondary'],
                                  fg=self.theme.colors['text_primary'],
                                  font=("Arial", 12),
                                  relief='flat',
                                  borderwidth=0,
                                  cursor='hand2',
                                  command=lambda: self._extract_code_fragments(question_index))
            extract_btn.pack(side='left', padx=2)
            self._add_tooltip(extract_btn, "Extract Code")
            
        # Store button references in widget info
        if len(self.question_widgets) > 0:
            self.question_widgets[-1]['expand_btn'] = expand_btn
            self.question_widgets[-1]['extract_btn'] = extract_btn if question_status.status == "completed" and question_status.response else None
        
    def _add_tooltip(self, widget, text):
        """Add tooltip to a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, 
                           background=self.theme.colors['bg_primary'],
                           foreground=self.theme.colors['text_primary'],
                           relief='solid', borderwidth=1,
                           font=("Arial", 8))
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
    def _delete_question(self, question_index):
        """Delete a question from the history."""
        if 0 <= question_index < len(self.question_widgets):
            widget_info = self.question_widgets[question_index]
            
            # Destroy the widget
            widget_info['frame'].destroy()
            
            # Remove from list
            self.question_widgets.pop(question_index)
            
            # Update indices for remaining questions
            for i, remaining_widget in enumerate(self.question_widgets):
                remaining_widget['question_index'] = i
                
            # Update canvas scroll region
            self.canvas.update_idletasks()
            
    def _toggle_expand_question(self, question_index):
        """Toggle expand/minimize state of a question."""
        if 0 <= question_index < len(self.question_widgets):
            widget_info = self.question_widgets[question_index]
            question_frame = widget_info['frame']
            
            if widget_info['is_expanded']:
                # Minimize - restore original height
                if widget_info['original_height']:
                    question_frame.configure(height=widget_info['original_height'])
                    widget_info['is_expanded'] = False
                    if 'expand_btn' in widget_info and widget_info['expand_btn']:
                        widget_info['expand_btn'].configure(text="⬆️")
                        self._add_tooltip(widget_info['expand_btn'], "Expand Question")
            else:
                # Expand - take full height
                # Store original height first
                widget_info['original_height'] = question_frame.winfo_reqheight()
                
                # Get parent height (scroll area)
                parent_height = self.canvas.winfo_height()
                
                # Set to take most of the parent height
                expand_height = max(parent_height - 100, 400)  # Leave some padding
                question_frame.configure(height=expand_height)
                widget_info['is_expanded'] = True
                
                if 'expand_btn' in widget_info and widget_info['expand_btn']:
                    widget_info['expand_btn'].configure(text="⬇️")
                    self._add_tooltip(widget_info['expand_btn'], "Minimize Question")
                    
            # Update canvas scroll region
            self.canvas.update_idletasks()
            
    def _extract_code_fragments(self, question_index):
        """Extract code fragments from the question response."""
        if 0 <= question_index < len(self.question_widgets):
            widget_info = self.question_widgets[question_index]
            question_status = widget_info['status']
            
            if question_status.response:
                try:
                    # Import the code fragment parser
                    from code_fragment_parser import show_code_fragments_dialog
                    
                    # Show the code extraction dialog
                    show_code_fragments_dialog(self.parent, question_status.response)
                    
                except ImportError:
                    print("Code fragment parser not available")
                except Exception as e:
                    print(f"Error extracting code fragments: {e}")
        
    def _get_status_display(self, status: str):
        """Get display text and color for status."""
        theme = theme_manager.get_current_theme()
        status_mapping = {
            'working': ('🔄 Working...', theme.colors['warning']),
            'completed': ('✅ Completed', theme.colors['success']),
            'error': ('❌ Error', theme.colors['danger'])
        }
        return status_mapping.get(status, ('❓ Unknown', theme.colors['text_muted']))
        
    def _add_response_to_widget(self, question_frame, response: str):
        """Add response text to an existing question widget."""
        # Response section
        response_frame = tk.Frame(question_frame, bg=self.theme.colors['bg_primary'])
        response_frame.pack(fill='both', expand=True, padx=5, pady=(0, 5))
        
        # Response label
        response_label = tk.Label(response_frame,
                                 text="Response:",
                                 bg=self.theme.colors['bg_primary'],
                                 fg=self.theme.colors['text_primary'],
                                 font=("Arial", 9, "bold"))
        response_label.pack(anchor='w', pady=(5, 2))
        
        # Response text (scrollable)
        response_text = scrolledtext.ScrolledText(response_frame,
                                                 height=6,
                                                 wrap=tk.WORD,
                                                 bg=self.theme.colors['bg_primary'],
                                                 fg=self.theme.colors['text_primary'],
                                                 font=("Consolas", 9),
                                                 state='disabled')
        response_text.pack(fill='both', expand=True)
        
        # Insert response text
        response_text.config(state='normal')
        response_text.insert('1.0', response)
        response_text.config(state='disabled')
        
        return response_text
        
    def update_question_status(self, question_index: int, status: str, response: str = ""):
        """Update the status of a question and optionally add response."""
        if 0 <= question_index < len(self.question_widgets):
            widget_info = self.question_widgets[question_index]
            question_status = widget_info['status']
            
            # Update the question status object
            question_status.status = status
            if response:
                question_status.response = response
            
            # Update status label
            if widget_info['status_label']:
                status_text, status_color = self._get_status_display(status)
                widget_info['status_label'].config(text=status_text, fg=status_color)
            
            # Add statistics text if completed and we have token info
            if status == "completed" and question_status.tokens_used > 0:
                self._add_statistics_to_header(widget_info, question_status)
            
            # Add extract code button if completed and response provided
            if status == "completed" and response and not widget_info.get('extract_btn'):
                self._add_extract_code_button(widget_info, question_index)
            
            # Add response if provided and not already added
            if response and not widget_info['response_text']:
                response_text = self._add_response_to_widget(widget_info['frame'], response)
                widget_info['response_text'] = response_text
                
                # Update canvas scroll region
                self.canvas.update_idletasks()
                
    def _add_statistics_to_header(self, widget_info, question_status):
        """Add statistics to the existing header."""
        try:
            # Find the status frame in the header and add statistics as tooltip or simple text
            question_frame = widget_info['frame']
            for child in question_frame.winfo_children():
                if isinstance(child, tk.Frame):  # This should be the header frame
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Frame):  # This should be the status frame
                            # Check if we already have a stats label
                            has_stats = False
                            for existing_child in grandchild.winfo_children():
                                if hasattr(existing_child, 'cget') and 'tokens' in str(existing_child.cget('text')):
                                    has_stats = True
                                    break
                            
                            if not has_stats:
                                # Create a simple statistics text
                                stats_text = f"{question_status.tokens_used} tokens • {question_status.processing_time:.1f}s"
                                if question_status.model_used:
                                    model_short = question_status.model_used.split('/')[-1]
                                    stats_text += f" • {model_short}"
                                
                                # Add it as a simple label without complex packing
                                stats_label = tk.Label(grandchild,
                                                     text=stats_text,
                                                     bg=self.theme.colors['bg_secondary'],
                                                     fg=self.theme.colors['text_secondary'],
                                                     font=("Arial", 8))
                                stats_label.pack(side='left', padx=(5, 0))
                            return
        except Exception as e:
            # Just update the status label with stats info instead
            if widget_info['status_label']:
                stats_text = f"✅ Completed ({question_status.tokens_used} tokens, {question_status.processing_time:.1f}s)"
                widget_info['status_label'].config(text=stats_text)
                
    def _add_extract_code_button(self, widget_info, question_index):
        """Add extract code button to completed question."""
        try:
            # Find the action frame to add the button
            question_frame = widget_info['frame']
            for child in question_frame.winfo_children():
                if isinstance(child, tk.Frame):  # Header frame
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Frame):  # Look for action frame
                            # Check if this frame has action buttons (by checking for emoji text)
                            for button in grandchild.winfo_children():
                                if isinstance(button, tk.Button) and "🗑️" in str(button.cget('text')):
                                    # This is the action frame, add extract button
                                    extract_btn = tk.Button(grandchild, text="💾", 
                                                          bg=self.theme.colors['bg_secondary'],
                                                          fg=self.theme.colors['text_primary'],
                                                          font=("Arial", 12),
                                                          relief='flat',
                                                          borderwidth=0,
                                                          cursor='hand2',
                                                          command=lambda: self._extract_code_fragments(question_index))
                                    extract_btn.pack(side='left', padx=2)
                                    self._add_tooltip(extract_btn, "Extract Code")
                                    
                                    # Store reference
                                    widget_info['extract_btn'] = extract_btn
                                    return
        except Exception as e:
            pass  # Silently handle errors in UI updates
                
    def clear_history(self):
        """Clear all questions from the history display."""
        for widget_info in self.question_widgets:
            widget_info['frame'].destroy()
        self.question_widgets.clear()
        
    def pack(self, **kwargs):
        """Pack the main frame."""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the main frame."""
        self.frame.grid(**kwargs)


class QuestionInputArea:
    """Input area for submitting new questions."""
    
    def __init__(self, parent, submit_callback: Optional[Callable] = None):
        """Initialize the question input area."""
        self.parent = parent
        self.theme = theme_manager.get_current_theme()
        self.submit_callback = submit_callback
        self.tool_vars = {}  # Store TOOL environment variables
        
        # Load tool variables
        self._load_tool_variables()
        
        # Create main frame with modern styling
        self.frame = tk.Frame(parent, bg=self.theme.colors['bg_secondary'],
                             relief='raised', bd=1)
        
        # Create input components
        self._create_input_components()
        
    def _load_tool_variables(self):
        """Load TOOL environment variables."""
        try:
            from env_manager import env_manager
            all_vars = env_manager.load_env_file()
            self.tool_vars = {key: value for key, value in all_vars.items() if key.startswith('TOOL')}
        except Exception as e:
            print(f"Error loading TOOL variables: {e}")
            self.tool_vars = {}
        
    def _create_input_components(self):
        """Create the enhanced input area with tool support."""
        # Container with reduced padding
        container = tk.Frame(self.frame, bg=self.theme.colors['bg_secondary'])
        container.pack(fill='both', expand=True, padx=10, pady=8)
        
        
        # Tool commands section (if tools exist)
        if self.tool_vars:
            self._create_tool_section(container)
        
        # Input frame (text + buttons)
        input_frame = tk.Frame(container, bg=self.theme.colors['bg_secondary'])
        input_frame.pack(fill='x', pady=(2, 0))
        
        # Text input with modern chat-like styling
        text_frame = tk.Frame(input_frame, bg=self.theme.colors['bg_secondary'])
        text_frame.pack(side='left', fill='both', expand=True, padx=(0, 8))
        
        # Add rounded appearance with border frame
        border_frame = tk.Frame(text_frame, bg='#D0D0D0', relief='flat')
        border_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        self.text_input = scrolledtext.ScrolledText(border_frame,
                                                   height=4,
                                                   wrap=tk.WORD,
                                                   bg=self.theme.colors['bg_primary'],
                                                   fg=self.theme.colors['text_primary'],
                                                   font=("Segoe UI", 11),
                                                   relief='flat',
                                                   bd=0,
                                                   insertbackground=self.theme.colors['text_primary'])
        self.text_input.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Button frame
        button_frame = tk.Frame(input_frame, bg=self.theme.colors['bg_secondary'])
        button_frame.pack(side='right', fill='y')
        
        # Submit button
        self.submit_btn = SimpleModernButton(button_frame,
                                           text="Submit\nQuestion",
                                           command=self._on_submit,
                                           style_type='primary',
                                           tooltip="Submit your question to the AI (Enter key)")
        self.submit_btn.pack(pady=(0, 5))
        
        # Clear button
        clear_btn = SimpleModernButton(button_frame,
                                     text="Clear",
                                     command=self._clear_input,
                                     style_type='secondary',
                                     tooltip="Clear the input text area")
        clear_btn.pack()
        
        # Bind keys
        self.text_input.bind('<Control-Return>', lambda e: self.text_input.insert(tk.INSERT, '\n'))
        self.text_input.bind('<Return>', self._on_enter_key)
        
    def _create_tool_section(self, container):
        """Create the tool commands section."""
        tools_frame = tk.Frame(container, bg=self.theme.colors['bg_secondary'])
        tools_frame.pack(fill='x', pady=(0, 5))
        
        # Tool label
        tool_label = tk.Label(tools_frame, text="🔧 Tool Commands:",
                             bg=self.theme.colors['bg_secondary'],
                             fg=self.theme.colors['text_primary'],
                             font=('Arial', 9, 'bold'))
        tool_label.pack(side='left', padx=(0, 10))
        
        # Tools dropdown
        self.tool_var = tk.StringVar()
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
        self.tool_combo.pack(side='left', padx=(0, 10))
        self.tool_combo.bind('<<ComboboxSelected>>', self._on_tool_selected)
        
        # Use tool button
        use_tool_btn = SimpleModernButton(tools_frame,
                                         text="Insert Tool",
                                         command=self._insert_tool_command,
                                         style_type='accent',
                                         tooltip="Insert the selected tool command into your question")
        use_tool_btn.pack(side='left', padx=(0, 10))
        
        # Tool preview
        self.tool_preview = tk.Label(tools_frame, text="",
                                    bg=self.theme.colors['bg_secondary'],
                                    fg=self.theme.colors['text_secondary'],
                                    font=('Arial', 8))
        self.tool_preview.pack(side='left', fill='x', expand=True)
        
    def _on_tool_selected(self, event=None):
        """Handle tool selection change."""
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
            
    def _insert_tool_command(self):
        """Insert the selected tool command into the text input."""
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
            cursor_pos = self.text_input.index(tk.INSERT)
            
            # Insert line feed, then command text, then another line feed
            injection_text = f"\n{command_text}\n"
            
            # Insert the text
            self.text_input.insert(cursor_pos, injection_text)
            
            # Move cursor to end of inserted text
            lines_added = injection_text.count('\n')
            if lines_added > 0:
                new_line, new_col = map(int, cursor_pos.split('.'))
                new_line += lines_added
                new_cursor_pos = f"{new_line}.{len(command_text)}"
                self.text_input.mark_set(tk.INSERT, new_cursor_pos)
            
            # Focus back to text input
            self.text_input.focus_set()
            
        except Exception as e:
            print(f"Error inserting tool command: {e}")
            
    def _on_enter_key(self, event):
        """Handle Enter key press."""
        # Submit on Enter (unless Shift+Enter for new line)
        if not event.state & 0x1:  # No Shift key
            self._on_submit()
            return 'break'  # Prevent default behavior
        return None  # Allow default behavior (new line)
        
    def _clear_input(self):
        """Clear the input text."""
        self.text_input.delete('1.0', tk.END)
        
    def refresh_tool_variables(self):
        """Refresh tool variables and update UI."""
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
                self.tool_combo.set(tool_options[0])
                self._on_tool_selected()
            else:
                self.tool_combo.set("No TOOL variables found")
                self.tool_preview.configure(text="")
        
    def _on_submit(self):
        """Handle submit button click."""
        question = self.get_question().strip()
        if question and self.submit_callback:
            self.submit_callback(question)
            self.clear_question()
            
    def get_question(self) -> str:
        """Get the current question text."""
        return self.text_input.get('1.0', 'end-1c')
        
    def clear_question(self):
        """Clear the question input."""
        self.text_input.delete('1.0', tk.END)
        
    def set_enabled(self, enabled: bool):
        """Enable or disable the input area."""
        state = 'normal' if enabled else 'disabled'
        self.text_input.config(state=state)
        self.submit_btn.config(state=state)
        
    def pack(self, **kwargs):
        """Pack the main frame."""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the main frame."""
        self.frame.grid(**kwargs)


class QuestionHistoryUI:
    """Complete question history interface with history display and input."""
    
    def __init__(self, parent, submit_callback: Optional[Callable] = None):
        """Initialize the complete question history UI."""
        self.parent = parent
        self.submit_callback = submit_callback
        
        # Create main container
        self.main_frame = tk.Frame(parent)
        
        # Create components
        self._create_components()
        
    def _create_components(self):
        """Create the history and input components."""
        # Configure grid weights
        self.main_frame.rowconfigure(0, weight=1)  # History area gets most space
        self.main_frame.columnconfigure(0, weight=1)
        
        # Question history area (top, expandable)
        self.history_area = QuestionHistoryArea(self.main_frame)
        self.history_area.grid(row=0, column=0, sticky='nsew', padx=3, pady=(3, 1))
        
        # Question input area (bottom, fixed height)
        self.input_area = QuestionInputArea(self.main_frame, self.submit_callback)
        self.input_area.grid(row=1, column=0, sticky='ew', padx=3, pady=(1, 3))
        
    def add_question(self, question_status: QuestionStatus):
        """Add a new question to the history."""
        self.history_area.add_question(question_status)
        
    def update_question_status(self, question_index: int, status: str, response: str = ""):
        """Update a question's status and response."""
        self.history_area.update_question_status(question_index, status, response)
        
    def clear_history(self):
        """Clear all questions from history."""
        self.history_area.clear_history()
        
    def set_input_enabled(self, enabled: bool):
        """Enable or disable question input."""
        self.input_area.set_enabled(enabled)
        
    def refresh_tool_variables(self):
        """Refresh tool variables in input area."""
        self.input_area.refresh_tool_variables()
        
    def pack(self, **kwargs):
        """Pack the main frame."""
        self.main_frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the main frame."""
        self.main_frame.grid(**kwargs)