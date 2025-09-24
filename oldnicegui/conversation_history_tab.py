"""
Conversation history tab component for viewing full chat history.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import List, Dict, Any
import json
from datetime import datetime

from theme import theme_manager
from icons import icon_manager
from simple_modern_ui import SimpleModernButton, SimpleModernLabel, show_simple_toast
from models import ConversationMessage

class ConversationHistoryTab(tk.Frame):
    """Tab for displaying full conversation history with all turns."""
    
    def __init__(self, parent, conversation_history: List[ConversationMessage] = None):
        super().__init__(parent)
        theme = theme_manager.get_current_theme()
        self.configure(bg=theme.colors['bg_primary'])
        
        self.conversation_history = conversation_history or []
        self.parent_window = parent
        
        self._create_widgets()
        self._refresh_history()
    
    def _create_widgets(self):
        """Create the conversation history widgets."""
        theme = theme_manager.get_current_theme()
        
        # Header with controls
        header_frame = tk.Frame(self, bg=theme.colors['bg_secondary'], relief='flat', bd=1)
        header_frame.pack(fill='x', padx=5, pady=(5, 0))
        
        # Header content
        header_content = tk.Frame(header_frame, bg=theme.colors['bg_secondary'])
        header_content.pack(fill='x', padx=15, pady=15)
        
        # Title and info
        title_frame = tk.Frame(header_content, bg=theme.colors['bg_secondary'])
        title_frame.pack(fill='x')
        
        title_label = SimpleModernLabel(title_frame, text="💬 Conversation History")
        title_label.pack(side='left')
        
        self.turn_count_label = SimpleModernLabel(title_frame, text="0 turns")
        self.turn_count_label.pack(side='right')
        
        # Controls
        controls_frame = tk.Frame(header_content, bg=theme.colors['bg_secondary'])
        controls_frame.pack(fill='x', pady=(10, 0))
        
        # Refresh button
        refresh_btn = SimpleModernButton(controls_frame, text="Refresh", 
                                       command=self._refresh_history, icon_action='refresh')
        refresh_btn.pack(side='left', padx=(0, 10))
        
        # Export buttons
        export_text_btn = SimpleModernButton(controls_frame, text="Export as Text", 
                                           command=self._export_as_text, icon_action='export')
        export_text_btn.pack(side='left', padx=(0, 10))
        
        export_json_btn = SimpleModernButton(controls_frame, text="Export as JSON", 
                                           command=self._export_as_json, icon_action='export')
        export_json_btn.pack(side='left', padx=(0, 10))
        
        # Copy button
        copy_btn = SimpleModernButton(controls_frame, text="Copy All", 
                                    command=self._copy_history, icon_action='copy')
        copy_btn.pack(side='left')
        
        # Clear button
        clear_btn = SimpleModernButton(controls_frame, text="Clear History", 
                                     command=self._clear_history, icon_action='delete')
        clear_btn.pack(side='right')
        
        # Conversation display area
        display_frame = tk.Frame(self, bg=theme.colors['bg_secondary'], relief='flat', bd=1)
        display_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollable text area for conversation
        self.conversation_display = scrolledtext.ScrolledText(
            display_frame,
            wrap='word',
            bg=theme.colors['bg_tertiary'],
            relief='flat',
            borderwidth=0,
            state='disabled',
            font=('Consolas', 10)
        )
        self.conversation_display.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Configure text tags for different message types
        self._configure_text_tags()
    
    def _configure_text_tags(self):
        """Configure text tags for styling different parts of the conversation."""
        theme = theme_manager.get_current_theme()
        
        # System message tag
        self.conversation_display.tag_configure('system', 
                                              background=theme.colors['bg_accent'],
                                              foreground=theme.colors['text_secondary'],
                                              font=('Consolas', 9, 'italic'))
        
        # User message tag
        self.conversation_display.tag_configure('user', 
                                              background=theme.colors['selection'],
                                              foreground=theme.colors['text_primary'],
                                              font=('Consolas', 10, 'bold'))
        
        # Assistant message tag
        self.conversation_display.tag_configure('assistant', 
                                              foreground=theme.colors['text_primary'],
                                              font=('Consolas', 10))
        
        # Turn separator tag
        self.conversation_display.tag_configure('separator', 
                                              foreground=theme.colors['text_muted'],
                                              font=('Consolas', 9),
                                              justify='center')
        
        # Timestamp tag
        self.conversation_display.tag_configure('timestamp', 
                                              foreground=theme.colors['text_secondary'],
                                              font=('Consolas', 8))
    
    def update_conversation_history(self, conversation_history: List[ConversationMessage]):
        """Update the conversation history and refresh display."""
        self.conversation_history = conversation_history
        self._refresh_history()
    
    def _refresh_history(self):
        """Refresh the conversation history display."""
        self.conversation_display.config(state='normal')
        self.conversation_display.delete('1.0', tk.END)
        
        if not self.conversation_history:
            self.conversation_display.insert(tk.END, "💭 No conversation history yet.\n\n")
            self.conversation_display.insert(tk.END, "Start a conversation by asking a question in the Chat tab!")
            self.turn_count_label.configure(text="0 turns")
            self.conversation_display.config(state='disabled')
            return
        
        # Count actual conversation turns (exclude system messages)
        user_messages = [msg for msg in self.conversation_history if msg.role == 'user']
        self.turn_count_label.configure(text=f"{len(user_messages)} turns")
        
        # Display conversation
        turn_number = 0
        system_message_shown = False
        
        for i, message in enumerate(self.conversation_history):
            if message.role == 'system':
                if not system_message_shown:
                    self._add_system_message(message)
                    system_message_shown = True
                continue
            
            elif message.role == 'user':
                turn_number += 1
                self._add_turn_separator(turn_number)
                self._add_user_message(message, turn_number)
                
            elif message.role == 'assistant':
                self._add_assistant_message(message)
        
        # Scroll to bottom
        self.conversation_display.see(tk.END)
        self.conversation_display.config(state='disabled')
    
    def _add_system_message(self, message: ConversationMessage):
        """Add system message to display."""
        self.conversation_display.insert(tk.END, "🤖 SYSTEM MESSAGE\n", 'separator')
        self.conversation_display.insert(tk.END, "─" * 50 + "\n", 'separator')
        
        # Show preview of system message (first 200 chars)
        content = message.content
        if len(content) > 200:
            preview = content[:200] + "..."
            full_length = len(content)
            self.conversation_display.insert(tk.END, f"{preview}\n", 'system')
            self.conversation_display.insert(tk.END, f"[Full system message: {full_length} characters]\n", 'timestamp')
        else:
            self.conversation_display.insert(tk.END, f"{content}\n", 'system')
        
        self.conversation_display.insert(tk.END, "\n")
    
    def _add_turn_separator(self, turn_number: int):
        """Add turn separator."""
        separator_text = f"\n{'═' * 20} TURN {turn_number} {'═' * 20}\n"
        self.conversation_display.insert(tk.END, separator_text, 'separator')
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conversation_display.insert(tk.END, f"⏰ {timestamp}\n\n", 'timestamp')
    
    def _add_user_message(self, message: ConversationMessage, turn_number: int):
        """Add user message to display."""
        self.conversation_display.insert(tk.END, f"👤 USER (Turn {turn_number}):\n", 'user')
        self.conversation_display.insert(tk.END, f"{message.content}\n\n", 'user')
    
    def _add_assistant_message(self, message: ConversationMessage):
        """Add assistant message to display."""
        self.conversation_display.insert(tk.END, "🤖 ASSISTANT:\n", 'assistant')
        self.conversation_display.insert(tk.END, f"{message.content}\n\n", 'assistant')
    
    def _export_as_text(self):
        """Export conversation as formatted text file."""
        if not self.conversation_history:
            show_simple_toast(self.parent_window, "No conversation to export", "warning")
            return
        
        filename = filedialog.asksaveasfilename(
            parent=self.parent_window,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Conversation as Text"
        )
        
        if filename:
            try:
                content = self._format_conversation_as_text()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                show_simple_toast(self.parent_window, "Conversation exported successfully!", "info")
            except Exception as e:
                show_simple_toast(self.parent_window, f"Export failed: {str(e)}", "error")
    
    def _export_as_json(self):
        """Export conversation as JSON file."""
        if not self.conversation_history:
            show_simple_toast(self.parent_window, "No conversation to export", "warning")
            return
        
        filename = filedialog.asksaveasfilename(
            parent=self.parent_window,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Conversation as JSON"
        )
        
        if filename:
            try:
                conversation_data = {
                    "timestamp": datetime.now().isoformat(),
                    "total_turns": len([msg for msg in self.conversation_history if msg.role == 'user']),
                    "messages": [msg.to_dict() for msg in self.conversation_history]
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(conversation_data, f, indent=2, ensure_ascii=False)
                show_simple_toast(self.parent_window, "Conversation exported successfully!", "info")
            except Exception as e:
                show_simple_toast(self.parent_window, f"Export failed: {str(e)}", "error")
    
    def _format_conversation_as_text(self) -> str:
        """Format conversation as readable text."""
        lines = []
        lines.append("=" * 60)
        lines.append("CODE CHAT CONVERSATION HISTORY")
        lines.append("=" * 60)
        lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Turns: {len([msg for msg in self.conversation_history if msg.role == 'user'])}")
        lines.append("=" * 60)
        
        turn_number = 0
        
        for message in self.conversation_history:
            if message.role == 'system':
                lines.append("\n🤖 SYSTEM MESSAGE:")
                lines.append("-" * 40)
                lines.append(message.content)
                lines.append("-" * 40)
                
            elif message.role == 'user':
                turn_number += 1
                lines.append(f"\n{'═' * 20} TURN {turn_number} {'═' * 20}")
                lines.append(f"\n👤 USER:")
                lines.append(message.content)
                
            elif message.role == 'assistant':
                lines.append(f"\n🤖 ASSISTANT:")
                lines.append(message.content)
        
        lines.append("\n" + "=" * 60)
        lines.append("END OF CONVERSATION")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _copy_history(self):
        """Copy entire conversation to clipboard."""
        if not self.conversation_history:
            show_simple_toast(self.parent_window, "No conversation to copy", "warning")
            return
        
        try:
            content = self._format_conversation_as_text()
            self.clipboard_clear()
            self.clipboard_append(content)
            show_simple_toast(self.parent_window, "Conversation copied to clipboard!", "info")
        except Exception as e:
            show_simple_toast(self.parent_window, f"Copy failed: {str(e)}", "error")
    
    def _clear_history(self):
        """Clear conversation history with confirmation."""
        if not self.conversation_history:
            show_simple_toast(self.parent_window, "No conversation to clear", "warning")
            return
        
        result = messagebox.askyesno(
            "Clear Conversation",
            "Are you sure you want to clear the entire conversation history? This cannot be undone.",
            parent=self.parent_window
        )
        
        if result:
            self.conversation_history.clear()
            self._refresh_history()
            show_simple_toast(self.parent_window, "Conversation history cleared", "info")
            
            # Notify parent to update its conversation history
            if hasattr(self.parent_window, '_on_conversation_cleared'):
                self.parent_window._on_conversation_cleared()