"""
System message manager for custom AI system messages.
"""
import os
from typing import Optional, List, Dict, Any
from common.env_manager import env_manager

class SystemMessageManager:
    """Manages system messages from file or default."""
    
    def __init__(self, system_message_file: str = "systemmessage_default.txt"):
        self.system_message_file = system_message_file
        
        # Load current system prompt from environment or use default
        try:
            env_vars = env_manager.load_env_file()
            saved_prompt = env_vars.get('CURRENT_SYSTEM_PROMPT', system_message_file)
            self.current_message_file = saved_prompt
            
            # If CURRENT_SYSTEM_PROMPT wasn't in the .env file, save the default
            if 'CURRENT_SYSTEM_PROMPT' not in env_vars:
                env_manager.update_single_var('CURRENT_SYSTEM_PROMPT', system_message_file)
        except Exception:
            self.current_message_file = system_message_file
            # Try to save the default value
            try:
                env_manager.update_single_var('CURRENT_SYSTEM_PROMPT', system_message_file)
            except Exception:
                pass  # Ignore if we can't save
            
        self.default_system_message = (
            "You are a helpful AI assistant that helps with code analysis. "
            "The user has provided the following codebase:\n\n{codebase_content}"
        )
    
    def get_system_message(self, codebase_content: str) -> str:
        """
        Get system message, either from currently selected file or default.
        
        Args:
            codebase_content: The codebase content to include in the message
            
        Returns:
            Complete system message ready for AI
        """
        custom_message = self.load_custom_system_message(self.current_message_file)
        
        if custom_message:
            # Use custom system message
            # Replace placeholder if it exists
            if "{codebase_content}" in custom_message:
                return custom_message.format(codebase_content=codebase_content)
            else:
                # If no placeholder, append codebase content
                return f"{custom_message}\n\nThe user has provided the following codebase:\n\n{codebase_content}"
        else:
            # Use default system message
            return self.default_system_message.format(codebase_content=codebase_content)
    
    def load_custom_system_message(self, filename: str = None) -> Optional[str]:
        """
        Load custom system message from file.
        
        Args:
            filename: Specific filename to load, defaults to current_message_file
        
        Returns:
            Custom system message content or None if file doesn't exist or error
        """
        target_file = filename if filename else self.current_message_file
        
        if not os.path.exists(target_file):
            return None
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                return None
                
            return content
            
        except Exception as e:
            print(f"Error reading system message file: {e}")
            return None
    
    def save_custom_system_message(self, message: str) -> bool:
        """
        Save custom system message to file.
        
        Args:
            message: System message content to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.system_message_file, 'w', encoding='utf-8') as f:
                f.write(message)
            return True
        except Exception as e:
            print(f"Error saving system message file: {e}")
            return False
    
    def delete_custom_system_message(self) -> bool:
        """
        Delete custom system message file to revert to default.
        
        Returns:
            True if deleted successfully or file doesn't exist, False on error
        """
        if not os.path.exists(self.system_message_file):
            return True
        
        try:
            os.remove(self.system_message_file)
            return True
        except Exception as e:
            print(f"Error deleting system message file: {e}")
            return False
    
    def has_custom_system_message(self) -> bool:
        """
        Check if current system message file exists and has content.
        
        Returns:
            True if current system message exists, False otherwise
        """
        return self.load_custom_system_message(self.current_message_file) is not None
    
    def scan_system_message_files(self) -> List[str]:
        """
        Scan for all files that start with 'systemmessage'.
        
        Returns:
            List of system message filenames found
        """
        try:
            files = []
            current_dir = os.getcwd()
            
            for filename in os.listdir(current_dir):
                if filename.startswith('systemmessage') and filename.endswith('.txt'):
                    # Check if file has content
                    if self.load_custom_system_message(filename):
                        files.append(filename)
            
            # Sort files for consistent ordering
            return sorted(files)
            
        except Exception as e:
            print(f"Error scanning for system message files: {e}")
            return []
    
    def get_system_message_files_info(self) -> List[dict]:
        """
        Get detailed information about all system message files.
        
        Returns:
            List of dictionaries with file info
        """
        files = self.scan_system_message_files()
        file_info = []
        
        for filename in files:
            try:
                content = self.load_custom_system_message(filename)
                if content:
                    # Create display name from filename
                    display_name = filename.replace('.txt', '').replace('systemmessage', '')
                    if display_name.startswith('_'):
                        display_name = display_name[1:]  # Remove leading underscore
                    if not display_name:
                        display_name = "Default"
                    
                    file_info.append({
                        'filename': filename,
                        'display_name': display_name.title(),
                        'preview': content[:100] + "..." if len(content) > 100 else content,
                        'length': len(content),
                        'is_current': filename == self.current_message_file
                    })
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        
        return file_info
    
    def set_current_system_message_file(self, filename: str) -> bool:
        """
        Set the current system message file to use.
        
        Args:
            filename: Name of the system message file to use
            
        Returns:
            True if file exists and was set successfully, False otherwise
        """
        if filename and os.path.exists(filename):
            content = self.load_custom_system_message(filename)
            if content:
                self.current_message_file = filename
                # Save the current system prompt to environment variables
                try:
                    env_manager.update_single_var('CURRENT_SYSTEM_PROMPT', filename)
                except Exception as e:
                    print(f"Warning: Could not save current system prompt to .env: {e}")
                return True
        return False
    
    def get_current_system_message_file(self) -> str:
        """
        Get the currently active system message filename.
        
        Returns:
            Current system message filename
        """
        return self.current_message_file
    
    def get_display_name_for_file(self, filename: str) -> str:
        """
        Get a user-friendly display name for a system message file.
        
        Args:
            filename: System message filename
            
        Returns:
            User-friendly display name
        """
        if not filename or filename == self.system_message_file:
            return "Default"
        
        display_name = filename.replace('.txt', '').replace('systemmessage', '')
        if display_name.startswith('_'):
            display_name = display_name[1:]
        
        return display_name.title() if display_name else "Default"
    
    def get_system_message_info(self) -> dict:
        """
        Get information about the current system message setup.
        
        Returns:
            Dictionary with system message info
        """
        custom_message = self.load_custom_system_message()
        
        return {
            'has_custom': custom_message is not None,
            'file_path': os.path.abspath(self.system_message_file),
            'file_exists': os.path.exists(self.system_message_file),
            'custom_message': custom_message,
            'default_message': self.default_system_message,
            'preview': (custom_message[:200] + "..." if custom_message and len(custom_message) > 200 
                       else custom_message) if custom_message else None
        }
    
    def create_example_system_message(self) -> str:
        """
        Create an example system message file content.
        
        Returns:
            Example system message content
        """
        return """You are an expert code reviewer and software architect with deep knowledge of multiple programming languages and best practices.

When analyzing code, please:
1. Focus on code quality, security, and performance
2. Suggest improvements and optimizations
3. Explain complex concepts clearly
4. Provide specific examples when helpful
5. Consider maintainability and readability

The user has provided the following codebase for analysis:

{codebase_content}

Please provide thoughtful, detailed responses that help improve the code and the developer's understanding."""

# Global instance
system_message_manager = SystemMessageManager()