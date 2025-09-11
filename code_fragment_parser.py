"""
Code fragment parser for extracting code blocks from AI responses.
"""
import re
from typing import List, Dict, Any
import tkinter as tk
from tkinter import messagebox
from theme import theme_manager

class CodeFragment:
    """Represents a code fragment from AI response."""
    
    def __init__(self, content: str, language: str = "", line_start: int = 0):
        self.content = content.strip()
        self.language = language
        self.line_start = line_start
        self.preview = self._create_preview()
    
    def _create_preview(self) -> str:
        """Create a preview string for the fragment."""
        lines = self.content.split('\n')
        preview_lines = lines[:3]  # First 3 lines
        
        if len(lines) > 3:
            preview_lines.append("...")
        
        preview = '\n'.join(preview_lines)
        
        # Add language info if available
        if self.language:
            return f"[{self.language}] {preview}"
        return preview

class CodeFragmentParser:
    """Parser for extracting code fragments from AI responses."""
    
    @staticmethod
    def extract_fragments(text: str) -> List[CodeFragment]:
        """
        Extract code fragments from text using ``` markers.
        
        Args:
            text: The text to parse for code fragments
            
        Returns:
            List of CodeFragment objects
        """
        fragments = []
        
        # Pattern to match code blocks with optional language specifier
        # Matches: ```language\ncode content\n``` or ```\ncode content\n```
        pattern = r'```(\w+)?\n(.*?)\n```'
        
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            language = match.group(1) or ""
            content = match.group(2)
            line_start = text[:match.start()].count('\n')
            
            if content.strip():  # Only add non-empty fragments
                fragment = CodeFragment(content, language, line_start)
                fragments.append(fragment)
        
        return fragments
    
    @staticmethod
    def has_code_fragments(text: str) -> bool:
        """
        Quick check if text contains code fragments.
        
        Args:
            text: The text to check
            
        Returns:
            True if code fragments are found
        """
        return '```' in text and text.count('```') >= 2

class CodeFragmentDialog:
    """Dialog for selecting and copying code fragments."""
    
    def __init__(self, parent, fragments: List[CodeFragment]):
        self.parent = parent
        self.fragments = fragments
        self.selected_fragment = None
        self.result = None
        
        # Get theme for consistent styling
        theme = theme_manager.get_current_theme()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Code Fragment")
        self.dialog.geometry("600x400")
        self.dialog.configure(bg=theme.colors['bg_primary'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"600x400+{x}+{y}")
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create the dialog widgets."""
        # Get current theme for consistent styling
        theme = theme_manager.get_current_theme()
        
        # Main frame
        main_frame = tk.Frame(self.dialog, bg=theme.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title and button frame
        header_frame = tk.Frame(main_frame, bg=theme.colors['bg_primary'])
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Title label
        title_label = tk.Label(header_frame, text="Found Code Fragments:", 
                              font=theme.fonts['heading'],
                              bg=theme.colors['bg_primary'],
                              fg=theme.colors['text_primary'])
        title_label.pack(side='left')
        
        # Button frame (moved to top)
        button_frame = tk.Frame(header_frame, bg=theme.colors['bg_primary'])
        button_frame.pack(side='right')
        
        # Buttons (moved to top)
        copy_btn = tk.Button(button_frame, text="Copy to Clipboard", 
                           command=self._copy_selected, 
                           bg=theme.colors['success'], fg='white', 
                           font=theme.fonts['body'],
                           relief='flat', borderwidth=0, cursor='hand2',
                           activebackground=theme.colors.get('success_hover', theme.colors['success']), 
                           activeforeground='white')
        copy_btn.pack(side='right', padx=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                             command=self._cancel,
                             bg=theme.colors['danger'], fg='white', 
                             font=theme.fonts['body'],
                             relief='flat', borderwidth=0, cursor='hand2',
                             activebackground=theme.colors.get('danger_hover', theme.colors['danger']), 
                             activeforeground='white')
        cancel_btn.pack(side='right')
        
        # Fragment list with scrollbar
        list_frame = tk.Frame(main_frame, bg=theme.colors['bg_primary'])
        list_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, bg=theme.colors['bg_secondary'])
        scrollbar.pack(side='right', fill='y')
        
        self.fragment_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                          font=theme.fonts['code_small'],
                                          bg=theme.colors['bg_secondary'],
                                          fg=theme.colors['text_primary'],
                                          selectbackground=theme.colors['selection'],
                                          selectforeground=theme.colors['text_primary'],
                                          borderwidth=1,
                                          highlightthickness=0)
        self.fragment_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.fragment_listbox.yview)
        
        # Populate the listbox
        for i, fragment in enumerate(self.fragments):
            display_text = f"Fragment {i+1}: {fragment.preview[:100]}"
            if len(fragment.preview) > 100:
                display_text += "..."
            self.fragment_listbox.insert(tk.END, display_text)
        
        # Bind selection event
        self.fragment_listbox.bind('<<ListboxSelect>>', self._on_fragment_select)
        
        # Preview area
        preview_label = tk.Label(main_frame, text="Preview:", 
                               font=theme.fonts['body_bold'],
                               bg=theme.colors['bg_primary'],
                               fg=theme.colors['text_primary'])
        preview_label.pack(anchor='w', pady=(10, 5))
        
        self.preview_text = tk.Text(main_frame, height=8, 
                                   font=theme.fonts['code'],
                                   bg=theme.colors['bg_tertiary'],
                                   fg=theme.colors['text_primary'],
                                   state='disabled', wrap='none',
                                   borderwidth=1,
                                   highlightthickness=0)
        self.preview_text.pack(fill='both', expand=True)
        
        # Select first fragment by default
        if self.fragments:
            self.fragment_listbox.selection_set(0)
            self._on_fragment_select(None)
    
    def _on_fragment_select(self, event):
        """Handle fragment selection."""
        selection = self.fragment_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_fragment = self.fragments[index]
            
            # Update preview
            self.preview_text.config(state='normal')
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', self.selected_fragment.content)
            self.preview_text.config(state='disabled')
    
    def _copy_selected(self):
        """Copy selected fragment to clipboard."""
        if self.selected_fragment:
            try:
                self.dialog.clipboard_clear()
                self.dialog.clipboard_append(self.selected_fragment.content)
                self.dialog.update()  # Ensure clipboard is updated
                
                messagebox.showinfo("Success", "Code fragment copied to clipboard!")
                self.result = self.selected_fragment
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy to clipboard: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a code fragment first.")
    
    def _cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result

def show_code_fragments_dialog(parent, text: str):
    """
    Show code fragments dialog for given text.
    
    Args:
        parent: Parent widget
        text: Text to parse for code fragments
        
    Returns:
        Selected CodeFragment or None if cancelled
    """
    fragments = CodeFragmentParser.extract_fragments(text)
    
    if not fragments:
        messagebox.showinfo("No Code Fragments", "No code fragments found in the response.")
        return None
    
    dialog = CodeFragmentDialog(parent, fragments)
    return dialog.show()