"""
Unit tests for lazy file scanner functionality.
"""
import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from lazy_file_scanner import LazyCodebaseScanner, FileInfo, CodebaseScanner


class TestFileInfo:
    """Test cases for FileInfo dataclass."""
    
    def test_file_info_creation(self):
        """Test FileInfo object creation."""
        file_info = FileInfo(
            path="/test/file.py",
            relative_path="file.py",
            size=1024,
            modified_time=1234567890.0,
            extension=".py",
            is_special=False
        )
        
        assert file_info.path == "/test/file.py"
        assert file_info.relative_path == "file.py"
        assert file_info.size == 1024
        assert file_info.modified_time == 1234567890.0
        assert file_info.extension == ".py"
        assert file_info.is_special is False


class TestLazyCodebaseScanner:
    """Test cases for LazyCodebaseScanner class."""
    
    def test_init(self):
        """Test LazyCodebaseScanner initialization."""
        scanner = LazyCodebaseScanner(cache_size=50, max_file_size=512*1024)
        
        assert scanner.cache_size == 50
        assert scanner.max_file_size == 512*1024
        assert len(scanner._content_cache) == 0
        assert len(scanner.supported_extensions) > 10
        assert '.py' in scanner.supported_extensions
        assert '.env' in scanner.special_files
    
    def test_is_supported_file(self):
        """Test file support detection."""
        scanner = LazyCodebaseScanner()
        
        assert scanner._is_supported_file("main.py")
        assert scanner._is_supported_file("script.js")
        assert scanner._is_supported_file("component.tsx")
        assert scanner._is_supported_file(".env")
        assert scanner._is_supported_file("requirements.txt")
        
        assert not scanner._is_supported_file("image.png")
        assert not scanner._is_supported_file("video.mp4")
        assert not scanner._is_supported_file("binary.exe")
    
    def test_should_skip_directory(self):
        """Test directory skipping logic."""
        scanner = LazyCodebaseScanner()
        # Ensure we have the expected ignore folders for testing
        scanner.ignore_folders = {"venv", ".venv", "env", "__pycache__", "node_modules", "dist", "build", ".git"}
        
        assert scanner._should_skip_directory("/project/node_modules")
        assert scanner._should_skip_directory("/project/__pycache__")
        assert scanner._should_skip_directory("/project/.git")
        assert scanner._should_skip_directory("/project/venv")
        
        assert not scanner._should_skip_directory("/project/src")
        assert not scanner._should_skip_directory("/project/lib")
        assert not scanner._should_skip_directory("/project/tests")
    
    def test_file_content_lazy_caching(self, temp_dir):
        """Test lazy file content loading with caching."""
        scanner = LazyCodebaseScanner(cache_size=5)
        
        # Create test file
        test_file = Path(temp_dir) / "test.py"
        content = "print('Hello, World!')"
        test_file.write_text(content)
        
        # First read should cache the content
        result1 = scanner.get_file_content_lazy(str(test_file))
        assert result1 == content
        assert str(test_file) in scanner._content_cache
        assert scanner.stats['cache_misses'] == 1
        
        # Second read should hit cache
        result2 = scanner.get_file_content_lazy(str(test_file))
        assert result2 == content
        assert scanner.stats['cache_hits'] == 1
    
    def test_file_content_cache_invalidation(self, temp_dir):
        """Test cache invalidation when file changes."""
        scanner = LazyCodebaseScanner()
        
        # Create and cache file
        test_file = Path(temp_dir) / "test.py"
        original_content = "original content"
        test_file.write_text(original_content)
        
        result1 = scanner.get_file_content_lazy(str(test_file))
        assert result1 == original_content
        
        # Wait a bit and modify file
        time.sleep(0.01)
        new_content = "modified content"
        test_file.write_text(new_content)
        
        # Should reload content
        result2 = scanner.get_file_content_lazy(str(test_file))
        assert result2 == new_content
    
    def test_file_content_size_limit(self, temp_dir):
        """Test file size limits for caching."""
        scanner = LazyCodebaseScanner(max_file_size=100)  # Very small limit
        
        # Create large file
        test_file = Path(temp_dir) / "large.py"
        large_content = "x" * 1000  # Larger than limit
        test_file.write_text(large_content)
        
        # Should read but not cache
        result = scanner.get_file_content_lazy(str(test_file))
        assert result == large_content
        assert str(test_file) not in scanner._content_cache
    
    def test_cache_lru_eviction(self, temp_dir):
        """Test LRU cache eviction."""
        scanner = LazyCodebaseScanner(cache_size=2)
        
        # Create multiple files
        files = []
        for i in range(3):
            test_file = Path(temp_dir) / f"test{i}.py"
            test_file.write_text(f"content {i}")
            files.append(str(test_file))
        
        # Load all files (should evict first one)
        for file_path in files:
            scanner.get_file_content_lazy(file_path)
        
        # First file should be evicted
        assert len(scanner._content_cache) == 2
        assert files[0] not in scanner._content_cache
        assert files[1] in scanner._content_cache
        assert files[2] in scanner._content_cache
    
    def test_scan_directory_lazy_empty_dir(self, temp_dir):
        """Test lazy scanning of empty directory."""
        scanner = LazyCodebaseScanner()
        
        batches = list(scanner.scan_directory_lazy(temp_dir))
        assert len(batches) == 0
    
    def test_scan_directory_lazy_with_files(self, temp_dir):
        """Test lazy scanning with actual files."""
        scanner = LazyCodebaseScanner()
        
        # Create test files
        files_created = []
        for i in range(5):
            test_file = Path(temp_dir) / f"test{i}.py"
            test_file.write_text(f"# Test file {i}")
            files_created.append(test_file.name)
        
        # Scan directory
        all_file_infos = []
        for batch in scanner.scan_directory_lazy(temp_dir):
            all_file_infos.extend(batch)
        
        # Verify results
        found_files = [info.relative_path for info in all_file_infos]
        for created_file in files_created:
            assert created_file in found_files
    
    def test_scan_directory_lazy_with_progress(self, temp_dir):
        """Test lazy scanning with progress callback."""
        scanner = LazyCodebaseScanner()
        
        # Create test files
        for i in range(10):
            test_file = Path(temp_dir) / f"test{i}.py"
            test_file.write_text(f"# Test file {i}")
        
        # Track progress calls
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        # Scan with progress
        list(scanner.scan_directory_lazy(temp_dir, progress_callback))
        
        # Should have received progress updates
        assert len(progress_calls) > 0
        
        # Final call should have current == total
        final_call = progress_calls[-1]
        assert final_call[0] == final_call[1]
    
    def test_codebase_content_lazy_size_limit(self, temp_dir):
        """Test codebase content with size limits."""
        scanner = LazyCodebaseScanner()
        
        # Create files of different sizes
        small_file = Path(temp_dir) / "small.py"
        small_file.write_text("small content")
        
        large_file = Path(temp_dir) / "large.py"
        large_file.write_text("x" * 1000)  # Large content
        
        files = [str(small_file), str(large_file)]
        
        # Get content with small size limit
        content = scanner.get_codebase_content_lazy(files, max_total_size=500)
        
        # Should include small file but might skip large file
        assert "small content" in content
        assert "=== File: small.py ===" in content
    
    def test_get_directory_stats(self, temp_dir):
        """Test directory statistics collection."""
        scanner = LazyCodebaseScanner()
        
        # Create test files
        (Path(temp_dir) / "test.py").write_text("# Python file")
        (Path(temp_dir) / "script.js").write_text("// JavaScript file")
        (Path(temp_dir) / ".env").write_text("API_KEY=secret")
        
        stats = scanner.get_directory_stats(temp_dir)
        
        assert stats['total_files'] == 3
        assert '.py' in stats['file_types']
        assert '.js' in stats['file_types']
        assert len(stats['special_files']) >= 1
        assert '.env' in stats['special_files']
    
    def test_cache_stats(self):
        """Test cache statistics."""
        scanner = LazyCodebaseScanner()
        
        initial_stats = scanner.get_cache_stats()
        assert initial_stats['cache_size'] == 0
        assert initial_stats['cache_hit_rate'] == 0.0
        
        # Add some stats
        scanner.stats['cache_hits'] = 10
        scanner.stats['cache_misses'] = 5
        
        updated_stats = scanner.get_cache_stats()
        assert updated_stats['cache_hit_rate'] == pytest.approx(66.67, rel=1e-2)
    
    def test_clear_cache(self, temp_dir):
        """Test cache clearing."""
        scanner = LazyCodebaseScanner()
        
        # Create and cache a file
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("test content")
        scanner.get_file_content_lazy(str(test_file))
        
        assert len(scanner._content_cache) > 0
        
        # Clear cache
        scanner.clear_cache()
        
        assert len(scanner._content_cache) == 0
        assert len(scanner._cache_access_times) == 0


