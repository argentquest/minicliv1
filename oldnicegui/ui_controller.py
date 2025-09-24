"""
UI Controller for separating UI logic from business logic.
Handles all UI creation, event binding, and state management.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional, List, Dict, Any

from theme import theme_manager
from simple_modern_ui import (
    SimpleModernButton, SimpleModernLabel, SimpleFilesList, 
    SimpleStatusBar, show_simple_toast
)
from tabbed_chat_area import TabbedChatArea
from question_history_ui import QuestionHistoryUI
from tabbed_conversation_manager import TabbedConversationManager
from models import AppState, QuestionStatus
from context_dialog import show_context_dialog


class UIController:
    """Handles UI creation, layout, and event management."""
    
    def __init__(self, root: tk.Tk, app_state: AppState, models: List[str]):
        """
        Initialize UI controller.
        
        Args:
            root: Main tkinter window
            app_state: Application state object
            models: List of available AI models
        """
        self.root = root
        self.state = app_state
        self.models = models
        
        # UI components (will be created in setup_ui)
        self.main_container = None
        self.files_list = None
        self.chat_area = None
        self.question_history_ui = None
        self.tabbed_conversation_manager = None
        self.status_bar = None
        
        # UI variables
        self.model_var = None
        self.system_message_var = None
        
        # Button references
        self.send_btn = None
        self.execute_system_btn = None
        self.theme_btn = None
        
        # Callback handlers (to be set by main application)
        self.callbacks = {}
        
    def set_callback(self, event_name: str, callback: Callable):
        """Set a callback function for UI events."""
        self.callbacks[event_name] = callback
    
    def get_callback(self, event_name: str) -> Optional[Callable]:
        """Get a callback function for UI events."""
        return self.callbacks.get(event_name)
    
    def setup_window(self):
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
    
    def create_ui(self):
        """Create the complete UI interface."""
        theme = theme_manager.get_current_theme()
        
        # Main container
        self.main_container = tk.Frame(self.root, bg=theme.colors['bg_primary'])
        self.main_container.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        
        # Configure grid weights
        self.main_container.columnconfigure(0, weight=1)  # Single column takes all space
        self.main_container.rowconfigure(1, weight=1)     # Main content area
        
        # Create sections
        self._create_header_with_actions()
        self._create_main_content_with_directory()
        self._create_status_bar()
        
        # Initialize model and system message variables
        self.model_var.set(self.state.selected_model)
        self._refresh_system_message_options()
    
    def _create_header_with_actions(self):
        """Create the header with title, selections, and action buttons."""
        theme = theme_manager.get_current_theme()
        
        header_frame = tk.Frame(self.main_container, bg=theme.colors['bg_secondary'], 
                               relief='flat', bd=1)
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 0))
        
        # Top row: Title and selections
        self._create_title_and_selections(header_frame)
        
        # Bottom row: Action buttons
        self._create_action_buttons(header_frame)
    
    def _create_title_and_selections(self, parent):
        """Create title and model/system message selections."""
        theme = theme_manager.get_current_theme()
        
        top_row = tk.Frame(parent, bg=theme.colors['bg_secondary'])
        top_row.pack(fill='x', padx=8, pady=(6, 3))
        
        # Title
        title_label = SimpleModernLabel(top_row, text="🤖 Code Chat with AI")
        title_label.pack(side='left')
        
        # Model and System Message selection
        selection_frame = tk.Frame(top_row, bg=theme.colors['bg_secondary'])
        selection_frame.pack(side='right')
        
        # Model selection
        self._create_model_selection(selection_frame)
        
        # System Message selection
        self._create_system_message_selection(selection_frame)
    
    def _create_model_selection(self, parent):
        """Create model selection UI."""
        theme = theme_manager.get_current_theme()
        
        model_frame = tk.Frame(parent, bg=theme.colors['bg_secondary'])
        model_frame.pack(side='left', padx=(0, 20))
        
        SimpleModernLabel(model_frame, text="🧠 Model:").pack(side='left', padx=(0, 8))
        
        self.model_var = tk.StringVar(value=self.state.selected_model)
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                       values=self.models, state="readonly", width=25)
        self.model_combo.pack(side='left')
        self.model_combo.bind('<<ComboboxSelected>>', self._on_model_change)
    
    def _create_system_message_selection(self, parent):
        """Create system message selection UI."""
        theme = theme_manager.get_current_theme()
        
        sysmsg_frame = tk.Frame(parent, bg=theme.colors['bg_secondary'])
        sysmsg_frame.pack(side='left')
        
        SimpleModernLabel(sysmsg_frame, text="🤖 System:").pack(side='left', padx=(0, 8))
        
        self.system_message_var = tk.StringVar()
        self.system_message_combo = ttk.Combobox(sysmsg_frame, textvariable=self.system_message_var, 
                                               state="readonly", width=15)
        self.system_message_combo.pack(side='left')
        self.system_message_combo.bind('<<ComboboxSelected>>', self._on_system_message_change)
        self.system_message_combo.configure(takefocus=True)
    
    def _create_action_buttons(self, parent):
        """Create action buttons row."""
        theme = theme_manager.get_current_theme()
        
        actions_row = tk.Frame(parent, bg=theme.colors['bg_secondary'])
        actions_row.pack(fill='x', padx=8, pady=(3, 6))
        
        # Primary actions (left side)
        self._create_primary_actions(actions_row)
        
        # Secondary actions (right side)
        self._create_secondary_actions(actions_row)
    
    def _create_primary_actions(self, parent):
        """Create primary action buttons."""
        theme = theme_manager.get_current_theme()
        
        primary_actions = tk.Frame(parent, bg=theme.colors['bg_secondary'])
        primary_actions.pack(side='left')
        
        # Context button
        context_btn = SimpleModernButton(primary_actions, text="Set Context", 
                                       command=self._on_set_context,
                                       style_type='accent', icon_action='folder',
                                       tooltip="Select files to use as context for AI conversations")
        context_btn.pack(side='left', padx=(0, 10))
        
        self.send_btn = SimpleModernButton(primary_actions, text="Send Question", 
                                         command=self._on_send_question,
                                         style_type='primary', icon_action='send',
                                         tooltip="Send your question to the AI model")
        self.send_btn.pack(side='left', padx=(0, 10))
        
        self.execute_system_btn = SimpleModernButton(primary_actions, text="Execute System Prompt", 
                                                   command=self._on_execute_system_prompt,
                                                   style_type='accent', icon_action='play',
                                                   tooltip="Execute the current system prompt without a question")
        self.execute_system_btn.pack(side='left', padx=(0, 10))
        
        clear_btn = SimpleModernButton(primary_actions, text="Clear Response", 
                                     command=self._on_clear_response, icon_action='clear',
                                     tooltip="Clear the current AI response")
        clear_btn.pack(side='left', padx=(0, 10))
        
        new_btn = SimpleModernButton(primary_actions, text="New Conversation", 
                                   command=self._on_new_conversation, icon_action='new',
                                   tooltip="Start a new conversation and clear history")
        new_btn.pack(side='left')
    
    def _create_secondary_actions(self, parent):
        """Create secondary action buttons."""
        theme = theme_manager.get_current_theme()
        
        secondary_actions = tk.Frame(parent, bg=theme.colors['bg_secondary'])
        secondary_actions.pack(side='right')
        
        save_btn = SimpleModernButton(secondary_actions, text="Save History", 
                                    command=self._on_save_history, icon_action='save',
                                    tooltip="Save conversation history to a file")
        save_btn.pack(side='left', padx=(0, 10))
        
        load_btn = SimpleModernButton(secondary_actions, text="Load History", 
                                    command=self._on_load_history, icon_action='load',
                                    tooltip="Load a previously saved conversation history")
        load_btn.pack(side='left', padx=(0, 10))
        
        settings_btn = SimpleModernButton(secondary_actions, text="Settings", 
                                        command=self._on_open_settings, icon_action='settings',
                                        tooltip="Open application settings and configuration")
        settings_btn.pack(side='left', padx=(0, 10))
        
        # Theme toggle button
        self._create_theme_toggle_button(secondary_actions)
        
        system_msg_btn = SimpleModernButton(secondary_actions, text="System Message", 
                                          command=self._on_open_system_message_editor,
                                          icon_action='ai',
                                          tooltip="Edit system messages and AI prompts")
        system_msg_btn.pack(side='left', padx=(0, 10))
        
        about_btn = SimpleModernButton(secondary_actions, text="About", 
                                     command=self._on_open_about,
                                     icon_action='info',
                                     tooltip="About this application and version information")
        about_btn.pack(side='left')
    
    def _create_theme_toggle_button(self, parent):
        """Create theme toggle button with appropriate icon and text."""
        current_theme = theme_manager.current_theme_name
        theme_icon = 'sun' if current_theme == 'dark' else 'moon'
        theme_text = '☀️ Light' if current_theme == 'dark' else '🌙 Dark'
        
        self.theme_btn = SimpleModernButton(parent, text=theme_text, 
                                          command=self._on_toggle_theme, icon_action=theme_icon,
                                          tooltip="Toggle between light and dark themes")
        self.theme_btn.pack(side='left', padx=(0, 10))
    
    def _create_main_content_with_directory(self):
        """Create the main content area."""
        theme = theme_manager.get_current_theme()
        
        # Configure main container to have only one column now
        self.main_container.columnconfigure(0, weight=1)  # Single column takes all space
        
        # Use tabbed conversation manager with enhanced chat areas
        self.tabbed_conversation_manager = TabbedConversationManager(self.main_container, 
                                                                   submit_callback=self._on_question_submitted)
        self.tabbed_conversation_manager.grid(row=1, column=0, sticky='nsew')
    
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = SimpleStatusBar(self.main_container)
        self.status_bar.grid(row=2, column=0, sticky='ew', pady=(0, 0))
    
    # Event handler methods (delegate to callbacks)
    def _on_model_change(self, event):
        """Handle model selection change."""
        callback = self.get_callback('model_change')
        if callback:
            callback(self.model_var.get())
    
    def _on_system_message_change(self, event):
        """Handle system message selection change."""
        callback = self.get_callback('system_message_change')
        if callback:
            callback(self.system_message_var.get())
    
    def _on_send_question(self):
        """Handle send question action."""
        callback = self.get_callback('send_question')
        if callback:
            callback()
    
    def _on_execute_system_prompt(self):
        """Handle execute system prompt action."""
        callback = self.get_callback('execute_system_prompt')
        if callback:
            callback()
    
    def _on_clear_response(self):
        """Handle clear response action."""
        callback = self.get_callback('clear_response')
        if callback:
            callback()
    
    def _on_new_conversation(self):
        """Handle new conversation action."""
        callback = self.get_callback('new_conversation')
        if callback:
            callback()
    
    def _on_save_history(self):
        """Handle save history action."""
        callback = self.get_callback('save_history')
        if callback:
            callback()
    
    def _on_load_history(self):
        """Handle load history action."""
        callback = self.get_callback('load_history')
        if callback:
            callback()
    
    def _on_open_settings(self):
        """Handle open settings action."""
        callback = self.get_callback('open_settings')
        if callback:
            callback()
    
    def _on_toggle_theme(self):
        """Handle theme toggle action."""
        callback = self.get_callback('toggle_theme')
        if callback:
            callback()
    
    def _on_open_system_message_editor(self):
        """Handle open system message editor action."""
        callback = self.get_callback('open_system_message_editor')
        if callback:
            callback()
    
    def _on_open_about(self):
        """Handle open about action."""
        callback = self.get_callback('open_about')
        if callback:
            callback()
    
    def _on_select_directory(self):
        """Handle directory selection."""
        callback = self.get_callback('select_directory')
        if callback:
            callback()
    
    def _on_refresh_codebase(self):
        """Handle codebase refresh."""
        callback = self.get_callback('refresh_codebase')
        if callback:
            callback()
    
    def _on_file_selection_change(self):
        """Handle file selection changes."""
        callback = self.get_callback('file_selection_change')
        if callback:
            callback()
            
    def _on_question_submitted(self, question: str):
        """Handle question submission from new UI."""
        callback = self.get_callback('question_submitted')
        if callback:
            callback(question)
            
    def _on_set_context(self):
        """Handle set context action."""
        callback = self.get_callback('set_context')
        if callback:
            callback()
    
    # UI update methods
    def update_directory_label(self, directory: str):
        """Update the directory label."""
        if hasattr(self, 'dir_label'):
            self.dir_label.configure(text=directory)
    
    def update_theme_button(self):
        """Update theme button text and icon after theme change."""
        if hasattr(self, 'theme_btn'):
            current_theme = theme_manager.current_theme_name
            theme_text = '☀️ Light' if current_theme == 'dark' else '🌙 Dark'
            self.theme_btn.configure(text=theme_text)
    
    def update_model_selection(self, models: List[str], selected_model: str):
        """Update model selection options."""
        if hasattr(self, 'model_combo'):
            self.model_combo['values'] = models
            self.model_var.set(selected_model)
    
    def enable_buttons(self, enabled: bool = True):
        """Enable or disable action buttons."""
        state = 'normal' if enabled else 'disabled'
        if hasattr(self, 'send_btn'):
            self.send_btn.configure(state=state)
        if hasattr(self, 'execute_system_btn'):
            self.execute_system_btn.configure(state=state)
    
    def set_status(self, message: str, status_type: str = 'info'):
        """Set status bar message."""
        if hasattr(self, 'status_bar'):
            self.status_bar.set_status(message, status_type)
    
    def show_toast(self, message: str, toast_type: str = 'info'):
        """Show toast notification."""
        show_simple_toast(self.root, message, toast_type)
    
    def _refresh_system_message_options(self):
        """Refresh the system message dropdown options."""
        callback = self.get_callback('refresh_system_message_options')
        if callback:
            callback()
    
    def update_system_message_options(self, options: List[str], current_selection: str):
        """Update system message dropdown options."""
        if hasattr(self, 'system_message_combo'):
            self.system_message_combo['values'] = options
            self.system_message_var.set(current_selection)
    
    # Utility methods for accessing UI components
    def get_question(self) -> str:
        """Get current question text."""
        return ""  # Questions are submitted directly in the new UI
    
    def set_response(self, response: str):
        """Set AI response."""
        # Response is handled through question status updates in new UI
        pass
    
    def clear_response(self):
        """Clear AI response."""
        # No single response area to clear in new UI
        pass
    
    def clear_question(self):
        """Clear question text."""
        # Questions are cleared automatically after submission in new UI
        pass
            
    # New methods for question history UI
    def add_question_to_history(self, question_status: QuestionStatus):
        """Add a question to the history display."""
        if hasattr(self, 'tabbed_conversation_manager'):
            # Get context files if available
            context_files = self.state.persistent_selected_files if hasattr(self.state, 'persistent_selected_files') else []
            
            # Add user message to active tab with context
            self.tabbed_conversation_manager.add_message_to_active_tab(
                'user', question_status.question, context_files=context_files)
            
    def update_question_in_history(self, question_index: int, status: str, response: str = "", 
                                  tokens_used: int = 0, processing_time: float = 0.0, model_used: str = ""):
        """Update a question's status in the history."""
        if hasattr(self, 'tabbed_conversation_manager') and status == "completed" and response:
            # Add assistant response to active tab
            self.tabbed_conversation_manager.add_message_to_active_tab(
                'assistant', response, tokens_used, processing_time, model_used)
            
    def clear_question_history(self):
        """Clear all questions from history."""
        if hasattr(self, 'tabbed_conversation_manager'):
            self.tabbed_conversation_manager.clear_active_tab()
            
    def set_question_input_enabled(self, enabled: bool):
        """Enable or disable question input."""
        if hasattr(self, 'tabbed_conversation_manager'):
            self.tabbed_conversation_manager.set_input_enabled(enabled)
    
    def get_selected_files(self) -> List[str]:
        """Get selected file paths."""
        # File selection is now handled through context dialog
        return []
    
    def get_file_selection_count(self) -> int:
        """Get number of selected files."""
        # File selection is now handled through context dialog
        return 0
    
    def add_files_to_list(self, files: List[str], file_paths: List[str]):
        """Add files to the file list."""
        # File selection is now handled through context dialog
        pass
    
    def update_conversation_history(self, conversation_history):
        """Update conversation history in chat area."""
        # Conversation history is handled by question history UI
        pass
    
    def refresh_tool_variables(self):
        """Refresh tool variables in chat area."""
        if hasattr(self, 'tabbed_conversation_manager'):
            self.tabbed_conversation_manager.refresh_tool_variables()