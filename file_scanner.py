"""
File scanning utilities for the Code Chat application.
"""
import os
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv

class CodebaseScanner:
    """Handles scanning and reading of codebase files."""
    
    def __init__(self):
        self.supported_extensions = ['.py']
        self.special_files = ['.env']
        
        # Load ignore folders from environment
        load_dotenv()
        ignore_folders_env = os.getenv("IGNORE_FOLDERS", "venv,.venv,env,__pycache__")
        self.ignore_folders = [folder.strip() for folder in ignore_folders_env.split(",") if folder.strip()]
    
    def scan_directory(self, directory: str) -> List[str]:
        """
        Scan directory for supported files, excluding configured ignore folders.
        
        Args:
            directory: Path to the directory to scan
            
        Returns:
            List of file paths found in the directory
        """
        if not directory:
            raise Exception("Error scanning directory: No directory specified")
        
        if not os.path.exists(directory):
            raise Exception(f"Error scanning directory: Directory does not exist: {directory}")
            
        files = []
        
        try:
            # Scan for files with supported extensions
            for root, dirs, filenames in os.walk(directory):
                # Skip any directory that matches ignore folders
                if any(part in self.ignore_folders for part in Path(root).parts):
                    continue
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    
                    # Check for supported extensions
                    if any(filename.endswith(ext) for ext in self.supported_extensions):
                        files.append(file_path)
                    
                    # Check for special files
                    elif filename in self.special_files:
                        files.append(file_path)
            
            return sorted(files)
            
        except Exception as e:
            raise Exception(f"Error scanning directory: {str(e)}")
    
    def get_relative_paths(self, files: List[str], base_directory: str) -> List[str]:
        """
        Convert absolute file paths to relative paths.
        
        Args:
            files: List of absolute file paths
            base_directory: Base directory for relative path calculation
            
        Returns:
            List of relative file paths
        """
        relative_paths = []
        for file_path in files:
            try:
                relative_path = os.path.relpath(file_path, base_directory)
                relative_paths.append(relative_path)
            except ValueError:
                # If relative path can't be calculated, use filename
                relative_paths.append(os.path.basename(file_path))
        return relative_paths
    
    def read_file_content(self, file_path: str) -> str:
        """
        Read content of a single file.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def get_codebase_content(self, files: List[str]) -> str:
        """
        Read and combine content from multiple files.
        
        Args:
            files: List of file paths to read
            
        Returns:
            Combined content from all files with file separators
        """
        # Exclude files in any ignored folder
        files = [f for f in files if not any(part in self.ignore_folders for part in Path(f).parts)]
        content = ""
        
        for file_path in files:
            filename = os.path.basename(file_path)
            file_content = self.read_file_content(file_path)
            
            content += f"\n\n=== File: {filename} ===\n"
            content += file_content
        
        return content
    
    def validate_directory(self, directory: str) -> Tuple[bool, str]:
        """
        Validate if directory exists and is accessible.
        
        Args:
            directory: Directory path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not directory:
            return False, "No directory specified"
        
        if not os.path.exists(directory):
            return False, f"Directory does not exist: {directory}"
        
        if not os.path.isdir(directory):
            return False, f"Path is not a directory: {directory}"
        
        if not os.access(directory, os.R_OK):
            return False, f"Directory is not readable: {directory}"
        
        return True, ""