class TestCodebaseScannerWrapper:
    """Test cases for backwards compatibility wrapper."""
    
    def test_wrapper_initialization(self):
        """Test wrapper initialization."""
        scanner = CodebaseScanner()
        
        assert scanner.lazy_scanner is not None
        assert scanner.supported_extensions == ['.py']  # Original compatibility
        assert scanner.special_files == ['.env']
    
    def test_wrapper_scan_directory(self, temp_dir):
        """Test wrapper scan_directory method."""
        scanner = CodebaseScanner()
        
        # Create test files
        py_file = Path(temp_dir) / "test.py"
        py_file.write_text("# Python file")
        
        js_file = Path(temp_dir) / "test.js"  # Should be ignored in compatibility mode
        js_file.write_text("// JavaScript file")
        
        env_file = Path(temp_dir) / ".env"
        env_file.write_text("API_KEY=secret")
        
        # Scan directory
        files = scanner.scan_directory(temp_dir)
        
        # Should only include .py and .env files for compatibility
        file_names = [Path(f).name for f in files]
        assert "test.py" in file_names
        assert ".env" in file_names
        assert "test.js" not in file_names  # Filtered out for compatibility
    
    def test_wrapper_get_relative_paths(self, temp_dir):
        """Test wrapper get_relative_paths method."""
        scanner = CodebaseScanner()
        
        test_file = Path(temp_dir) / "subdir" / "test.py"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("# Test")
        
        files = [str(test_file)]
        relative_paths = scanner.get_relative_paths(files, temp_dir)
        
        assert len(relative_paths) == 1
        assert "subdir" in relative_paths[0]
        assert "test.py" in relative_paths[0]
    
    def test_wrapper_read_file_content(self, temp_dir):
        """Test wrapper read_file_content method."""
        scanner = CodebaseScanner()
        
        test_file = Path(temp_dir) / "test.py"
        content = "print('Hello, World!')"
        test_file.write_text(content)
        
        result = scanner.read_file_content(str(test_file))
        assert result == content
    
    def test_wrapper_get_codebase_content(self, temp_dir):
        """Test wrapper get_codebase_content method."""
        scanner = CodebaseScanner()
        
        # Create test files
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("# File 1")
        
        file2 = Path(temp_dir) / "file2.py"
        file2.write_text("# File 2")
        
        files = [str(file1), str(file2)]
        content = scanner.get_codebase_content(files)
        
        assert "=== File: file1.py ===" in content
        assert "=== File: file2.py ===" in content
        assert "# File 1" in content
        assert "# File 2" in content
    
    def test_wrapper_validate_directory(self, temp_dir):
        """Test wrapper validate_directory method."""
        scanner = CodebaseScanner()
        
        # Valid directory
        is_valid, error = scanner.validate_directory(temp_dir)
        assert is_valid is True
        assert error == ""
        
        # Invalid directory
        is_valid, error = scanner.validate_directory("/nonexistent/path")
        assert is_valid is False
        assert "does not exist" in error


