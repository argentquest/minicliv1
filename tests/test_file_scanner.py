"""
Unit tests for the file_scanner module.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch

from file_scanner import CodebaseScanner


class TestCodebaseScanner:
    """Test cases for CodebaseScanner class."""
    
    def test_init_default_values(self):
        """Test scanner initialization with default values."""
        scanner = CodebaseScanner()
        assert '.py' in scanner.supported_extensions
        assert '.env' in scanner.special_files
        assert 'venv' in scanner.ignore_folders
        assert '__pycache__' in scanner.ignore_folders
    
    @patch.dict(os.environ, {'IGNORE_FOLDERS': 'node_modules,dist,build'})
    def test_init_custom_ignore_folders(self):
        """Test scanner initialization with custom ignore folders."""
        scanner = CodebaseScanner()
        assert 'node_modules' in scanner.ignore_folders
        assert 'dist' in scanner.ignore_folders
        assert 'build' in scanner.ignore_folders
    
    def test_validate_directory_valid(self, temp_dir):
        """Test directory validation with valid directory."""
        scanner = CodebaseScanner()
        is_valid, error_msg = scanner.validate_directory(temp_dir)
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_directory_empty_path(self):
        """Test directory validation with empty path."""
        scanner = CodebaseScanner()
        is_valid, error_msg = scanner.validate_directory("")
        assert is_valid is False
        assert "No directory specified" in error_msg
    
    def test_validate_directory_nonexistent(self):
        """Test directory validation with non-existent directory."""
        scanner = CodebaseScanner()
        is_valid, error_msg = scanner.validate_directory("/nonexistent/path")
        assert is_valid is False
        assert "Directory does not exist" in error_msg
    
    def test_validate_directory_file_instead_of_dir(self, temp_dir):
        """Test directory validation when path points to a file."""
        scanner = CodebaseScanner()
        file_path = Path(temp_dir) / "test_file.txt"
        file_path.write_text("test content")
        
        is_valid, error_msg = scanner.validate_directory(str(file_path))
        assert is_valid is False
        assert "Path is not a directory" in error_msg
    
    def test_scan_directory_empty_dir(self, temp_dir):
        """Test scanning an empty directory."""
        scanner = CodebaseScanner()
        files = scanner.scan_directory(temp_dir)
        assert files == []
    
    def test_scan_directory_with_python_files(self, sample_py_files, temp_dir):
        """Test scanning directory with Python files."""
        scanner = CodebaseScanner()
        files = scanner.scan_directory(temp_dir)
        
        # Should find Python files and .env file
        py_files = [f for f in files if f.endswith('.py')]
        env_files = [f for f in files if f.endswith('.env')]
        
        assert len(py_files) >= 2  # main.py and utils.py
        assert len(env_files) == 1  # .env file
        assert any('main.py' in f for f in py_files)
        assert any('utils.py' in f for f in py_files)
    
    def test_scan_directory_ignores_folders(self, temp_dir):
        """Test that scanner ignores specified folders."""
        scanner = CodebaseScanner()
        
        # Create files in ignored folders
        venv_dir = Path(temp_dir) / "venv" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "some_module.py").write_text("# Should be ignored")
        
        cache_dir = Path(temp_dir) / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "module.pyc").write_text("# Should be ignored")
        
        # Create regular file
        (Path(temp_dir) / "main.py").write_text("# Should be found")
        
        files = scanner.scan_directory(temp_dir)
        
        # Should not include files from ignored folders
        assert not any('venv' in f for f in files)
        assert not any('__pycache__' in f for f in files)
        assert any('main.py' in f for f in files)
    
    def test_scan_directory_nonexistent(self):
        """Test scanning non-existent directory."""
        scanner = CodebaseScanner()
        with pytest.raises(Exception) as exc_info:
            scanner.scan_directory("/nonexistent/path")
        assert "Error scanning directory" in str(exc_info.value)
    
    def test_get_relative_paths(self, temp_dir):
        """Test converting absolute paths to relative paths."""
        scanner = CodebaseScanner()
        
        # Create some test files
        file1 = Path(temp_dir) / "file1.py"
        file2 = Path(temp_dir) / "subdir" / "file2.py"
        file1.touch()
        file2.parent.mkdir()
        file2.touch()
        
        absolute_paths = [str(file1), str(file2)]
        relative_paths = scanner.get_relative_paths(absolute_paths, temp_dir)
        
        assert "file1.py" in relative_paths
        assert os.path.join("subdir", "file2.py") in relative_paths or "subdir/file2.py" in relative_paths
    
    def test_read_file_content_success(self, temp_dir):
        """Test reading file content successfully."""
        scanner = CodebaseScanner()
        test_file = Path(temp_dir) / "test.py"
        test_content = "# Test Python file\nprint('Hello, World!')"
        test_file.write_text(test_content)
        
        content = scanner.read_file_content(str(test_file))
        assert content == test_content
    
    def test_read_file_content_nonexistent(self):
        """Test reading non-existent file."""
        scanner = CodebaseScanner()
        content = scanner.read_file_content("/nonexistent/file.py")
        assert "Error reading file" in content
    
    def test_get_codebase_content(self, temp_dir):
        """Test combining content from multiple files."""
        scanner = CodebaseScanner()
        
        # Create test files
        file1 = Path(temp_dir) / "module1.py"
        file2 = Path(temp_dir) / "module2.py"
        
        content1 = "# Module 1\nclass Class1:\n    pass"
        content2 = "# Module 2\nclass Class2:\n    pass"
        
        file1.write_text(content1)
        file2.write_text(content2)
        
        files = [str(file1), str(file2)]
        combined_content = scanner.get_codebase_content(files)
        
        # Should contain file separators and content from both files
        assert "=== File: module1.py ===" in combined_content
        assert "=== File: module2.py ===" in combined_content
        assert "class Class1:" in combined_content
        assert "class Class2:" in combined_content
    
    def test_get_codebase_content_ignores_folders(self, temp_dir):
        """Test that get_codebase_content ignores files in ignored folders."""
        scanner = CodebaseScanner()
        
        # Create file in ignored folder
        venv_dir = Path(temp_dir) / "venv"
        venv_dir.mkdir()
        ignored_file = venv_dir / "ignored.py"
        ignored_file.write_text("# Should be ignored")
        
        # Create regular file
        regular_file = Path(temp_dir) / "regular.py"
        regular_file.write_text("# Should be included")
        
        files = [str(ignored_file), str(regular_file)]
        combined_content = scanner.get_codebase_content(files)
        
        # Should not contain content from ignored file
        assert "ignored.py" not in combined_content
        assert "regular.py" in combined_content
        assert "Should be included" in combined_content
    
    def test_get_codebase_content_empty_list(self):
        """Test get_codebase_content with empty file list."""
        scanner = CodebaseScanner()
        content = scanner.get_codebase_content([])
        assert content == ""
    
    @pytest.mark.parametrize("extension,should_find", [
        (".py", True),
        (".js", False),
        (".txt", False),
    ])
    def test_supported_extensions(self, temp_dir, extension, should_find):
        """Test that scanner only finds supported extensions."""
        scanner = CodebaseScanner()
        
        test_file = Path(temp_dir) / f"test{extension}"
        test_file.write_text("test content")
        
        files = scanner.scan_directory(temp_dir)
        
        if should_find:
            assert any(f.endswith(extension) for f in files)
        else:
            assert not any(f.endswith(extension) for f in files)
    
    def test_special_files(self, temp_dir):
        """Test that scanner finds special files by exact name."""
        scanner = CodebaseScanner()
        
        # Create .env file (exact name match)
        env_file = Path(temp_dir) / ".env"
        env_file.write_text("API_KEY=test")
        
        files = scanner.scan_directory(temp_dir)
        
        assert any(f.endswith(".env") for f in files)
        assert ".env" in [Path(f).name for f in files]