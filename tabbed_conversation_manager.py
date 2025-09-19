"""
Tabbed Conversation Manager

Manages multiple conversation sessions with tabs, each containing an enhanced chat area.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Callable, Optional
import uuid
from datetime import datetime

from theme import theme_manager
from simple_modern_ui import SimpleModernButton
from enhanced_chat_area import EnhancedChatArea
from question_history_ui import QuestionInputArea
from models import ConversationMessage


class ConversationTab:
    """Represents a single conversation tab."""
    
    def __init__(self, tab_id: str, title: str = None):
        self.tab_id = tab_id
        self.title = title or f"Chat {datetime.now().strftime('%H:%M')}"
        self.chat_area = None
        self.conversation_history = []
        self.is_active = False
        self.has_unsaved_changes = False
        
    def mark_dirty(self):
        """Mark the tab as having unsaved changes."""
        self.has_unsaved_changes = True
        
    def mark_clean(self):
        """Mark the tab as saved."""
        self.has_unsaved_changes = False


class TabbedConversationManager:
    """Manages multiple conversation tabs."""
    
    def __init__(self, parent, submit_callback: Optional[Callable] = None):
        self.parent = parent
        self.theme = theme_manager.get_current_theme()
        self.submit_callback = submit_callback
        self.tabs = {}  # Dict[str, ConversationTab]
        self.active_tab_id = None
        
        # Create main frame
        self.frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        
        # Create tab interface
        self._create_tab_interface()
        
        # Create initial tab
        self._create_new_tab()
        
    def _create_tab_interface(self):
        """Create the tab bar and content area."""
        # Tab bar frame
        self.tab_bar_frame = tk.Frame(self.frame, bg=self.theme.colors['bg_secondary'], 
                                     relief='flat', bd=1)
        self.tab_bar_frame.grid(row=0, column=0, sticky='ew', padx=3, pady=(3, 1))
        
        # Tabs container (scrollable if needed)
        self.tabs_container = tk.Frame(self.tab_bar_frame, bg=self.theme.colors['bg_secondary'])
        self.tabs_container.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        
        # Tab controls
        self._create_tab_controls()
        
        # Configure main frame for grid layout
        self.frame.rowconfigure(1, weight=1)  # Content area expands
        self.frame.columnconfigure(0, weight=1)
        
        # Content area frame (for chat areas)
        self.content_frame = tk.Frame(self.frame, bg=self.theme.colors['bg_primary'])
        self.content_frame.grid(row=1, column=0, sticky='nsew', padx=3, pady=(1, 1))
        
        # Input area (shared across all tabs)
        self.input_area = QuestionInputArea(self.frame, submit_callback=self._on_question_submitted)
        self.input_area.grid(row=2, column=0, sticky='ew', padx=3, pady=(1, 3))
        
    def _create_tab_controls(self):
        """Create tab control buttons."""
        controls_frame = tk.Frame(self.tab_bar_frame, bg=self.theme.colors['bg_secondary'])
        controls_frame.pack(side='right', padx=5, pady=5)
        
        # New tab button
        new_tab_btn = SimpleModernButton(controls_frame, text="+ New", 
                                        command=self._create_new_tab,
                                        style_type='accent',
                                        tooltip="Create a new conversation tab")
        new_tab_btn.pack(side='left', padx=2)
        
        # Close tab button
        close_tab_btn = SimpleModernButton(controls_frame, text="✕", 
                                          command=self._close_current_tab,
                                          style_type='secondary',
                                          tooltip="Close current tab")
        close_tab_btn.pack(side='left', padx=2)
        
        # Save tab button
        save_tab_btn = SimpleModernButton(controls_frame, text="💾", 
                                         command=self._save_current_tab,
                                         style_type='secondary',
                                         tooltip="Save current conversation")
        save_tab_btn.pack(side='left', padx=2)
        
    def _create_new_tab(self, title: str = None):
        """Create a new conversation tab."""
        tab_id = str(uuid.uuid4())
        tab = ConversationTab(tab_id, title)
        
        # Create tab button
        tab_button = self._create_tab_button(tab)
        
        # Create chat area for this tab
        tab.chat_area = EnhancedChatArea(self.content_frame)
        
        # Add to tabs dict
        self.tabs[tab_id] = tab
        
        # Switch to new tab
        self._switch_to_tab(tab_id)
        
        return tab_id
        
    def _create_tab_button(self, tab: ConversationTab):
        """Create a button for a tab."""
        # Tab button frame
        tab_btn_frame = tk.Frame(self.tabs_container, bg=self.theme.colors['bg_secondary'])
        tab_btn_frame.pack(side='left', padx=1)
        
        # Tab button
        tab_btn = tk.Button(tab_btn_frame, 
                           text=self._get_tab_display_title(tab),
                           bg=self.theme.colors['bg_tertiary'],
                           fg=self.theme.colors['text_primary'],
                           font=('Segoe UI', 9),
                           relief='flat', bd=1,
                           cursor='hand2',
                           command=lambda: self._switch_to_tab(tab.tab_id))
        tab_btn.pack(side='left')
        
        # Store button reference
        tab.button = tab_btn
        tab.button_frame = tab_btn_frame
        
        return tab_btn
        
    def _get_tab_display_title(self, tab: ConversationTab):
        """Get the display title for a tab (with dirty indicator)."""
        title = tab.title
        if tab.has_unsaved_changes:
            title += " •"
        return title
        
    def _switch_to_tab(self, tab_id: str):
        """Switch to a specific tab."""
        if tab_id not in self.tabs:
            return
            
        # Hide current tab content
        if self.active_tab_id and self.active_tab_id in self.tabs:
            current_tab = self.tabs[self.active_tab_id]
            if current_tab.chat_area:
                current_tab.chat_area.frame.pack_forget()
            current_tab.is_active = False
            # Update button appearance
            if hasattr(current_tab, 'button'):
                current_tab.button.config(bg=self.theme.colors['bg_tertiary'])
                
        # Show new tab content
        new_tab = self.tabs[tab_id]
        if new_tab.chat_area:
            new_tab.chat_area.frame.pack(fill='both', expand=True)
        new_tab.is_active = True
        
        # Update button appearance
        if hasattr(new_tab, 'button'):
            new_tab.button.config(bg=self.theme.colors['primary'])
            
        self.active_tab_id = tab_id
        
    def _close_current_tab(self):
        """Close the current tab."""
        if not self.active_tab_id:
            return
            
        # Don't close if it's the last tab
        if len(self.tabs) <= 1:
            messagebox.showwarning("Cannot Close", "Cannot close the last tab. Create a new tab first.")
            return
            
        tab = self.tabs[self.active_tab_id]
        
        # Check for unsaved changes
        if tab.has_unsaved_changes:
            result = messagebox.askyesnocancel("Unsaved Changes", 
                                              f"Tab '{tab.title}' has unsaved changes. Save before closing?")
            if result is None:  # Cancel
                return
            elif result:  # Yes, save
                self._save_current_tab()
                
        # Remove tab
        tab_id = self.active_tab_id
        
        # Destroy UI elements
        if hasattr(tab, 'button_frame'):
            tab.button_frame.destroy()
        if tab.chat_area:
            tab.chat_area.frame.destroy()
            
        # Remove from tabs dict
        del self.tabs[tab_id]
        
        # Switch to another tab
        remaining_tab_ids = list(self.tabs.keys())
        if remaining_tab_ids:
            self._switch_to_tab(remaining_tab_ids[0])
        else:
            self.active_tab_id = None
            
    def _save_current_tab(self):
        """Save the current tab's conversation."""
        if not self.active_tab_id:
            return
            
        tab = self.tabs[self.active_tab_id]
        # Implementation would save to file
        # For now, just mark as clean
        tab.mark_clean()
        self._update_tab_title(tab)
        
    def _update_tab_title(self, tab: ConversationTab):
        """Update the tab button title."""
        if hasattr(tab, 'button'):
            tab.button.config(text=self._get_tab_display_title(tab))
            
    def get_active_chat_area(self) -> Optional[EnhancedChatArea]:
        """Get the chat area of the active tab."""
        if self.active_tab_id and self.active_tab_id in self.tabs:
            return self.tabs[self.active_tab_id].chat_area
        return None
        
    def add_message_to_active_tab(self, role: str, content: str, 
                                 tokens_used: int = 0, processing_time: float = 0.0, 
                                 model_used: str = "", context_files: List[str] = None):
        """Add a message to the active tab."""
        chat_area = self.get_active_chat_area()
        if chat_area:
            chat_area.add_message(role, content, tokens_used, processing_time, model_used, context_files)
            # Mark tab as dirty
            if self.active_tab_id:
                self.tabs[self.active_tab_id].mark_dirty()
                self._update_tab_title(self.tabs[self.active_tab_id])
                
    def clear_active_tab(self):
        """Clear the active tab's conversation."""
        chat_area = self.get_active_chat_area()
        if chat_area:
            chat_area.clear_chat()
            if self.active_tab_id:
                tab = self.tabs[self.active_tab_id]
                tab.conversation_history.clear()
                tab.mark_clean()
                self._update_tab_title(tab)
                
    def update_last_message(self, content: str, tokens_used: int = 0, 
                           processing_time: float = 0.0, model_used: str = ""):
        """Update the last message in the active tab."""
        chat_area = self.get_active_chat_area()
        if chat_area:
            chat_area.update_last_message(content, tokens_used, processing_time, model_used)
            # Mark tab as dirty
            if self.active_tab_id:
                self.tabs[self.active_tab_id].mark_dirty()
                self._update_tab_title(self.tabs[self.active_tab_id])
                
    def rename_active_tab(self, new_title: str):
        """Rename the active tab."""
        if self.active_tab_id and self.active_tab_id in self.tabs:
            tab = self.tabs[self.active_tab_id]
            tab.title = new_title
            self._update_tab_title(tab)
            
    def get_tab_count(self) -> int:
        """Get the number of open tabs."""
        return len(self.tabs)
        
    def _on_question_submitted(self, question: str):
        """Handle question submission from input area."""
        if self.submit_callback:
            self.submit_callback(question)
            
    def set_input_enabled(self, enabled: bool):
        """Enable or disable the input area."""
        if hasattr(self, 'input_area'):
            self.input_area.set_enabled(enabled)
            
    def refresh_tool_variables(self):
        """Refresh tool variables in input area."""
        if hasattr(self, 'input_area'):
            self.input_area.refresh_tool_variables()
        
    def pack(self, **kwargs):
        """Pack the main frame."""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the main frame."""
        self.frame.grid(**kwargs)