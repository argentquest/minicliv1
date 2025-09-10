"""
Modern, beautiful version of the Code Chat application with enhanced UI.
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
from modern_ui import (
    ModernFrame, ModernButton, ModernLabel, EnhancedFilesList, 
    EnhancedChatArea, ModernStatusBar, ProgressIndicator, show_toast
)

class ModernCodeChatApp:
    """Modern, beautiful version of the Code Chat application."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = AppConfig.get_default()
        self.state = AppState()
        self.scanner = CodebaseScanner()
        
        # Load environment and initialize components
        self._load_environment()
        self._setup_window()
        self._create_modern_ui()
        
        # Initialize AI processor
        self.ai_processor = AIProcessor(self.state.api_key)
        
        # Set initial status
        self.status_bar.set_status("Ready to analyze your code! 🚀", "ready")
        
        # Load any saved theme preference
        self._apply_current_theme()
    
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
        """Configure the main window with modern styling."""
        self.root.title("🤖 Code Chat with AI - Modern Edition")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Configure for modern look
        self.root.configure(bg=theme_manager.get_current_theme().colors['bg_primary'])
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Set icon (if available)
        try:
            # Try to set a window icon
            self.root.iconname("Code Chat AI")
        except:
            pass
    
    def _create_modern_ui(self):
        """Create the modern, beautiful UI."""
        theme = theme_manager.get_current_theme()
        
        # Main container with padding
        self.main_container = ModernFrame(self.root, style_key='main_window')
        self.main_container.grid(row=0, column=0, sticky='nsew')
        
        # Configure grid weights for main container
        self.main_container.columnconfigure(1, weight=2)  # Chat area gets more space
        self.main_container.columnconfigure(0, weight=1)  # File list
        self.main_container.rowconfigure(2, weight=1)     # Main content area
        
        # Header section
        self._create_header()
        
        # Directory selection section
        self._create_directory_section()
        
        # Main content area (side by side)
        self._create_main_content()
        
        # Action buttons section
        self._create_action_buttons()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create the application header."""
        header_frame = ModernFrame(self.main_container)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        
        # App title and model selection
        title_frame = tk.Frame(header_frame, bg=theme_manager.get_current_theme().colors['bg_secondary'])
        title_frame.pack(fill='x', padx=16, pady=16)
        
        # Title
        title_label = ModernLabel(title_frame, text="🤖 Code Chat with AI", style_key='label_heading')
        title_label.pack(side='left')
        
        # Model selection
        model_frame = tk.Frame(title_frame, bg=theme_manager.get_current_theme().colors['bg_secondary'])
        model_frame.pack(side='right')
        
        ModernLabel(model_frame, text="🧠 Model:", style_key='label_body').pack(side='left', padx=(0, 8))
        
        self.model_var = tk.StringVar(value=self.state.selected_model)
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                       values=self.models, state="readonly", width=25)
        self.model_combo.pack(side='left')
        self.model_combo.bind('<<ComboboxSelected>>', self._on_model_change)
    
    def _create_directory_section(self):
        """Create the directory selection section."""
        dir_frame = ModernFrame(self.main_container)
        dir_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        
        # Directory controls
        dir_container = tk.Frame(dir_frame, bg=theme_manager.get_current_theme().colors['bg_secondary'])
        dir_container.pack(fill='x', padx=16, pady=16)
        
        # Directory label and path
        dir_info_frame = tk.Frame(dir_container, bg=theme_manager.get_current_theme().colors['bg_secondary'])
        dir_info_frame.pack(fill='x', pady=(0, 12))
        
        ModernLabel(dir_info_frame, text="📁 Codebase Directory:", style_key='label_body').pack(side='left')
        
        self.dir_label = ModernLabel(dir_info_frame, text="No directory selected", 
                                    style_key='label_secondary')
        self.dir_label.pack(side='left', padx=(12, 0))
        
        # Directory buttons
        button_frame = tk.Frame(dir_container, bg=theme_manager.get_current_theme().colors['bg_secondary'])
        button_frame.pack()
        
        self.browse_btn = ModernButton(button_frame, text="Browse", 
                                      command=self._select_directory, 
                                      style_key='button_primary', icon_action='folder')
        self.browse_btn.pack(side='left', padx=(0, 12))
        
        self.refresh_btn = ModernButton(button_frame, text="Refresh", 
                                       command=self._refresh_codebase,
                                       icon_action='refresh')
        self.refresh_btn.pack(side='left')
    
    def _create_main_content(self):
        """Create the main content area with file list and chat."""
        # File list (left side)
        self.files_list = EnhancedFilesList(self.main_container, 
                                           selection_callback=self._on_file_selection_change)
        self.files_list.grid(row=2, column=0, sticky='nsew', padx=(0, 10))
        
        # Chat area (right side)
        self.chat_area = EnhancedChatArea(self.main_container)
        self.chat_area.grid(row=2, column=1, sticky='nsew')
    
    def _create_action_buttons(self):
        """Create the action buttons section."""
        action_frame = ModernFrame(self.main_container)
        action_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(20, 0))
        
        # Button container
        button_container = tk.Frame(action_frame, bg=theme_manager.get_current_theme().colors['bg_secondary'])
        button_container.pack(padx=16, pady=16)
        
        # Primary actions
        primary_frame = tk.Frame(button_container, bg=theme_manager.get_current_theme().colors['bg_secondary'])
        primary_frame.pack(pady=(0, 12))
        
        self.send_btn = ModernButton(primary_frame, text="Send Question", 
                                    command=self._send_question,
                                    style_key='button_primary', icon_action='send')
        self.send_btn.pack(side='left', padx=(0, 12))
        
        self.clear_btn = ModernButton(primary_frame, text="Clear Response", 
                                     command=self._clear_response, icon_action='clear')
        self.clear_btn.pack(side='left', padx=(0, 12))
        
        self.new_btn = ModernButton(primary_frame, text="New Conversation", 
                                   command=self._new_conversation, icon_action='new')
        self.new_btn.pack(side='left')
        
        # Secondary actions
        secondary_frame = tk.Frame(button_container, bg=theme_manager.get_current_theme().colors['bg_secondary'])
        secondary_frame.pack()
        
        self.save_btn = ModernButton(secondary_frame, text="Save History", 
                                    command=self._save_history, icon_action='save')
        self.save_btn.pack(side='left', padx=(0, 12))
        
        self.load_btn = ModernButton(secondary_frame, text="Load History", 
                                    command=self._load_history, icon_action='load')
        self.load_btn.pack(side='left', padx=(0, 12))
        
        self.settings_btn = ModernButton(secondary_frame, text="Settings", 
                                        command=self._open_settings, icon_action='settings')
        self.settings_btn.pack(side='left')
    
    def _create_status_bar(self):
        """Create the modern status bar."""
        self.status_bar = ModernStatusBar(self.main_container)
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(20, 0))
    
    def _apply_current_theme(self):
        """Apply the current theme to the application."""
        theme = theme_manager.get_current_theme()
        theme.apply_to_root(self.root)
    
    def _on_model_change(self, event):
        """Handle model selection change."""
        self.state.selected_model = self.model_var.get()
        model_name = self.state.selected_model.split('/')[-1]  # Get just the model name
        self.status_bar.set_status(f"Switched to {model_name} model", "info")
        show_toast(self.root, f"Model changed to {model_name}", "info")
    
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
            show_toast(self.root, "Please select a directory first", "warning")
            return
        
        self.status_bar.show_progress("Scanning files")
        
        try:
            # Validate directory
            is_valid, error_msg = self.scanner.validate_directory(self.state.selected_directory)
            if not is_valid:
                self.status_bar.hide_progress()
                self.status_bar.set_status(error_msg, "error")
                show_toast(self.root, error_msg, "error")
                return
            
            # Scan for files
            files = self.scanner.scan_directory(self.state.selected_directory)
            self.state.codebase_files = files
            
            # Update files list display
            relative_paths = self.scanner.get_relative_paths(files, self.state.selected_directory)
            self.files_list.add_files(relative_paths, files)
            
            self.status_bar.hide_progress()
            self._on_file_selection_change()  # Update status with selection info
            
            show_toast(self.root, f"Found {len(files)} files", "success")
            
        except Exception as e:
            self.status_bar.hide_progress()
            error_msg = f"Error scanning files: {str(e)}"
            self.status_bar.set_status(error_msg, "error")
            show_toast(self.root, error_msg, "error")
    
    def _on_file_selection_change(self):
        """Handle file selection changes."""
        selected_count = self.files_list.get_selection_count()
        total_count = len(self.state.codebase_files)
        if total_count > 0:
            self.status_bar.set_status(f"Ready - {selected_count}/{total_count} files selected for analysis", "ready")
        else:
            self.status_bar.set_status("Ready to analyze your code! 🚀", "ready")
    
    def _send_question(self):
        """Send question to AI."""
        question = self.chat_area.get_question()
        if not question:
            show_toast(self.root, "Please enter a question", "warning")
            return
        
        if not self.ai_processor.validate_api_key():
            show_toast(self.root, "Please configure your API key in Settings", "warning")
            return
        
        # Check if any files are selected
        selected_files = self.files_list.get_selected_file_paths()
        if not selected_files:
            show_toast(self.root, "Please select files for analysis", "warning")
            return
        
        self.status_bar.show_progress("Processing your question")
        
        # Disable send button to prevent multiple requests
        self.send_btn.configure(state='disabled')
        
        # Run in separate thread
        threading.Thread(target=self._process_question_async, args=(question,), daemon=True).start()
    
    def _process_question_async(self, question):
        """Process question asynchronously."""
        try:
            # Add user message to conversation history
            user_message = {"role": "user", "content": question}
            self.state.conversation_history.append(ConversationMessage(role="user", content=question))
            
            # Get codebase content from selected files only
            selected_files = self.files_list.get_selected_file_paths()
            codebase_content = self.scanner.get_codebase_content(selected_files)
            
            # Process with AI
            ai_response = self.ai_processor.process_question(
                question=question,
                conversation_history=[msg.to_dict() for msg in self.state.conversation_history[:-1]],
                codebase_content=codebase_content,
                model=self.state.selected_model
            )
            
            # Add AI response to conversation history
            self.state.conversation_history.append(ConversationMessage(role="assistant", content=ai_response))
            
            # Update UI on main thread
            self.root.after(0, self._update_response_ui, ai_response, True)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self._update_response_ui, f"Error: {error_msg}", False)
    
    def _update_response_ui(self, response: str, success: bool):
        """Update response UI on main thread."""
        self.status_bar.hide_progress()
        self.send_btn.configure(state='normal')
        
        if success:
            self.chat_area.set_response(response)
            self.status_bar.set_status("Response received! ✨", "success")
            show_toast(self.root, "Response received!", "success")
        else:
            self.chat_area.set_response(response)
            self.status_bar.set_status("Error processing request", "error")
            show_toast(self.root, "Error processing request", "error")
    
    def _clear_response(self):
        """Clear the response area."""
        self.chat_area.clear_response()
        self.status_bar.set_status("Response cleared", "info")
    
    def _new_conversation(self):
        """Start a new conversation."""
        self.state.clear_conversation()
        self.chat_area.clear_response()
        self.chat_area.clear_question()
        self.status_bar.set_status("New conversation started! 🆕", "info")
        show_toast(self.root, "Started new conversation", "info")
    
    def _save_history(self):
        """Save conversation history."""
        if not self.state.conversation_history:
            show_toast(self.root, "No conversation history to save", "warning")
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
                self.status_bar.set_status("Conversation history saved", "success")
                show_toast(self.root, "History saved successfully!", "success")
            except Exception as e:
                error_msg = f"Error saving history: {str(e)}"
                self.status_bar.set_status(error_msg, "error")
                show_toast(self.root, error_msg, "error")
    
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
                
                self.status_bar.set_status("Conversation history loaded", "success")
                show_toast(self.root, "History loaded successfully!", "success")
            except Exception as e:
                error_msg = f"Error loading history: {str(e)}"
                self.status_bar.set_status(error_msg, "error")
                show_toast(self.root, error_msg, "error")
    
    def _open_settings(self):
        """Open modern settings dialog."""
        self._create_modern_settings_dialog()
    
    def _create_modern_settings_dialog(self):
        """Create a modern settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("500x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Apply theme
        theme = theme_manager.get_current_theme()
        settings_window.configure(bg=theme.colors['bg_primary'])
        
        # Center the dialog
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
        y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        
        # Main container
        container = ModernFrame(settings_window)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ModernLabel(container, text="⚙️ Application Settings", style_key='label_heading')
        title_label.pack(pady=(0, 20))
        
        # API Key section
        api_frame = ModernFrame(container)
        api_frame.pack(fill='x', pady=(0, 20))
        
        api_label = ModernLabel(api_frame, text="🔑 API Key:", style_key='label_body')
        api_label.pack(anchor='w', padx=16, pady=(16, 8))
        
        self.api_key_var = tk.StringVar(value=self.state.api_key)
        api_entry = tk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=50)
        api_entry.pack(padx=16, pady=(0, 16))
        
        # Apply theme to entry
        entry_style = theme.get_style('text_input')
        api_entry.configure(**entry_style)
        
        # Theme section
        theme_frame = ModernFrame(container)
        theme_frame.pack(fill='x', pady=(0, 20))
        
        theme_label = ModernLabel(theme_frame, text="🎨 Theme:", style_key='label_body')
        theme_label.pack(anchor='w', padx=16, pady=(16, 8))
        
        # Theme selection
        theme_selection_frame = tk.Frame(theme_frame, bg=theme.colors['bg_secondary'])
        theme_selection_frame.pack(padx=16, pady=(0, 16))
        
        self.theme_var = tk.StringVar(value=theme_manager.current_theme_name)
        
        light_radio = tk.Radiobutton(theme_selection_frame, text="☀️ Light Theme", 
                                   variable=self.theme_var, value="light",
                                   bg=theme.colors['bg_secondary'], fg=theme.colors['text_primary'])
        light_radio.pack(anchor='w')
        
        dark_radio = tk.Radiobutton(theme_selection_frame, text="🌙 Dark Theme", 
                                  variable=self.theme_var, value="dark",
                                  bg=theme.colors['bg_secondary'], fg=theme.colors['text_primary'])
        dark_radio.pack(anchor='w')
        
        # Buttons
        button_frame = tk.Frame(container, bg=theme.colors['bg_primary'])
        button_frame.pack(pady=(20, 0))
        
        def save_settings():
            # Save API key
            self.state.api_key = self.api_key_var.get()
            self.ai_processor.set_api_key(self.state.api_key)
            
            # Save theme preference
            new_theme = self.theme_var.get()
            if new_theme != theme_manager.current_theme_name:
                theme_manager.switch_theme(new_theme)
                show_toast(self.root, f"Theme will be applied on next restart", "info")
            
            settings_window.destroy()
            self.status_bar.set_status("Settings saved successfully! ✅", "success")
            show_toast(self.root, "Settings saved!", "success")
        
        save_btn = ModernButton(button_frame, text="Save Settings", command=save_settings,
                               style_key='button_primary', icon_action='save')
        save_btn.pack(side='left', padx=(0, 12))
        
        cancel_btn = ModernButton(button_frame, text="Cancel", command=settings_window.destroy)
        cancel_btn.pack(side='left')
        
        # Handle Enter key
        settings_window.bind('<Return>', lambda e: save_settings())
        settings_window.bind('<Escape>', lambda e: settings_window.destroy())
        
        # Focus on API key entry
        api_entry.focus()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()