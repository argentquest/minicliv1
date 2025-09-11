"""
Simplified modern version of the Code Chat application with better compatibility.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from dotenv import load_dotenv

from models import AppState, AppConfig, ConversationMessage
from file_scanner import CodebaseScanner
from ai import AIProcessor
from theme import theme_manager
from icons import icon_manager
from simple_modern_ui import (
    SimpleModernButton, SimpleModernLabel, SimpleFilesList, 
    SimpleChatArea, SimpleStatusBar, show_simple_toast
)
from tabbed_chat_area import TabbedChatArea
from env_settings_dialog import EnvSettingsDialog
from env_manager import env_manager
from system_message_dialog import SystemMessageDialog
from system_message_manager import system_message_manager

class SimpleModernCodeChatApp:
    """Simplified modern version of the Code Chat application."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = AppConfig.get_default()
        self.state = AppState()
        self.scanner = CodebaseScanner()
        
        # Load environment and initialize components
        self._load_environment()
        
        # Reload theme preference after dotenv loads .env file
        theme_manager._load_theme_preference()
        
        self._setup_window()
        self._create_ui()
        
        # Initialize AI processor with provider from environment
        ai_provider = os.getenv("PROVIDER", "openrouter")
        self.ai_processor = AIProcessor(self.state.api_key, ai_provider)
        
        # Set initial status
        self._update_initial_status()
    
    def _load_environment(self):
        """Load environment variables."""
        load_dotenv()
        self.state.api_key = os.getenv("API_KEY", "")
        
        # Load models from environment
        models_env = os.getenv("MODELS")
        if models_env:
            self.models = [m.strip() for m in models_env.split(",") if m.strip()]
        else:
            self.models = [
                "openai/gpt-3.5-turbo",
                "openai/gpt-4",
                "openai/gpt-4-turbo",
                "anthropic/claude-3-haiku",
                "anthropic/claude-3-sonnet"
            ]
        
        # Set default model
        self.state.selected_model = os.getenv("DEFAULT_MODEL", self.models[0])
    
    def _setup_window(self):
        """Configure the main window."""
        self.root.title("🤖 Code Chat with AI - Modern Edition")
        self.root.geometry("1200x900")
        self.root.minsize(900, 700)
        
        # Apply theme to root
        theme = theme_manager.get_current_theme()
        self.root.configure(bg=theme.colors['bg_primary'])
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def _create_ui(self):
        """Create the simplified modern UI."""
        theme = theme_manager.get_current_theme()
        
        # Main container
        self.main_container = tk.Frame(self.root, bg=theme.colors['bg_primary'])
        self.main_container.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        
        # Configure grid weights
        self.main_container.columnconfigure(1, weight=1)  # Chat area takes remaining space
        # Column 0 (left panel) has no weight = fixed size
        self.main_container.rowconfigure(1, weight=1)     # Main content area (moved up)
        
        # Create sections
        self._create_header_with_actions()  # Combined header with actions
        self._create_main_content_with_directory()  # Combined content with directory
        self._create_status_bar()
    
    def _create_header_with_actions(self):
        """Create the header with title, selections, and action buttons."""
        theme = theme_manager.get_current_theme()
        
        header_frame = tk.Frame(self.main_container, bg=theme.colors['bg_secondary'], 
                               relief='flat', bd=1)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        # Top row: Title and selections
        top_row = tk.Frame(header_frame, bg=theme.colors['bg_secondary'])
        top_row.pack(fill='x', padx=15, pady=(12, 6))
        
        # Title
        title_label = SimpleModernLabel(top_row, text="🤖 Code Chat with AI")
        title_label.pack(side='left')
        
        # Model and System Message selection
        selection_frame = tk.Frame(top_row, bg=theme.colors['bg_secondary'])
        selection_frame.pack(side='right')
        
        # Model selection
        model_frame = tk.Frame(selection_frame, bg=theme.colors['bg_secondary'])
        model_frame.pack(side='left', padx=(0, 20))
        
        SimpleModernLabel(model_frame, text="🧠 Model:").pack(side='left', padx=(0, 8))
        
        self.model_var = tk.StringVar(value=self.state.selected_model)
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                       values=self.models, state="readonly", width=25)
        self.model_combo.pack(side='left')
        self.model_combo.bind('<<ComboboxSelected>>', self._on_model_change)
        
        # System Message selection
        sysmsg_frame = tk.Frame(selection_frame, bg=theme.colors['bg_secondary'])
        sysmsg_frame.pack(side='left')
        
        SimpleModernLabel(sysmsg_frame, text="🤖 System:").pack(side='left', padx=(0, 8))
        
        self.system_message_var = tk.StringVar()
        self.system_message_combo = ttk.Combobox(sysmsg_frame, textvariable=self.system_message_var, 
                                               state="readonly", width=15)
        self.system_message_combo.pack(side='left')
        self.system_message_combo.bind('<<ComboboxSelected>>', self._on_system_message_change)
        
        # Ensure the combobox is focusable and accessible
        self.system_message_combo.configure(takefocus=True)
        
        # Bottom row: Action buttons
        actions_row = tk.Frame(header_frame, bg=theme.colors['bg_secondary'])
        actions_row.pack(fill='x', padx=15, pady=(6, 12))
        
        # Primary actions (left side)
        primary_actions = tk.Frame(actions_row, bg=theme.colors['bg_secondary'])
        primary_actions.pack(side='left')
        
        self.send_btn = SimpleModernButton(primary_actions, text="Send Question", 
                                         command=self._send_question,
                                         style_type='primary', icon_action='send')
        self.send_btn.pack(side='left', padx=(0, 10))
        
        self.execute_system_btn = SimpleModernButton(primary_actions, text="Execute System Prompt", 
                                                   command=self._execute_system_prompt,
                                                   style_type='accent', icon_action='play')
        self.execute_system_btn.pack(side='left', padx=(0, 10))
        
        self.clear_btn = SimpleModernButton(primary_actions, text="Clear Response", 
                                          command=self._clear_response, icon_action='clear')
        self.clear_btn.pack(side='left', padx=(0, 10))
        
        self.new_btn = SimpleModernButton(primary_actions, text="New Conversation", 
                                        command=self._new_conversation, icon_action='new')
        self.new_btn.pack(side='left')
        
        # Secondary actions (right side)
        secondary_actions = tk.Frame(actions_row, bg=theme.colors['bg_secondary'])
        secondary_actions.pack(side='right')
        
        self.save_btn = SimpleModernButton(secondary_actions, text="Save History", 
                                         command=self._save_history, icon_action='save')
        self.save_btn.pack(side='left', padx=(0, 10))
        
        self.load_btn = SimpleModernButton(secondary_actions, text="Load History", 
                                         command=self._load_history, icon_action='load')
        self.load_btn.pack(side='left', padx=(0, 10))
        
        self.settings_btn = SimpleModernButton(secondary_actions, text="Settings", 
                                             command=self._open_settings, icon_action='settings')
        self.settings_btn.pack(side='left', padx=(0, 10))
        
        # Theme toggle button
        current_theme = theme_manager.current_theme_name
        theme_icon = 'sun' if current_theme == 'dark' else 'moon'
        theme_text = '☀️ Light' if current_theme == 'dark' else '🌙 Dark'
        self.theme_btn = SimpleModernButton(secondary_actions, text=theme_text, 
                                          command=self._toggle_theme, icon_action=theme_icon)
        self.theme_btn.pack(side='left', padx=(0, 10))
        
        self.system_msg_btn = SimpleModernButton(secondary_actions, text="System Message", 
                                                command=self._open_system_message_editor,
                                                icon_action='ai')
        self.system_msg_btn.pack(side='left', padx=(0, 10))
        
        self.about_btn = SimpleModernButton(secondary_actions, text="About", 
                                           command=self._open_about,
                                           icon_action='info')
        self.about_btn.pack(side='left')
        
        # Load system message options
        self._refresh_system_message_options()
    
    def _create_main_content_with_directory(self):
        """Create the main content area with directory section at top of left side."""
        theme = theme_manager.get_current_theme()
        
        # Left side container - fixed 300px width
        left_container = tk.Frame(self.main_container, bg=theme.colors['bg_primary'], width=300)
        left_container.grid(row=1, column=0, sticky='nsew', padx=(0, 10))
        left_container.grid_propagate(False)  # Prevent container from shrinking to fit contents
        left_container.rowconfigure(1, weight=1)  # File list gets most space
        left_container.columnconfigure(0, weight=1)  # Full width
        
        # Directory section at top of left side
        dir_frame = tk.Frame(left_container, bg=theme.colors['bg_secondary'],
                            relief='flat', bd=1)
        dir_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        # Directory container
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
        
        self.browse_btn = SimpleModernButton(button_frame, text="Browse", 
                                           command=self._select_directory, 
                                           style_type='primary', icon_action='folder')
        self.browse_btn.pack(side='left', padx=(0, 10))
        
        self.refresh_btn = SimpleModernButton(button_frame, text="Refresh", 
                                            command=self._refresh_codebase,
                                            icon_action='refresh')
        self.refresh_btn.pack(side='left')
        
        # File list below directory section
        self.files_list = SimpleFilesList(left_container, 
                                         selection_callback=self._on_file_selection_change)
        self.files_list.grid(row=1, column=0, sticky='nsew')
        
        # Chat area (right side) - now with tabs
        self.chat_area = TabbedChatArea(self.main_container, self.state.conversation_history, 
                                       parent_window=self, send_callback=self._send_question)
        self.chat_area.grid(row=1, column=1, sticky='nsew')
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = SimpleStatusBar(self.main_container)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(15, 0))
    
    def _on_model_change(self, event):
        """Handle model selection change."""
        self.state.selected_model = self.model_var.get()
        model_name = self.state.selected_model.split('/')[-1]
        self.status_bar.set_status(f"Switched to {model_name} model", "info")
    
    def _select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(title="Select Codebase Directory")
        if directory:
            self.state.selected_directory = directory
            self.dir_label.configure(text=directory)
            self._refresh_codebase()
    
    def _refresh_codebase(self):
        """Refresh the codebase file list."""
        if not self.state.selected_directory:
            show_simple_toast(self.root, "Please select a directory first", "warning")
            return
        
        self.status_bar.set_status("Scanning files...", "info")
        
        try:
            # Validate directory
            is_valid, error_msg = self.scanner.validate_directory(self.state.selected_directory)
            if not is_valid:
                self.status_bar.set_status(error_msg, "error")
                show_simple_toast(self.root, error_msg, "error")
                return
            
            # Scan for files
            files = self.scanner.scan_directory(self.state.selected_directory)
            self.state.codebase_files = files
            
            # Update files list display
            relative_paths = self.scanner.get_relative_paths(files, self.state.selected_directory)
            self.files_list.add_files(relative_paths, files)
            
            self._on_file_selection_change()  # Update status
            
        except Exception as e:
            error_msg = f"Error scanning files: {str(e)}"
            self.status_bar.set_status(error_msg, "error")
            show_simple_toast(self.root, error_msg, "error")
    
    def _on_file_selection_change(self):
        """Handle file selection changes."""
        selected_count = self.files_list.get_selection_count()
        total_count = len(self.state.codebase_files)
        persistent_count = len(self.state.get_persistent_files())
        
        if total_count > 0:
            status_msg = f"Ready - {selected_count}/{total_count} files selected"
            if persistent_count > 0 and len(self.state.conversation_history) > 0:
                status_msg += f" (using {persistent_count} persistent files from first turn)"
            self.status_bar.set_status(status_msg, "ready")
        else:
            self.status_bar.set_status("Ready to analyze your code! 🚀", "ready")
    
    def _send_question(self):
        """Send question to AI."""
        question = self.chat_area.get_question()
        if not question:
            show_simple_toast(self.root, "Please enter a question", "warning")
            return
        
        if not self.ai_processor.validate_api_key():
            show_simple_toast(self.root, "Please configure your API key in Settings", "warning")
            return
        
        # Check if any files are selected or if we have persistent files from previous turn
        selected_files = self.files_list.get_selected_file_paths()
        persistent_files = self.state.get_persistent_files()
        is_first_message = len(self.state.conversation_history) == 0
        
        if is_first_message and not selected_files:
            show_simple_toast(self.root, "Please select files for analysis", "warning")
            return
        elif not is_first_message and not selected_files and not persistent_files:
            show_simple_toast(self.root, "No files available for analysis. Please select files or start a new conversation.", "warning")
            return
        
        self.status_bar.set_status("Processing your question...", "info")
        self.send_btn.configure(state='disabled')
        
        # Run in separate thread
        threading.Thread(target=self._process_question_async, args=(question,), daemon=True).start()
    
    def _execute_system_prompt(self):
        """Execute the system prompt directly without a user question."""
        if not self.ai_processor.validate_api_key():
            show_simple_toast(self.root, "Please configure your API key in Settings", "warning")
            return
        
        # Check if any files are selected or if we have persistent files from previous turn
        selected_files = self.files_list.get_selected_file_paths()
        persistent_files = self.state.get_persistent_files()
        is_first_message = len(self.state.conversation_history) == 0
        
        if is_first_message and not selected_files:
            show_simple_toast(self.root, "Please select files for analysis", "warning")
            return
        elif not is_first_message and not selected_files and not persistent_files:
            show_simple_toast(self.root, "No files available for analysis. Please select files or start a new conversation.", "warning")
            return
        
        self.status_bar.set_status("Executing system prompt...", "info")
        self.send_btn.configure(state='disabled')
        self.execute_system_btn.configure(state='disabled')
        
        # Run in separate thread - pass empty string as question to indicate system prompt execution
        threading.Thread(target=self._process_system_prompt_async, daemon=True).start()
    
    def _process_system_prompt_async(self):
        """Process system prompt execution asynchronously."""
        try:
            # Get files to analyze
            is_first_message = len(self.state.conversation_history) == 0
            
            if is_first_message:
                # First message: use currently selected files and save them for future use
                selected_files = self.files_list.get_selected_file_paths()
                if selected_files:
                    self.state.set_persistent_files(selected_files)
                    codebase_content = self.scanner.get_codebase_content(selected_files)
                else:
                    codebase_content = ""
            else:
                # Use persistent files if available
                persistent_files = self.state.get_persistent_files()
                if persistent_files:
                    codebase_content = self.scanner.get_codebase_content(persistent_files)
                else:
                    # Fallback to currently selected files
                    selected_files = self.files_list.get_selected_file_paths()
                    if selected_files:
                        codebase_content = self.scanner.get_codebase_content(selected_files)
                    else:
                        codebase_content = ""
            
            # Get the system message content directly
            system_message = system_message_manager.get_system_message(codebase_content)
            
            # Process system message as if it were a user question
            ai_response = self.ai_processor.process_question(
                question=system_message,
                conversation_history=[],  # No conversation history for system prompt execution
                codebase_content="",      # Already included in system message
                model=self.state.selected_model,
                update_callback=lambda response, status: self.root.after(0, self.status_bar.set_status, status, "success")
            )
            
            # Add system prompt execution to conversation history
            self.state.conversation_history.append(ConversationMessage(role="user", content="[System Prompt Executed]"))
            self.state.conversation_history.append(ConversationMessage(role="assistant", content=ai_response))
            
            # Update conversation history in tabbed chat area
            self.root.after(0, self._update_conversation_in_tabs)
            
            # Update UI on main thread
            self.root.after(0, self._update_response_ui, ai_response, True)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self._update_response_ui, f"Error executing system prompt: {error_msg}", False)
    
    def _process_question_async(self, question):
        """Process question asynchronously."""
        try:
            # Determine if this is the first message
            is_first_message = len(self.state.conversation_history) == 0
            
            # Check if this question needs codebase context (tool commands or first message)
            needs_codebase_context = is_first_message or self._is_tool_command(question)
            
            # Add user message to conversation history
            self.state.conversation_history.append(ConversationMessage(role="user", content=question))
            
            # Get codebase content when needed
            if needs_codebase_context:
                if is_first_message:
                    # First message: use currently selected files and save them for future use
                    selected_files = self.files_list.get_selected_file_paths()
                    if selected_files:
                        self.state.set_persistent_files(selected_files)
                        codebase_content = self.scanner.get_codebase_content(selected_files)
                    else:
                        codebase_content = ""
                else:
                    # Subsequent messages with tool commands: use persistent files if available
                    persistent_files = self.state.get_persistent_files()
                    if persistent_files:
                        codebase_content = self.scanner.get_codebase_content(persistent_files)
                    else:
                        # Fallback to currently selected files if no persistent files
                        selected_files = self.files_list.get_selected_file_paths()
                        if selected_files:
                            codebase_content = self.scanner.get_codebase_content(selected_files)
                        else:
                            codebase_content = ""
            else:
                codebase_content = ""  # Not needed for regular follow-up messages
            
            # Process with AI
            ai_response = self.ai_processor.process_question(
                question=question,
                conversation_history=[msg.to_dict() for msg in self.state.conversation_history[:-1]],
                codebase_content=codebase_content,
                model=self.state.selected_model,
                update_callback=lambda response, status: self.root.after(0, self.status_bar.set_status, status, "success")
            )
            
            # Add AI response to conversation history
            self.state.conversation_history.append(ConversationMessage(role="assistant", content=ai_response))
            
            # If this was the first message, we need to add the system message to our history
            # so it's included in future conversations
            if is_first_message:
                system_msg_content = system_message_manager.get_system_message(codebase_content)
                system_message = ConversationMessage(role="system", content=system_msg_content)
                # Insert at the beginning of conversation history
                self.state.conversation_history.insert(0, system_message)
            
            # Update conversation history in tabbed chat area
            self.root.after(0, self._update_conversation_in_tabs)
            
            # Update UI on main thread
            self.root.after(0, self._update_response_ui, ai_response, True)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self._update_response_ui, f"Error: {error_msg}", False)
    
    def _update_conversation_in_tabs(self):
        """Update conversation history in the tabbed chat area."""
        self.chat_area.update_conversation_history(self.state.conversation_history)
    
    def _on_conversation_cleared(self):
        """Handle conversation cleared event from history tab."""
        # This is called when the user clears the conversation from the history tab
        self.state.clear_conversation()
        self.status_bar.set_status("Conversation cleared from history tab", "info")
        # Update file selection status to remove persistent files indicator
        self._on_file_selection_change()
    
    def _update_response_ui(self, response: str, success: bool):
        """Update response UI on main thread."""
        self.send_btn.configure(state='normal')
        self.execute_system_btn.configure(state='normal')
        
        if success:
            self.chat_area.set_response(response)
            # Don't override status here - token info is set by the AI processor callback
        else:
            self.chat_area.set_response(response)
            self.status_bar.set_status("Error processing request", "error")
    
    def _clear_response(self):
        """Clear the response area."""
        self.chat_area.clear_response()
        self.status_bar.set_status("Response cleared", "info")
    
    def _new_conversation(self):
        """Start a new conversation."""
        self.state.clear_conversation()
        self.chat_area.clear_response()
        self.chat_area.clear_question()
        self._update_conversation_in_tabs()  # Update history tab
        self.status_bar.set_status("New conversation started! 🆕", "info")
    
    def _save_history(self):
        """Save conversation history."""
        if not self.state.conversation_history:
            show_simple_toast(self.root, "No conversation history to save", "warning")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Conversation History"
        )
        
        if filename:
            try:
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.state.get_conversation_dict(), f, indent=2, ensure_ascii=False)
                self.status_bar.set_status("History saved successfully!", "success")
            except Exception as e:
                error_msg = f"Error saving history: {str(e)}"
                self.status_bar.set_status(error_msg, "error")
                show_simple_toast(self.root, error_msg, "error")
    
    def _load_history(self):
        """Load conversation history."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Conversation History"
        )
        
        if filename:
            try:
                import json
                with open(filename, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                # Convert dict format back to ConversationMessage objects
                self.state.conversation_history = [
                    ConversationMessage(role=msg["role"], content=msg["content"])
                    for msg in history
                ]
                
                # Update conversation history in tabs
                self._update_conversation_in_tabs()
                
                self.status_bar.set_status("History loaded successfully!", "success")
            except Exception as e:
                error_msg = f"Error loading history: {str(e)}"
                self.status_bar.set_status(error_msg, "error")
                show_simple_toast(self.root, error_msg, "error")
    
    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        try:
            # Toggle the theme
            old_theme = theme_manager.current_theme_name
            theme_manager.toggle_theme()
            new_theme = theme_manager.current_theme_name
            
            # Update the theme button text and icon
            theme_icon = 'sun' if new_theme == 'dark' else 'moon'
            theme_text = '☀️ Light' if new_theme == 'dark' else '🌙 Dark'
            self.theme_btn.configure(text=theme_text)
            
            # Save the theme preference to environment
            from env_manager import env_manager
            env_manager.update_single_var('UI_THEME', new_theme)
            
            # Show status message
            self.status_bar.set_status(f"Switched to {new_theme} theme - Restart for full effect", "info")
            show_simple_toast(self.root, f"Theme changed to {new_theme}.\nRestart the application for full effect.", "info")
            
        except Exception as e:
            error_msg = f"Error changing theme: {str(e)}"
            self.status_bar.set_status(error_msg, "error")
            show_simple_toast(self.root, error_msg, "error")
    
    def _open_settings(self):
        """Open enhanced environment settings dialog."""
        EnvSettingsDialog(self.root, self._on_settings_saved)
    
    def _on_settings_saved(self, env_vars):
        """Handle settings saved callback."""
        # Update API key if changed
        if 'API_KEY' in env_vars:
            self.state.api_key = env_vars['API_KEY']
            self.ai_processor.set_api_key(self.state.api_key)
        
        # Update models if changed
        if 'MODELS' in env_vars:
            self.models = [m.strip() for m in env_vars['MODELS'].split(',') if m.strip()]
            # Update combobox values
            self.model_combo['values'] = self.models
            
            # Update selected model if it's no longer available
            if self.state.selected_model not in self.models and self.models:
                self.state.selected_model = self.models[0]
                self.model_var.set(self.state.selected_model)
        
        # Update default model if changed
        if 'DEFAULT_MODEL' in env_vars and env_vars['DEFAULT_MODEL'] in self.models:
            self.state.selected_model = env_vars['DEFAULT_MODEL']
            self.model_var.set(self.state.selected_model)
        
        # Refresh codebase scanner in case ignore folders changed
        if 'IGNORE_FOLDERS' in env_vars:
            self.scanner = CodebaseScanner()  # Reinitialize to pick up new ignore folders
            
            # Refresh current directory if one is selected
            if self.state.selected_directory:
                self._refresh_codebase()
        
        # Refresh TOOL variables in chat area if any TOOL variables changed
        tool_vars_changed = any(key.startswith('TOOL') for key in env_vars.keys())
        if tool_vars_changed:
            self.chat_area.refresh_tool_variables()
        
        self.status_bar.set_status("Settings applied successfully! ✅", "success")
    
    def _open_system_message_editor(self):
        """Open system message editor dialog."""
        SystemMessageDialog(self.root)
    
    def _is_tool_command(self, question: str) -> bool:
        """Check if the question contains a tool command that needs codebase context."""
        # Load tool variables to check against
        try:
            from env_manager import env_manager
            all_vars = env_manager.load_env_file()
            tool_vars = {key: value for key, value in all_vars.items() if key.startswith('TOOL')}
            
            # Check if the question contains any tool command text
            for tool_text in tool_vars.values():
                if tool_text.strip() in question:
                    return True
            
            # Also check for common patterns that suggest code analysis is needed
            code_analysis_patterns = [
                "fix and debug",
                "explain this code",
                "analyze this code",
                "review this code", 
                "refactor this code",
                "optimize this code",
                "test this code",
                "document this code",
                "following code"
            ]
            
            question_lower = question.lower()
            for pattern in code_analysis_patterns:
                if pattern in question_lower:
                    return True
                    
            return False
            
        except Exception:
            # If we can't load tool vars, default to False
            return False
    
    def _open_about(self):
        """Open about dialog."""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Code Chat with AI")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        
        # Center the window
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Apply theme
        theme = theme_manager.get_current_theme()
        about_window.configure(bg=theme.colors['bg_primary'])
        
        # About content frame
        about_frame = tk.Frame(about_window, bg=theme.colors['bg_primary'])
        about_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(about_frame, text="🤖 Code Chat with AI", 
                              font=("Arial", 20, "bold"), 
                              bg=theme.colors['bg_primary'], 
                              fg=theme.colors['text_primary'])
        title_label.pack(pady=(0, 5))
        
        # Subtitle
        subtitle_label = tk.Label(about_frame, text="Modern Edition", 
                                 font=("Arial", 12, "italic"), 
                                 bg=theme.colors['bg_primary'], 
                                 fg=theme.colors['text_secondary'])
        subtitle_label.pack(pady=(0, 20))
        
        # Version
        version_label = tk.Label(about_frame, text="Version 2.0", 
                                font=("Arial", 11), 
                                bg=theme.colors['bg_primary'], 
                                fg=theme.colors['text_primary'])
        version_label.pack(pady=(0, 15))
        
        # Description
        description = """A modern desktop application that allows you to chat with AI models about your codebase. Select files from your project and ask questions to get insights, explanations, and assistance with your code."""
        
        desc_label = tk.Label(about_frame, text=description, wraplength=450, 
                             justify=tk.CENTER, font=("Arial", 10),
                             bg=theme.colors['bg_primary'], 
                             fg=theme.colors['text_primary'])
        desc_label.pack(pady=(0, 20))
        
        # Features
        features_text = """✨ Features:
