"""
Simplified modern version of the Code Chat application with better compatibility.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from models import AppState, AppConfig, ConversationMessage
from lazy_file_scanner import CodebaseScanner, LazyCodebaseScanner
from ai import AIProcessor, create_ai_processor
from theme import theme_manager
from icons import icon_manager
from simple_modern_ui import show_simple_toast
from env_settings_dialog import EnvSettingsDialog
from env_manager import env_manager
from system_message_dialog import SystemMessageDialog
from system_message_manager import system_message_manager
from ui_controller import UIController

class SimpleModernCodeChatApp:
    """Simplified modern version of the Code Chat application."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = AppConfig.get_default()
        self.state = AppState()
        self.scanner = CodebaseScanner()
        self.lazy_scanner = None  # Will be created when needed for large codebases
        
        # Load environment and initialize components
        self._load_environment()
        
        # Reload theme preference after dotenv loads .env file
        theme_manager._load_theme_preference()
        
        # Initialize UI controller
        self.ui_controller = UIController(self.root, self.state, self.models)
        self._setup_ui_callbacks()
        
        # Setup window and UI
        self.ui_controller.setup_window()
        self.ui_controller.create_ui()
        
        # Initialize AI processor with provider from environment
        ai_provider_name = os.getenv("PROVIDER", "openrouter")
        self.ai_processor = create_ai_processor(self.state.api_key, ai_provider_name)
        
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
    
    def _setup_ui_callbacks(self):
        """Setup callbacks for UI controller events."""
        self.ui_controller.set_callback('model_change', self._on_model_change)
        self.ui_controller.set_callback('system_message_change', self._on_system_message_change)
        self.ui_controller.set_callback('send_question', self._send_question)
        self.ui_controller.set_callback('execute_system_prompt', self._execute_system_prompt)
        self.ui_controller.set_callback('clear_response', self._clear_response)
        self.ui_controller.set_callback('new_conversation', self._new_conversation)
        self.ui_controller.set_callback('save_history', self._save_history)
        self.ui_controller.set_callback('load_history', self._load_history)
        self.ui_controller.set_callback('open_settings', self._open_settings)
        self.ui_controller.set_callback('toggle_theme', self._toggle_theme)
        self.ui_controller.set_callback('open_system_message_editor', self._open_system_message_editor)
        self.ui_controller.set_callback('open_about', self._open_about)
        self.ui_controller.set_callback('select_directory', self._select_directory)
        self.ui_controller.set_callback('refresh_codebase', self._refresh_codebase)
        self.ui_controller.set_callback('file_selection_change', self._on_file_selection_change)
        self.ui_controller.set_callback('refresh_system_message_options', self._refresh_system_message_options)
    
    # UI creation is now handled by UIController
    
    # Old UI creation methods removed - now handled by UIController
    
    def _on_model_change(self, model):
        """Handle model selection change."""
        self.state.selected_model = model
        model_name = self.state.selected_model.split('/')[-1]
        self.ui_controller.set_status(f"Switched to {model_name} model", "info")
    
    def _select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(title="Select Codebase Directory")
        if directory:
            self.state.selected_directory = directory
            self.ui_controller.update_directory_label(directory)
            self._refresh_codebase()
    
    def _refresh_codebase(self):
        """Refresh the codebase file list with lazy loading for large codebases."""
        if not self.state.selected_directory:
            self.ui_controller.show_toast("Please select a directory first", "warning")
            return
        
        self.ui_controller.set_status("Scanning files...", "info")
        
        try:
            # Validate directory
            is_valid, error_msg = self.scanner.validate_directory(self.state.selected_directory)
            if not is_valid:
                self.ui_controller.set_status(error_msg, "error")
                self.ui_controller.show_toast(error_msg, "error")
                return
            
            # Check if this is a large codebase that needs lazy loading
            if self._should_use_lazy_loading(self.state.selected_directory):
                self._refresh_codebase_lazy()
            else:
                self._refresh_codebase_standard()
                
        except Exception as e:
            error_msg = f"Error scanning files: {str(e)}"
            self.ui_controller.set_status(error_msg, "error")
            self.ui_controller.show_toast(error_msg, "error")
    
    def _should_use_lazy_loading(self, directory: str) -> bool:
        """Determine if lazy loading should be used for this directory."""
        try:
            # Quick directory size estimate
            file_count = 0
            total_size = 0
            
            # Sample first 100 files to estimate
            for root, dirs, filenames in os.walk(directory):
                # Skip common ignore folders for quick check
                dirs[:] = [d for d in dirs if d not in {'node_modules', '__pycache__', '.git', 'venv', '.venv'}]
                
                for filename in filenames[:10]:  # Sample first 10 files per directory
                    if filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                        file_count += 1
                        try:
                            file_path = os.path.join(root, filename)
                            total_size += os.path.getsize(file_path)
                        except OSError:
                            continue
                
                # Stop early if we've sampled enough
                if file_count > 50:
                    break
            
            # Use lazy loading if estimated to be large
            # Thresholds: > 200 files OR > 10MB total size OR deep directory structure
            estimated_total_files = file_count * 5  # Conservative estimate
            return (estimated_total_files > 200 or 
                   total_size > 10 * 1024 * 1024 or
                   len(Path(directory).parts) > 8)
            
        except Exception:
            return False  # Default to standard loading on error
    
    def _refresh_codebase_standard(self):
        """Standard codebase refresh for smaller projects."""
        files = self.scanner.scan_directory(self.state.selected_directory)
        self.state.codebase_files = files
        
        # Update files list display
        relative_paths = self.scanner.get_relative_paths(files, self.state.selected_directory)
        self.ui_controller.add_files_to_list(relative_paths, files)
        
        self._on_file_selection_change()  # Update status
    
    def _refresh_codebase_lazy(self):
        """Lazy codebase refresh for large projects."""
        if not self.lazy_scanner:
            self.lazy_scanner = LazyCodebaseScanner()
        
        # Start lazy scanning in background
        threading.Thread(target=self._lazy_scan_worker, daemon=True).start()
    
    def _lazy_scan_worker(self):
        """Background worker for lazy file scanning."""
        try:
            files = []
            file_infos = []
            total_batches = 0
            
            def progress_callback(current, total):
                if total > 0:
                    progress = (current / total) * 100
                    status = f"Scanning files... {progress:.0f}% ({current}/{total})"
                    self.root.after(0, self.ui_controller.set_status, status, "info")
            
            # Collect files from lazy scanner
            for file_batch in self.lazy_scanner.scan_directory_lazy(
                self.state.selected_directory, 
                progress_callback=progress_callback
            ):
                for file_info in file_batch:
                    files.append(file_info.path)
                    file_infos.append(file_info)
                total_batches += 1
                
                # Update UI periodically
                if total_batches % 5 == 0:  # Every 5 batches
                    self._update_lazy_scan_ui(files, file_infos)
            
            # Final UI update
            self._update_lazy_scan_ui(files, file_infos, final=True)
            
        except Exception as e:
            error_msg = f"Error scanning files: {str(e)}"
            self.root.after(0, self.ui_controller.set_status, error_msg, "error")
    
    def _update_lazy_scan_ui(self, files: List[str], file_infos: List, final: bool = False):
        """Update UI with lazy scan results."""
        def update_ui():
            self.state.codebase_files = files[:]
            
            # Get relative paths
            relative_paths = []
            for file_info in file_infos:
                relative_paths.append(file_info.relative_path)
            
            self.ui_controller.add_files_to_list(relative_paths, files)
            
            if final:
                # Show final status with performance info
                cache_stats = self.lazy_scanner.get_cache_stats()
                status_msg = f"Scanned {len(files)} files in {cache_stats['total_scan_time']:.1f}s"
                if len(files) > 500:
                    status_msg += " (lazy loading enabled)"
                self.ui_controller.set_status(status_msg, "success")
            
            self._on_file_selection_change()
        
        self.root.after(0, update_ui)
    
    def _on_file_selection_change(self):
        """Handle file selection changes."""
        selected_count = self.ui_controller.get_file_selection_count()
        total_count = len(self.state.codebase_files)
        persistent_count = len(self.state.get_persistent_files())
        
        if total_count > 0:
            status_msg = f"Ready - {selected_count}/{total_count} files selected"
            if persistent_count > 0 and len(self.state.conversation_history) > 0:
                status_msg += f" (using {persistent_count} persistent files from first turn)"
            self.ui_controller.set_status(status_msg, "ready")
        else:
            self.ui_controller.set_status("Ready to analyze your code! 🚀", "ready")
    
    def _send_question(self):
        """Send question to AI."""
        question = self.ui_controller.get_question()
        if not question:
            self.ui_controller.show_toast("Please enter a question", "warning")
            return
        
        if not self.ai_processor.validate_api_key():
            self.ui_controller.show_toast("Please configure your API key in Settings", "warning")
            return
        
        # Check if any files are selected or if we have persistent files from previous turn
        selected_files = self.ui_controller.get_selected_files()
        persistent_files = self.state.get_persistent_files()
        is_first_message = len(self.state.conversation_history) == 0
        
        if is_first_message and not selected_files:
            self.ui_controller.show_toast("Please select files for analysis", "warning")
            return
        elif not is_first_message and not selected_files and not persistent_files:
            self.ui_controller.show_toast("No files available for analysis. Please select files or start a new conversation.", "warning")
            return
        
        self.ui_controller.set_status("Processing your question...", "info")
        self.ui_controller.enable_buttons(False)
        
        # Run in separate thread
        threading.Thread(target=self._process_question_async, args=(question,), daemon=True).start()
    
    def _execute_system_prompt(self):
        """Execute the system prompt directly without a user question."""
        if not self.ai_processor.validate_api_key():
            self.ui_controller.show_toast("Please configure your API key in Settings", "warning")
            return
        
        # Check if any files are selected or if we have persistent files from previous turn
        selected_files = self.ui_controller.get_selected_files()
        persistent_files = self.state.get_persistent_files()
        is_first_message = len(self.state.conversation_history) == 0
        
        if is_first_message and not selected_files:
            self.ui_controller.show_toast("Please select files for analysis", "warning")
            return
        elif not is_first_message and not selected_files and not persistent_files:
            self.ui_controller.show_toast("No files available for analysis. Please select files or start a new conversation.", "warning")
            return
        
        self.ui_controller.set_status("Executing system prompt...", "info")
        self.ui_controller.enable_buttons(False)
        
        # Run in separate thread - pass empty string as question to indicate system prompt execution
        threading.Thread(target=self._process_system_prompt_async, daemon=True).start()
    
    def _process_system_prompt_async(self):
        """Process system prompt execution asynchronously."""
        try:
            # Get codebase content for system prompt
            is_first_message = len(self.state.conversation_history) == 0
            codebase_content = self._get_codebase_content_for_question(is_first_message, needs_codebase_context=True)
            
            # Get the system message content and process it
            system_message = system_message_manager.get_system_message(codebase_content)
            ai_response = self._process_system_message_with_ai(system_message)
            
            # Update conversation history for system prompt execution
            self._update_system_prompt_conversation_history(ai_response)
            
            # Update UI on main thread
            self.root.after(0, self._finalize_system_prompt_processing, ai_response, True)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self._finalize_system_prompt_processing, f"Error executing system prompt: {error_msg}", False)
    
    def _process_question_async(self, question):
        """Process question asynchronously."""
        try:
            # Determine conversation context
            is_first_message = len(self.state.conversation_history) == 0
            needs_codebase_context = is_first_message or self._is_tool_command(question)
            
            # Add user message to conversation history
            self.state.conversation_history.append(ConversationMessage(role="user", content=question))
            
            # Get codebase content based on context
            codebase_content = self._get_codebase_content_for_question(is_first_message, needs_codebase_context)
            
            # Process question with AI
            ai_response = self._process_with_ai(question, codebase_content)
            
            # Update conversation history with response
            self._update_conversation_history(ai_response, is_first_message, codebase_content)
            
            # Update UI on main thread
            self.root.after(0, self._finalize_question_processing, ai_response, True)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self._finalize_question_processing, f"Error: {error_msg}", False)
    
    def _get_codebase_content_for_question(self, is_first_message: bool, needs_codebase_context: bool) -> str:
        """Get codebase content based on question context with lazy loading optimization."""
        if not needs_codebase_context:
            return ""  # Not needed for regular follow-up messages
        
        if is_first_message:
            # First message: use currently selected files and save them for future use
            selected_files = self.ui_controller.get_selected_files()
            if selected_files:
                self.state.set_persistent_files(selected_files)
                return self._get_file_content_optimized(selected_files)
            return ""
        else:
            # Subsequent messages with tool commands: use persistent files if available
            persistent_files = self.state.get_persistent_files()
            if persistent_files:
                return self._get_file_content_optimized(persistent_files)
            
            # Fallback to currently selected files if no persistent files
            selected_files = self.ui_controller.get_selected_files()
            if selected_files:
                return self._get_file_content_optimized(selected_files)
            
            return ""
    
    def _get_file_content_optimized(self, files: List[str]) -> str:
        """Get file content using the most appropriate scanner (lazy or standard)."""
        if self.lazy_scanner and len(files) > 50:  # Use lazy loading for many files
            return self.lazy_scanner.get_codebase_content_lazy(files)
        else:
            return self.scanner.get_codebase_content(files)
    
    def _process_with_ai(self, question: str, codebase_content: str) -> str:
        """Process question with AI and return response."""
        return self.ai_processor.process_question(
            question=question,
            conversation_history=[msg.to_dict() for msg in self.state.conversation_history[:-1]],
            codebase_content=codebase_content,
            model=self.state.selected_model,
            update_callback=lambda response, status: self.root.after(0, self.ui_controller.set_status, status, "success")
        )
    
    def _update_conversation_history(self, ai_response: str, is_first_message: bool, codebase_content: str):
        """Update conversation history with AI response and system message if needed."""
        # Add AI response to conversation history
        self.state.conversation_history.append(ConversationMessage(role="assistant", content=ai_response))
        
        # If this was the first message, add the system message to our history
        if is_first_message:
            system_msg_content = system_message_manager.get_system_message(codebase_content)
            system_message = ConversationMessage(role="system", content=system_msg_content)
            # Insert at the beginning of conversation history
            self.state.conversation_history.insert(0, system_message)
    
    def _process_system_message_with_ai(self, system_message: str) -> str:
        """Process system message with AI and return response."""
        return self.ai_processor.process_question(
            question=system_message,
            conversation_history=[],  # No conversation history for system prompt execution
            codebase_content="",      # Already included in system message
            model=self.state.selected_model,
            update_callback=lambda response, status: self.root.after(0, self.ui_controller.set_status, status, "success")
        )
    
    def _update_system_prompt_conversation_history(self, ai_response: str):
        """Update conversation history for system prompt execution."""
        self.state.conversation_history.append(ConversationMessage(role="user", content="[System Prompt Executed]"))
        self.state.conversation_history.append(ConversationMessage(role="assistant", content=ai_response))
    
    def _finalize_system_prompt_processing(self, response: str, success: bool):
        """Finalize system prompt processing by updating UI."""
        # Update conversation history in tabbed chat area
        self._update_conversation_in_tabs()
        
        # Update response UI
        self._update_response_ui(response, success)
    
    def _finalize_question_processing(self, response: str, success: bool):
        """Finalize question processing by updating UI."""
        # Update conversation history in tabbed chat area
        self._update_conversation_in_tabs()
        
        # Update response UI
        self._update_response_ui(response, success)
    
    def _update_conversation_in_tabs(self):
        """Update conversation history in the tabbed chat area."""
        self.ui_controller.update_conversation_history(self.state.conversation_history)
    
    def _on_conversation_cleared(self):
        """Handle conversation cleared event from history tab."""
        # This is called when the user clears the conversation from the history tab
        self.state.clear_conversation()
        self.ui_controller.set_status("Conversation cleared from history tab", "info")
        # Update file selection status to remove persistent files indicator
        self._on_file_selection_change()
    
    def _update_response_ui(self, response: str, success: bool):
        """Update response UI on main thread."""
        self.ui_controller.enable_buttons(True)
        
        if success:
            self.ui_controller.set_response(response)
            # Don't override status here - token info is set by the AI processor callback
        else:
            self.ui_controller.set_response(response)
            self.ui_controller.set_status("Error processing request", "error")
    
    def _clear_response(self):
        """Clear the response area."""
        self.ui_controller.clear_response()
        self.ui_controller.set_status("Response cleared", "info")
    
    def _new_conversation(self):
        """Start a new conversation."""
        self.state.clear_conversation()
        self.ui_controller.clear_response()
        self.ui_controller.clear_question()
        self._update_conversation_in_tabs()  # Update history tab
        self.ui_controller.set_status("New conversation started! 🆕", "info")
    
    def _save_history(self):
        """Save conversation history with file locking."""
        if not self.state.conversation_history:
            self.ui_controller.show_toast("No conversation history to save", "warning")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Conversation History"
        )
        
        if filename:
            try:
                from file_lock import safe_json_save
                
                # Use safe JSON save with file locking and backup
                if safe_json_save(self.state.get_conversation_dict(), filename, timeout=10.0, backup=True):
                    self.ui_controller.set_status("History saved successfully!", "success")
                else:
                    raise Exception("Failed to save history due to file locking error")
                    
            except Exception as e:
                error_msg = f"Error saving history: {str(e)}"
                self.ui_controller.set_status(error_msg, "error")
                self.ui_controller.show_toast(error_msg, "error")
    
    def _load_history(self):
        """Load conversation history with file locking."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Conversation History"
        )
        
        if filename:
            try:
                from file_lock import safe_json_load
                
                # Use safe JSON load with file locking
                history = safe_json_load(filename, timeout=10.0, default=None)
                
                if history is None:
                    raise Exception("Failed to load history or file is empty")
                
                # Convert dict format back to ConversationMessage objects
                self.state.conversation_history = [
                    ConversationMessage(role=msg["role"], content=msg["content"])
                    for msg in history
                ]
                
                # Update conversation history in tabs
                self._update_conversation_in_tabs()
                
                self.ui_controller.set_status("History loaded successfully!", "success")
                
            except Exception as e:
                error_msg = f"Error loading history: {str(e)}"
                self.ui_controller.set_status(error_msg, "error")
                self.ui_controller.show_toast(error_msg, "error")
    
    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        try:
            # Toggle the theme
            old_theme = theme_manager.current_theme_name
            theme_manager.toggle_theme()
            new_theme = theme_manager.current_theme_name
            
            # Update the theme button text and icon
            self.ui_controller.update_theme_button()
            
            # Save the theme preference to environment
            from env_manager import env_manager
            env_manager.update_single_var('UI_THEME', new_theme)
            
            # Show status message
            self.ui_controller.set_status(f"Switched to {new_theme} theme - Restart for full effect", "info")
            self.ui_controller.show_toast(f"Theme changed to {new_theme}.\nRestart the application for full effect.", "info")
            
        except Exception as e:
            error_msg = f"Error changing theme: {str(e)}"
            self.status_bar.set_status(error_msg, "error")
            show_simple_toast(self.root, error_msg, "error")
    
    def _open_settings(self):
        """Open enhanced environment settings dialog."""
        EnvSettingsDialog(self.root, self._on_settings_saved)
    
    def _on_settings_saved(self, env_vars):
        """Handle settings saved callback."""
        self._update_api_key_from_settings(env_vars)
        self._update_models_from_settings(env_vars)
        self._update_scanner_from_settings(env_vars)
        self._update_tool_variables_from_settings(env_vars)
        
        self.ui_controller.set_status("Settings applied successfully! ✅", "success")
    
    def _update_api_key_from_settings(self, env_vars):
        """Update API key from settings if changed."""
        if 'API_KEY' in env_vars:
            self.state.api_key = env_vars['API_KEY']
            self.ai_processor.set_api_key(self.state.api_key)
    
    def _update_models_from_settings(self, env_vars):
        """Update model configurations from settings."""
        # Update models if changed
        if 'MODELS' in env_vars:
            self.models = [m.strip() for m in env_vars['MODELS'].split(',') if m.strip()]
            # Update model selection in UI
            if self.state.selected_model not in self.models and self.models:
                self.state.selected_model = self.models[0]
            self.ui_controller.update_model_selection(self.models, self.state.selected_model)
        
        # Update default model if changed
        if 'DEFAULT_MODEL' in env_vars and env_vars['DEFAULT_MODEL'] in self.models:
            self.state.selected_model = env_vars['DEFAULT_MODEL']
            self.ui_controller.update_model_selection(self.models, self.state.selected_model)
    
    def _update_scanner_from_settings(self, env_vars):
        """Update scanner configuration from settings."""
        if 'IGNORE_FOLDERS' in env_vars:
            self.scanner = CodebaseScanner()  # Reinitialize to pick up new ignore folders
            
            # Refresh current directory if one is selected
            if self.state.selected_directory:
                self._refresh_codebase()
    
    def _update_tool_variables_from_settings(self, env_vars):
        """Update tool variables from settings."""
        tool_vars_changed = any(key.startswith('TOOL') for key in env_vars.keys())
        if tool_vars_changed:
            self.ui_controller.refresh_tool_variables()
    
    def _open_system_message_editor(self):
        """Open system message editor dialog."""
        SystemMessageDialog(self.root)
    
    def _is_tool_command(self, question: str) -> bool:
        """Check if the question contains a tool command that needs codebase context."""
        # Load tool variables to check against
        try:
            from env_manager import env_manager
            from pattern_matcher import pattern_matcher
            
            all_vars = env_manager.load_env_file()
            tool_vars = {key: value for key, value in all_vars.items() if key.startswith('TOOL')}
            
            # Use advanced pattern matching with confidence threshold
            return pattern_matcher.is_tool_command(question, tool_vars, threshold=0.5)
            
        except Exception:
            # If we can't load tool vars or pattern matcher, default to False
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
            self.ui_controller.set_status(f"Ready to analyze your code! 🚀 (Using {display_name} system message)", "ready")
        else:
            self.ui_controller.set_status("Ready to analyze your code! 🚀", "ready")
    
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
            
            # Update system message options in UI
            self.ui_controller.update_system_message_options(options, current_selection)
            
        except Exception as e:
            print(f"Error refreshing system message options: {e}")
            # Fallback to default
            self.ui_controller.update_system_message_options(["Default"], "Default")
    
    def _on_system_message_change(self, selected_display_name):
        """Handle system message selection change."""
        try:
            
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
                self.ui_controller.set_status(f"Switched to {selected_display_name} - New conversation started", "info")
            else:
                self.ui_controller.set_status("Switched to default system message - New conversation started", "info")
                
        except Exception as e:
            print(f"Error changing system message: {e}")
            self.ui_controller.show_toast(f"Error changing system message: {str(e)}", "error")
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Main entry point - handles both CLI and GUI modes."""
    import sys
    
    # Check if CLI mode is requested
    if '--cli' in sys.argv:
        # CLI mode
        from cli_interface import CLIInterface
        
        cli = CLIInterface()
        parser = cli.setup_argument_parser()
        
        try:
            args = parser.parse_args()
            exit_code = cli.run_cli(args)
            sys.exit(exit_code)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Unexpected error: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        # GUI mode (default)
        try:
            root = tk.Tk()
            app = SimpleModernCodeChatApp(root)
            app.run()
        except KeyboardInterrupt:
            print("\nApplication closed by user.")
        except Exception as e:
            print(f"ERROR: Failed to start GUI application: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()