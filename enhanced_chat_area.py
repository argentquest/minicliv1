"""
Enhanced Chat Area with Traditional Chat Bubbles and Expandable Functionality

This combines the best of both worlds:
- Traditional chat message display with user/assistant bubbles
- Expandable chat turns for detailed viewing
- Rich text display with syntax highlighting
- Message actions (copy, regenerate, edit)
- Tabbed conversations for multiple sessions
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import List, Callable, Optional, Dict, Any, Tuple
import re
import time
from datetime import datetime
import keyword

CODE_FRAGMENT_PATTERN = re.compile(
    r"```(?P<lang>[^\n`]*)\n?(?P<code_bt>[\s\S]*?)```|'''(?P<code_sq>[\s\S]*?)'''",
    re.MULTILINE,
)

from theme import theme_manager
from simple_modern_ui import SimpleModernButton, SimpleModernLabel
from models import ConversationMessage, QuestionStatus


class ChatMessage:
    """Represents a single chat message with metadata."""
    
    def __init__(self, role: str, content: str, timestamp: str = None, 
                 tokens_used: int = 0, processing_time: float = 0.0, model_used: str = ""):
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        self.tokens_used = tokens_used
        self.processing_time = processing_time
        self.model_used = model_used
        self.is_expanded = False
        self.widget_refs = {}  # Store widget references for updates


class EnhancedChatArea:
    """Enhanced chat area with traditional bubbles and expandable functionality."""
    
    def __init__(self, parent, conversation_history: List[ConversationMessage] = None):
        self.parent = parent
        self.theme = theme_manager.get_current_theme()
        self.conversation_history = conversation_history or []
        self.chat_messages = []  # ChatMessage objects
        
        # Create main frame
        self.frame = tk.Frame(parent, bg=self.theme.colors['bg_primary'])
        
        # Create chat display
        self._create_chat_display()
        
        # Convert existing conversation history
        self._convert_conversation_history()
        
    def _create_chat_display(self):
        """Create the scrollable chat display area."""
        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(self.frame, bg=self.theme.colors['bg_primary'], 
                               highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", 
                                      command=self.canvas.yview)
        
        # Scrollable frame that will contain the messages
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
        
    def _convert_conversation_history(self):
        """Convert existing conversation history to chat messages."""
        for msg in self.conversation_history:
            chat_msg = ChatMessage(msg.role, msg.content)
            self.chat_messages.append(chat_msg)
            self._create_message_widget(chat_msg)
            
    def add_message(self, role: str, content: str, tokens_used: int = 0, 
                   processing_time: float = 0.0, model_used: str = "", 
                   context_files: List[str] = None):
        """Add a new message to the chat."""
        chat_msg = ChatMessage(role, content, tokens_used=tokens_used,
                              processing_time=processing_time, model_used=model_used)
        
        # Add context files if provided
        if context_files:
            chat_msg.context_files = context_files
            
        self.chat_messages.append(chat_msg)
        self._create_message_widget(chat_msg)
        
        # Scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        
    def _create_message_widget(self, chat_msg: ChatMessage):
        """Create a widget for a single chat message."""
        # Message container
        msg_container = tk.Frame(self.scrollable_frame, bg=self.theme.colors['bg_primary'])
        msg_container.pack(fill='x', padx=5, pady=3)
        
        # Determine message alignment and styling
        if chat_msg.role == 'user':
            self._create_user_message(msg_container, chat_msg)
        elif chat_msg.role == 'assistant':
            self._create_assistant_message(msg_container, chat_msg)
        elif chat_msg.role == 'system':
            self._create_system_message(msg_container, chat_msg)
            
        # Store widget reference
        chat_msg.widget_refs['container'] = msg_container
        
    def _create_user_message(self, container, chat_msg: ChatMessage):
        """Create a user message bubble (right-aligned)."""
        # Right-aligned frame
        right_frame = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        right_frame.pack(side='right', fill='x', expand=True, padx=(50, 0))
        
        # Message bubble
        bubble_frame = tk.Frame(right_frame, bg=self.theme.colors['primary'], 
                               relief='flat', bd=0)
        bubble_frame.pack(side='right', padx=5, pady=2)
        
        # Message header (timestamp, actions)
        header_frame = tk.Frame(bubble_frame, bg=self.theme.colors['primary'])
        header_frame.pack(fill='x', padx=8, pady=(6, 2))
        
        # User label
        user_label = tk.Label(header_frame, text="You", 
                             bg=self.theme.colors['primary'], fg='white',
                             font=('Segoe UI', 9, 'bold'))
        user_label.pack(side='left')
        
        # Timestamp
        time_label = tk.Label(header_frame, text=chat_msg.timestamp,
                             bg=self.theme.colors['primary'], fg='white',
                             font=('Segoe UI', 8))
        time_label.pack(side='right')
        
        # Message actions
        self._create_message_actions(header_frame, chat_msg, is_user=True)
        
        # Context files display (if any)
        if hasattr(chat_msg, 'context_files') and chat_msg.context_files:
            self._create_context_files_display(bubble_frame, chat_msg, is_user=True)
        
        # Message content
        self._create_message_content(bubble_frame, chat_msg, fg_color='white', 
                                   bg_color=self.theme.colors['primary'])
        
    def _create_assistant_message(self, container, chat_msg: ChatMessage):
        """Create an assistant message bubble (left-aligned)."""
        # Left-aligned frame
        left_frame = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        left_frame.pack(side='left', fill='x', expand=True, padx=(0, 50))
        
        # Message bubble
        bubble_frame = tk.Frame(left_frame, bg=self.theme.colors['bg_secondary'], 
                               relief='solid', bd=1)
        bubble_frame.pack(side='left', padx=5, pady=2)
        
        # Message header
        header_frame = tk.Frame(bubble_frame, bg=self.theme.colors['bg_secondary'])
        header_frame.pack(fill='x', padx=8, pady=(6, 2))
        
        # Assistant label with model info
        model_text = f"AI"
        if chat_msg.model_used:
            model_short = chat_msg.model_used.split('/')[-1]
            model_text += f" ({model_short})"
            
        ai_label = tk.Label(header_frame, text=model_text,
                           bg=self.theme.colors['bg_secondary'], 
                           fg=self.theme.colors['text_primary'],
                           font=('Segoe UI', 9, 'bold'))
        ai_label.pack(side='left')
        
        # Statistics
        if chat_msg.tokens_used > 0:
            stats_text = f"{chat_msg.tokens_used} tokens • {chat_msg.processing_time:.1f}s"
            stats_label = tk.Label(header_frame, text=stats_text,
                                 bg=self.theme.colors['bg_secondary'],
                                 fg=self.theme.colors['text_secondary'],
                                 font=('Segoe UI', 8))
            stats_label.pack(side='left', padx=(10, 0))
        
        # Timestamp
        time_label = tk.Label(header_frame, text=chat_msg.timestamp,
                             bg=self.theme.colors['bg_secondary'], 
                             fg=self.theme.colors['text_secondary'],
                             font=('Segoe UI', 8))
        time_label.pack(side='right')
        
        # Message actions
        self._create_message_actions(header_frame, chat_msg, is_user=False)
        
        # Message content
        self._create_message_content(bubble_frame, chat_msg, 
                                   fg_color=self.theme.colors['text_primary'],
                                   bg_color=self.theme.colors['bg_secondary'])
        
    def _create_system_message(self, container, chat_msg: ChatMessage):
        """Create a system message (centered)."""
        # Centered frame
        center_frame = tk.Frame(container, bg=self.theme.colors['bg_primary'])
        center_frame.pack(expand=True, padx=20)
        
        # System message bubble
        bubble_frame = tk.Frame(center_frame, bg=self.theme.colors['bg_accent'], 
                               relief='flat', bd=1)
        bubble_frame.pack(padx=5, pady=2)
        
        # System label
        sys_label = tk.Label(bubble_frame, text="🤖 System", 
                            bg=self.theme.colors['bg_accent'], 
                            fg=self.theme.colors['text_primary'],
                            font=('Segoe UI', 9, 'bold'))
        sys_label.pack(padx=8, pady=(4, 2))
        
        # Message content (truncated for system messages)
        content_preview = chat_msg.content[:100] + "..." if len(chat_msg.content) > 100 else chat_msg.content
        content_label = tk.Label(bubble_frame, text=content_preview,
                                bg=self.theme.colors['bg_accent'],
                                fg=self.theme.colors['text_secondary'],
                                font=('Segoe UI', 8),
                                wraplength=300, justify='center')
        content_label.pack(padx=8, pady=(0, 4))
        
    def _create_context_files_display(self, parent, chat_msg: ChatMessage, is_user: bool):
        """Create a display for context files."""
        context_frame = tk.Frame(parent, bg=parent.cget('bg'))
        context_frame.pack(fill='x', padx=8, pady=(0, 4))
        
        # Context header
        context_label = tk.Label(context_frame, text="📁 Context Files:",
                               bg=parent.cget('bg'), 
                               fg='white' if is_user else self.theme.colors['text_primary'],
                               font=('Segoe UI', 8, 'bold'))
        context_label.pack(anchor='w')
        
        # Files list (show up to 3 files, then "and X more")
        files_to_show = chat_msg.context_files[:3]
        for file_path in files_to_show:
            file_name = file_path.split('/')[-1]  # Get just filename
            file_label = tk.Label(context_frame, text=f"• {file_name}",
                                bg=parent.cget('bg'),
                                fg='white' if is_user else self.theme.colors['text_secondary'],
                                font=('Segoe UI', 8))
            file_label.pack(anchor='w', padx=(10, 0))
            
        # Show "and X more" if there are more files
        if len(chat_msg.context_files) > 3:
            more_count = len(chat_msg.context_files) - 3
            more_label = tk.Label(context_frame, text=f"• ... and {more_count} more files",
                                bg=parent.cget('bg'),
                                fg='white' if is_user else self.theme.colors['text_secondary'],
                                font=('Segoe UI', 8, 'italic'))
            more_label.pack(anchor='w', padx=(10, 0))
        
    def _create_message_actions(self, parent, chat_msg: ChatMessage, is_user: bool):
        """Create action buttons for a message."""
        actions_frame = tk.Frame(parent, bg=parent.cget('bg'))
        actions_frame.pack(side='right', padx=(5, 0))

        code_fragments = self._find_code_fragments(chat_msg.content)

        # Expand/Collapse button
        expand_btn = tk.Button(
            actions_frame,
            text="??" if not chat_msg.is_expanded else "??",
            bg=parent.cget('bg'),
            fg='white' if is_user else self.theme.colors['text_primary'],
            font=('Arial', 10),
            relief='flat',
            bd=0,
            cursor='hand2',
            command=lambda: self._toggle_message_expand(chat_msg),
        )
        expand_btn.pack(side='left', padx=1)

        # Copy button
        copy_btn = tk.Button(
            actions_frame,
            text="??",
            bg=parent.cget('bg'),
            fg='white' if is_user else self.theme.colors['text_primary'],
            font=('Arial', 10),
            relief='flat',
            bd=0,
            cursor='hand2',
            command=lambda: self._copy_message(chat_msg),
        )
        copy_btn.pack(side='left', padx=1)

        if code_fragments:
            extract_btn = tk.Button(
                actions_frame,
                text="Extract",
                bg=parent.cget('bg'),
                fg='white' if is_user else self.theme.colors['text_primary'],
                font=('Arial', 10),
                relief='flat',
                bd=0,
                cursor='hand2',
                command=lambda: self._open_extract_dialog(chat_msg),
            )
            extract_btn.pack(side='left', padx=1)

        # Regenerate button (only for assistant messages)
        if not is_user and chat_msg.role == 'assistant':
            regen_btn = tk.Button(
                actions_frame,
                text="??",
                bg=parent.cget('bg'),
                fg=self.theme.colors['text_primary'],
                font=('Arial', 10),
                relief='flat',
                bd=0,
                cursor='hand2',
                command=lambda: self._regenerate_response(chat_msg),
            )
            regen_btn.pack(side='left', padx=1)

        # Store button references
        chat_msg.widget_refs['expand_btn'] = expand_btn
        chat_msg.widget_refs['actions_frame'] = actions_frame

    def _create_message_content(self, parent, chat_msg: ChatMessage, fg_color: str, bg_color: str):
        """Create the message content area with syntax highlighting."""
        # Content frame
        content_frame = tk.Frame(parent, bg=bg_color)
        content_frame.pack(fill='both', expand=True, padx=8, pady=(0, 8))
        
        # Determine initial height based on expand state
        initial_height = 10 if chat_msg.is_expanded else 3
        
        # Create text widget for rich content
        text_widget = tk.Text(content_frame, wrap=tk.WORD, 
                             height=initial_height,
                             bg=bg_color, fg=fg_color,
                             font=('Consolas', 11),
                             relief='flat', bd=0,
                             state='disabled',
                             cursor='arrow')
        text_widget.pack(fill='both', expand=True)
        
        # Add content with basic syntax highlighting
        text_widget.config(state='normal')
        self._add_rich_content(text_widget, chat_msg.content, fg_color, bg_color)
        text_widget.config(state='disabled')
        
        # Store widget reference
        chat_msg.widget_refs['content_widget'] = text_widget
        chat_msg.widget_refs['content_frame'] = content_frame
        

    def _find_code_fragments(self, content: str) -> List[Dict[str, str]]:
        '''Return ordered code fragments extracted from the message text.'''
        fragments: List[Dict[str, str]] = []
        if not content:
            return fragments

        for match in CODE_FRAGMENT_PATTERN.finditer(content):
            code_value = match.group('code_bt') if match.group('code_bt') is not None else match.group('code_sq')
            if not code_value:
                continue
            language = (match.group('lang') or '').strip()
            fragments.append(
                {
                    'language': language,
                    'code': code_value.strip(),
                }
            )

        return fragments

    def _open_extract_dialog(self, chat_msg: ChatMessage):
        '''Show extracted code fragments in a popup for copying.'''
        fragments = self._find_code_fragments(chat_msg.content)
        if not fragments:
            messagebox.showinfo("Extract Code", "No code fragments found in this message.")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("Extracted Code Fragments")
        dialog.configure(bg=self.theme.colors['bg_primary'])
        dialog.geometry("720x420")
        dialog.transient(self.parent)
        dialog.grab_set()

        def close_dialog():
            try:
                dialog.grab_release()
            except Exception:
                pass
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

        content_frame = tk.Frame(dialog, bg=self.theme.colors['bg_primary'])
        content_frame.pack(fill='both', expand=True, padx=12, pady=12)

        list_frame = tk.Frame(content_frame, bg=self.theme.colors['bg_primary'])
        list_frame.pack(side='left', fill='y')

        preview_items = []
        for index, fragment in enumerate(fragments, start=1):
            language = fragment['language'] or 'Code'
            snippet = fragment['code'].strip()
            first_line = snippet.splitlines()[0] if snippet else '(empty fragment)'
            preview_items.append(f"{index}. {language} - {first_line[:60]}")

        list_var = tk.StringVar(value=preview_items)
        select_bg = self.theme.colors.get('accent', self.theme.colors.get('bg_accent', '#4d4d4d'))
        listbox = tk.Listbox(
            list_frame,
            listvariable=list_var,
            height=min(len(preview_items), 12),
            bg=self.theme.colors['bg_secondary'],
            fg=self.theme.colors['text_primary'],
            activestyle='none',
            exportselection=False,
            selectbackground=select_bg,
        )
        listbox.pack(side='left', fill='y')
        list_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=listbox.yview)
        list_scroll.pack(side='right', fill='y')
        listbox.config(yscrollcommand=list_scroll.set)

        text_frame = tk.Frame(content_frame, bg=self.theme.colors['bg_primary'])
        text_frame.pack(side='left', fill='both', expand=True, padx=(12, 0))

        info_label = tk.Label(
            text_frame,
            text='Select a fragment to preview it.',
            anchor='w',
            bg=self.theme.colors['bg_primary'],
            fg=self.theme.colors['text_secondary'],
            font=('Segoe UI', 9, 'italic'),
        )
        info_label.pack(fill='x', pady=(0, 6))

        code_text = tk.Text(
            text_frame,
            wrap='none',
            font=('Consolas', 10),
            bg=self.theme.colors['bg_secondary'],
            fg=self.theme.colors['text_primary'],
            state='disabled',
        )
        code_text.pack(fill='both', expand=True)
        text_scroll = ttk.Scrollbar(text_frame, orient='vertical', command=code_text.yview)
        text_scroll.pack(side='right', fill='y')
        code_text.config(yscrollcommand=text_scroll.set)

        button_frame = tk.Frame(dialog, bg=self.theme.colors['bg_primary'])
        button_frame.pack(fill='x', padx=12, pady=(0, 12))

        selected_index = {'value': None}

        def show_fragment(event=None):
            selection = listbox.curselection()
            if not selection:
                selected_index['value'] = None
                code_text.config(state='normal')
                code_text.delete('1.0', tk.END)
                code_text.config(state='disabled')
                info_label.config(text='Select a fragment to preview it.')
                copy_btn.config(state='disabled')
                return

            idx = selection[0]
            selected_index['value'] = idx
            fragment = fragments[idx]
            language = fragment['language'] or 'Plain text'
            info_label.config(text=f"Language: {language}")
            code_text.config(state='normal')
            code_text.delete('1.0', tk.END)
            code_text.insert('1.0', fragment['code'])
            code_text.config(state='disabled')
            copy_btn.config(state='normal')

        def copy_selected():
            idx = selected_index['value']
            if idx is None:
                return
            try:
                self.parent.clipboard_clear()
                self.parent.clipboard_append(fragments[idx]['code'])
            except Exception as exc:
                messagebox.showerror('Copy Failed', f'Could not copy code: {exc}')
            else:
                info_label.config(text='Code copied to clipboard.')

        copy_btn = tk.Button(
            button_frame,
            text='Copy to Clipboard',
            state='disabled',
            bg=self.theme.colors['bg_secondary'],
            fg=self.theme.colors['text_primary'],
            relief='flat',
            bd=0,
            cursor='hand2',
            command=copy_selected,
        )
        copy_btn.pack(side='left', padx=(0, 8))

        close_btn = tk.Button(
            button_frame,
            text='Close',
            bg=self.theme.colors['bg_secondary'],
            fg=self.theme.colors['text_primary'],
            relief='flat',
            bd=0,
            cursor='hand2',
            command=close_dialog,
        )
        close_btn.pack(side='left')

        listbox.bind('<<ListboxSelect>>', show_fragment)
        if preview_items:
            listbox.selection_set(0)
            show_fragment()
            listbox.focus_set()
        dialog.focus_force()

    def _add_rich_content(self, text_widget, content: str, fg_color: str, bg_color: str):
        """Add content with markdown-aware styling."""
        text_widget.delete('1.0', tk.END)
        self._ensure_rich_text_tags(text_widget)

        if not content:
            return

        lines = content.splitlines()
        in_code_block = False
        code_language = ''
        code_lines: List[str] = []

        for index, line in enumerate(lines):
            stripped = line.rstrip('
')
            is_last_line = index == len(lines) - 1

            if stripped.strip().startswith('```'):
                fence = stripped.strip()
                if in_code_block:
                    self._insert_code_block(text_widget, code_lines, code_language)
                    code_lines = []
                    code_language = ''
                    in_code_block = False
                    if not is_last_line:
                        text_widget.insert(tk.END, '
')
                else:
                    code_language = fence[3:].strip().lower()
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(stripped)
            else:
                self._insert_markdown_line(text_widget, stripped)
                if not is_last_line:
                    text_widget.insert(tk.END, '
')

        if in_code_block:
            self._insert_code_block(text_widget, code_lines, code_language)

    def _ensure_rich_text_tags(self, text_widget: tk.Text):
        """Configure text tags used for rich formatting once per widget."""
        if getattr(text_widget, '_rich_tags_configured', False):
            return

        colors = self.theme.colors
        accent = colors.get('accent', '#5b8def')
        text_primary = colors.get('text_primary', '#f5f5f5')
        text_secondary = colors.get('text_secondary', '#b0b0b0')
        code_bg = colors.get('bg_tertiary', '#1f1f1f')
        inline_bg = colors.get('bg_secondary', '#2a2a2a')
        blockquote_bg = colors.get('bg_secondary', '#2e2e2e')

        text_widget.tag_configure('heading1', font=('Consolas', 16, 'bold'), foreground=text_primary, spacing3=6)
        text_widget.tag_configure('heading2', font=('Consolas', 14, 'bold'), foreground=text_primary, spacing3=4)
        text_widget.tag_configure('heading3', font=('Consolas', 12, 'bold'), foreground=text_primary, spacing3=4)
        text_widget.tag_configure('paragraph', foreground=text_primary, spacing3=4)
        text_widget.tag_configure('inline_code', font=('Consolas', 11), background=inline_bg, foreground=accent, relief='flat')
        text_widget.tag_configure('code', font=('Consolas', 11), background=code_bg, foreground=text_primary, lmargin1=12, lmargin2=12, spacing3=8, spacing1=4)
        text_widget.tag_configure('code_keyword', foreground='#ffd479')
        text_widget.tag_configure('code_string', foreground='#9cdcfe')
        text_widget.tag_configure('code_comment', foreground='#7c7c7c')
        text_widget.tag_configure('blockquote', foreground=text_secondary, background=blockquote_bg, lmargin1=12, lmargin2=16, spacing3=6)
        text_widget.tag_configure('list_bullet', foreground=accent, font=('Consolas', 11, 'bold'))
        text_widget.tag_configure('bold', font=('Consolas', 11, 'bold'))
        text_widget.tag_configure('italic', font=('Consolas', 11, 'italic'))
        text_widget.tag_configure('link', foreground=accent, underline=True)

        text_widget._rich_tags_configured = True

    def _insert_markdown_line(self, text_widget: tk.Text, line: str):
        """Render a single non-code markdown line."""
        stripped = line.strip('
')
        if not stripped:
            text_widget.insert(tk.END, '
')
            return

        if stripped.startswith('>'):
            content = stripped.lstrip('> ').strip()
            start_index = text_widget.index(tk.END)
            self._insert_inline_text(text_widget, content, ('blockquote',))
            end_index = text_widget.index(tk.END)
            text_widget.tag_add('blockquote', start_index, end_index)
            return

        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            level = min(level, 3)
            content = stripped[level:].strip() or stripped
            tag = f'heading{level}'
            self._insert_inline_text(text_widget, content, (tag,))
            return

        bullet_match = re.match(r'^(?:[-*]|\d+\.)\s+(.*)', stripped)
        if bullet_match:
            value = bullet_match.group(1)
            text_widget.insert(tk.END, '• ', ('list_bullet',))
            self._insert_inline_text(text_widget, value, ('paragraph',))
            return

        self._insert_inline_text(text_widget, stripped, ('paragraph',))

    def _insert_inline_text(self, text_widget: tk.Text, text: str, base_tags: Tuple[str, ...] = ()): 
        pattern = re.compile(r'(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^\)]+\))')
        position = 0
        for match in pattern.finditer(text):
            if match.start() > position:
                segment = text[position:match.start()]
                text_widget.insert(tk.END, segment, base_tags)

            token = match.group(0)
            if token.startswith('`'):
                text_widget.insert(tk.END, token[1:-1], base_tags + ('inline_code',))
            elif token.startswith('**'):
                text_widget.insert(tk.END, token[2:-2], base_tags + ('bold',))
            elif token.startswith('*'):
                text_widget.insert(tk.END, token[1:-1], base_tags + ('italic',))
            else:
                link_match = re.match(r'^\[([^\]]+)\]\(([^\)]+)\)$', token)
                if link_match:
                    label = link_match.group(1)
                    text_widget.insert(tk.END, label, base_tags + ('link',))
            position = match.end()

        if position < len(text):
            text_widget.insert(tk.END, text[position:], base_tags)

    def _insert_code_block(self, text_widget: tk.Text, code_lines: List[str], language: str):
        if not code_lines:
            return

        code_text = '
'.join(code_lines).rstrip('
') + '
'
        start_index = text_widget.index(tk.END)
        text_widget.insert(tk.END, code_text)
        end_index = text_widget.index(tk.END)
        text_widget.tag_add('code', start_index, end_index)

        if language in {'python', 'py'}:
            self._highlight_python_code(text_widget, start_index, end_index)

    def _highlight_python_code(self, text_widget: tk.Text, start: str, end: str):
        import io
        import tokenize

        code = text_widget.get(start, end)
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
        except tokenize.TokenError:
            return

        base_line = int(start.split('.')[0])

        for token_type, token_string, (srow, scol), (erow, ecol), _ in tokens:
            line_start = base_line + srow - 1
            line_end = base_line + erow - 1
            start_index = f"{line_start}.{scol}"
            end_index = f"{line_end}.{ecol}"

            if token_type == tokenize.NAME and keyword.iskeyword(token_string):
                text_widget.tag_add('code_keyword', start_index, end_index)
            elif token_type == tokenize.STRING:
                text_widget.tag_add('code_string', start_index, end_index)
            elif token_type == tokenize.COMMENT:
                text_widget.tag_add('code_comment', start_index, end_index)
def _toggle_message_expand(self, chat_msg: ChatMessage):
        """Toggle the expanded state of a message."""
        chat_msg.is_expanded = not chat_msg.is_expanded
        
        # Update expand button
        if 'expand_btn' in chat_msg.widget_refs:
            btn = chat_msg.widget_refs['expand_btn']
            btn.config(text="⬇️" if chat_msg.is_expanded else "⬆️")
            
        # Update content widget height
        if 'content_widget' in chat_msg.widget_refs:
            widget = chat_msg.widget_refs['content_widget']
            new_height = 15 if chat_msg.is_expanded else 3
            widget.config(height=new_height)
            
        # Update canvas scroll region
        self.canvas.update_idletasks()
        
    def _copy_message(self, chat_msg: ChatMessage):
        """Copy message content to clipboard."""
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(chat_msg.content)
            # Could add a toast notification here
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            
    def _regenerate_response(self, chat_msg: ChatMessage):
        """Regenerate the assistant response."""
        # This would trigger a regeneration callback
        # For now, just show a placeholder
        messagebox.showinfo("Regenerate", "Regeneration feature coming soon!")
        
    def clear_chat(self):
        """Clear all messages from the chat."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.chat_messages.clear()
        
    def update_last_message(self, content: str, tokens_used: int = 0, 
                           processing_time: float = 0.0, model_used: str = ""):
        """Update the last message with new content and stats."""
        if self.chat_messages:
            last_msg = self.chat_messages[-1]
            last_msg.content = content
            last_msg.tokens_used = tokens_used
            last_msg.processing_time = processing_time
            last_msg.model_used = model_used
            
            # Recreate the message widget
            if 'container' in last_msg.widget_refs:
                last_msg.widget_refs['container'].destroy()
            self._create_message_widget(last_msg)
            
    def pack(self, **kwargs):
        """Pack the main frame."""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the main frame."""
        self.frame.grid(**kwargs)