class TestLazyScannerIntegration:
    """Integration tests for lazy scanner functionality."""
    
    @pytest.mark.slow
    def test_large_directory_handling(self, temp_dir):
        """Test handling of large directory structures."""
        scanner = LazyCodebaseScanner()
        
        # Create nested directory structure with many files
        for i in range(5):  # 5 subdirectories
            subdir = Path(temp_dir) / f"subdir{i}"
            subdir.mkdir()
            
            for j in range(10):  # 10 files per subdirectory
                test_file = subdir / f"file{j}.py"
                test_file.write_text(f"# File {i}-{j}\nprint('Hello from {i}-{j}')")
        
        # Scan directory lazily
        all_files = []
        for batch in scanner.scan_directory_lazy(temp_dir):
            all_files.extend(batch)
        
        # Should find all 50 files
        assert len(all_files) == 50
        
        # Verify file info structure
        for file_info in all_files[:5]:  # Check first 5
            assert file_info.path.endswith('.py')
            assert file_info.size > 0
            assert file_info.extension == '.py'
            assert not file_info.is_special
    
    @pytest.mark.slow
    def test_performance_comparison(self, temp_dir):
        """Test performance benefits of lazy loading."""
        # Create moderate number of files
        files_created = []
        for i in range(20):
            test_file = Path(temp_dir) / f"test{i}.py"
            content = f"# Test file {i}\n" + "x" * 1000  # Some content
            test_file.write_text(content)
            files_created.append(str(test_file))
        
        # Test lazy scanner
        lazy_scanner = LazyCodebaseScanner()
        
        start_time = time.time()
        lazy_files = []
        for batch in lazy_scanner.scan_directory_lazy(temp_dir):
            lazy_files.extend(batch)
        lazy_scan_time = time.time() - start_time
        
        # Test regular scanner
        regular_scanner = CodebaseScanner()
        
        start_time = time.time()
        regular_files = regular_scanner.scan_directory(temp_dir)
        regular_scan_time = time.time() - start_time
        
        # Both should find the same files (accounting for filtering)
        lazy_paths = [info.path for info in lazy_files]
        assert len(lazy_paths) == len(regular_files)
        
        # Performance metrics should be reasonable
        assert lazy_scan_time < 5.0  # Should complete within 5 seconds
        assert regular_scan_time < 5.0
    
    def test_memory_efficiency_with_caching(self, temp_dir):
        """Test memory efficiency with file caching."""
        scanner = LazyCodebaseScanner(cache_size=5, max_file_size=1000)
        
        # Create files of various sizes
        small_files = []
        for i in range(10):
            test_file = Path(temp_dir) / f"small{i}.py"
            test_file.write_text(f"# Small file {i}")
            small_files.append(str(test_file))
        
        # Load all files (should trigger cache eviction)
        for file_path in small_files:
            scanner.get_file_content_lazy(file_path)
        
        # Cache should not exceed the limit
        assert len(scanner._content_cache) <= 5
        
        # Cache statistics should be reasonable
        stats = scanner.get_cache_stats()
        assert stats['cache_size'] <= 5
        assert stats['files_cached'] > 0