• Support for multiple AI models (OpenAI GPT, Anthropic Claude)
• Modern tabbed interface with conversation history
• Advanced codebase scanning and file selection
• Customizable system messages for different analysis types
• Conversation history management (save/load)
• Secure API key configuration
• Theme support and modern UI components"""
        
        features_label = tk.Label(about_frame, text=features_text, 
                                 wraplength=450, justify=tk.LEFT, font=("Arial", 10),
                                 bg=theme.colors['bg_primary'], 
                                 fg=theme.colors['text_primary'])
        features_label.pack(pady=(0, 20))
        
        # Close button
        close_btn = SimpleModernButton(about_frame, text="Close", 
                                      command=about_window.destroy,
                                      style_type='primary')
        close_btn.pack()
    
    def _update_initial_status(self):
        """Update initial status with system message info."""
        if system_message_manager.has_custom_system_message():
            current_file = system_message_manager.get_current_system_message_file()
            display_name = system_message_manager.get_display_name_for_file(current_file)
            self.status_bar.set_status(f"Ready to analyze your code! 🚀 (Using {display_name} system message)", "ready")
        else:
            self.status_bar.set_status("Ready to analyze your code! 🚀", "ready")
    
    def _refresh_system_message_options(self):
        """Refresh the system message dropdown options."""
        try:
            # Get all system message files
            files_info = system_message_manager.get_system_message_files_info()
            
            # Create options list
            options = []
            current_selection = "Default"
            
            # Add options from files (this includes "Default" for systemmessage.txt)
            for file_info in files_info:
                display_name = file_info['display_name']
                if display_name not in options:  # Avoid duplicates
                    options.append(display_name)
                
                if file_info['is_current']:
                    current_selection = display_name
            
            # If no files found or no Default option, add it
            if not options or "Default" not in options:
                options.insert(0, "Default")
                current_selection = "Default"
            
            # Update combobox
            self.system_message_combo['values'] = options
            self.system_message_var.set(current_selection)
            
        except Exception as e:
            print(f"Error refreshing system message options: {e}")
            # Fallback to default
            self.system_message_combo['values'] = ["Default"]
            self.system_message_var.set("Default")
    
    def _on_system_message_change(self, event):
        """Handle system message selection change."""
        try:
            selected_display_name = self.system_message_var.get()
            
            if selected_display_name == "Default":
                # Use default system message (systemmessage.txt)
                system_message_manager.set_current_system_message_file("systemmessage.txt")
            else:
                # Find the corresponding filename
                files_info = system_message_manager.get_system_message_files_info()
                
                for file_info in files_info:
                    if file_info['display_name'] == selected_display_name:
                        system_message_manager.set_current_system_message_file(file_info['filename'])
                        break
            
            # Clear current conversation for clean context switch
            self._new_conversation()
            
            # Update status to indicate both system message change and new conversation
            if system_message_manager.has_custom_system_message():
                self.status_bar.set_status(f"Switched to {selected_display_name} - New conversation started", "info")
            else:
                self.status_bar.set_status("Switched to default system message - New conversation started", "info")
                
        except Exception as e:
            print(f"Error changing system message: {e}")
            show_simple_toast(self.root, f"Error changing system message: {str(e)}", "error")
    
    def run(self):
        """Start the application."""
        self.root.mainloop()