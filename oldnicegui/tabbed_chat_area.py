"""
Tabbed chat area with conversation history view.
"""
import tkinter as tk
from tkinter import ttk
from typing import List, Callable

from theme import theme_manager
from simple_modern_ui import SimpleChatArea
from conversation_history_tab import ConversationHistoryTab
from models import ConversationMessage

class TabbedChatArea(tk.Frame):
    """Chat area with tabs for current conversation and full history."""
    
    def __init__(self, parent, conversation_history: List[ConversationMessage] = None, parent_window=None, send_callback=None):
        super().__init__(parent)
        theme = theme_manager.get_current_theme()
        self.configure(bg=theme.colors['bg_primary'])
        
        self.conversation_history = conversation_history or []
        self.parent_window = parent_window or parent  # Use provided parent_window or fallback to parent
        self.send_callback = send_callback
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the tabbed chat interface."""
        theme = theme_manager.get_current_theme()
        
        # Create notebook for tabs
        style = ttk.Style()
        
        # Configure tab style to match theme
        style.configure('Chat.TNotebook', 
                       background=theme.colors['bg_primary'],
                       borderwidth=0)
        style.configure('Chat.TNotebook.Tab', 
                       background=theme.colors['bg_secondary'],
                       foreground=theme.colors['text_primary'],
                       padding=[12, 8],
                       focuscolor='none')
        style.map('Chat.TNotebook.Tab',
                 background=[('selected', theme.colors['primary']),
                           ('active', theme.colors['hover'])],
                 foreground=[('selected', 'white')])
        
        self.notebook = ttk.Notebook(self, style='Chat.TNotebook')
        self.notebook.pack(fill='both', expand=True)
        
        # Create chat tab
        self.chat_tab = SimpleChatArea(self.notebook, send_callback=self.send_callback)
        self.notebook.add(self.chat_tab, text='💬 Chat')
        
        # Create conversation history tab
        self.history_tab = ConversationHistoryTab(self.notebook, self.conversation_history)
        self.history_tab.parent_window = self.parent_window  # Set correct parent window reference
        self.notebook.add(self.history_tab, text='📜 History')
        
        # Bind tab change event
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        # Set initial tab
        self.notebook.select(0)  # Start with chat tab
    
    def _on_tab_changed(self, event):
        """Handle tab change events."""
        selected_tab = self.notebook.select()
        tab_index = self.notebook.index(selected_tab)
        
        if tab_index == 1:  # History tab selected
            # Refresh history when switching to history tab
            self.history_tab.update_conversation_history(self.conversation_history)
    
    def update_conversation_history(self, conversation_history: List[ConversationMessage]):
        """Update conversation history in both tabs."""
        self.conversation_history = conversation_history
        
        # Update history tab if it exists
        if hasattr(self, 'history_tab'):
            self.history_tab.update_conversation_history(conversation_history)
        
        # Update tab text to show turn count
        if conversation_history:
            user_messages = [msg for msg in conversation_history if msg.role == 'user']
            turn_count = len(user_messages)
            if turn_count > 0:
                self.notebook.tab(1, text=f'📜 History ({turn_count})')
            else:
                self.notebook.tab(1, text='📜 History')
        else:
            self.notebook.tab(1, text='📜 History')
    
    def switch_to_chat_tab(self):
        """Switch to the chat tab."""
        self.notebook.select(0)
    
    def switch_to_history_tab(self):
        """Switch to the history tab."""
        self.notebook.select(1)
    
    def get_current_tab_name(self) -> str:
        """Get the name of the currently selected tab."""
        selected_tab = self.notebook.select()
        tab_index = self.notebook.index(selected_tab)
        return "chat" if tab_index == 0 else "history"
    
    # Proxy methods to maintain compatibility with SimpleChatArea interface
    def get_question(self) -> str:
        """Get the current question text from chat tab."""
        return self.chat_tab.get_question()
    
    def clear_question(self):
        """Clear the question text area in chat tab."""
        self.chat_tab.clear_question()
    
    def set_response(self, response: str):
        """Set the response text in chat tab."""
        self.chat_tab.set_response(response)
    
    def clear_response(self):
        """Clear the response text area in chat tab."""
        self.chat_tab.clear_response()
    
    def refresh_tool_variables(self):
        """Refresh TOOL variables in the chat tab."""
        if hasattr(self.chat_tab, 'refresh_tool_variables'):
            self.chat_tab.refresh_tool_variables()
    
    def reset_splitter(self):
        """Reset the chat splitter to 50/50."""
        if hasattr(self.chat_tab, 'reset_splitter'):
            self.chat_tab.reset_splitter()
    
    def set_splitter_ratio(self, ratio: float):
        """Set the chat splitter ratio (0.0 to 1.0)."""
        if hasattr(self.chat_tab, 'set_splitter_ratio'):
            self.chat_tab.set_splitter_ratio(ratio)
    
    def get_splitter_ratio(self) -> float:
        """Get the current chat splitter ratio."""
        if hasattr(self.chat_tab, 'get_splitter_ratio'):
            return self.chat_tab.get_splitter_ratio()
        return 0.5
    
    def _on_conversation_cleared(self):
        """Handle conversation cleared event from history tab."""
        # Clear conversation in main app
        self.conversation_history.clear()
        self.update_conversation_history([])
        
        # Clear chat tab
        self.clear_response()
        self.clear_question()
        
        # Notify parent if needed
        if hasattr(self.parent_window, '_on_conversation_cleared'):
            self.parent_window._on_conversation_cleared()

class ChatTabIndicator(tk.Frame):
    """Visual indicator showing which tab is active and conversation status."""
    
    def __init__(self, parent):
        super().__init__(parent)
        theme = theme_manager.get_current_theme()
        self.configure(bg=theme.colors['bg_secondary'])
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create indicator widgets."""
        from simple_modern_ui import SimpleModernLabel
        
        # Current tab indicator
        self.tab_label = SimpleModernLabel(self, text="💬 Active: Chat")
        self.tab_label.pack(side='left', padx=10, pady=5)
        
        # Conversation status
        self.status_label = SimpleModernLabel(self, text="🔄 Ready for new conversation")
        self.status_label.pack(side='right', padx=10, pady=5)
    
    def update_tab_status(self, tab_name: str, turn_count: int = 0):
        """Update the tab status display."""
        if tab_name == "chat":
            self.tab_label.configure(text="💬 Active: Chat")
        else:
            self.tab_label.configure(text="📜 Active: History")
        
        if turn_count == 0:
            self.status_label.configure(text="🔄 Ready for new conversation")
        else:
            self.status_label.configure(text=f"💭 Conversation: {turn_count} turns")