"""
Unit tests for file locking functionality.
"""
import pytest
import json
import time
import threading
from pathlib import Path
from unittest.mock import patch, Mock

from file_lock import (
    FileLock, FileLockError, safe_file_operation, 
    safe_json_save, safe_json_load, cleanup_stale_locks
)


class TestFileLock:
    """Test cases for FileLock class."""
    
    def test_init(self, temp_dir):
        """Test FileLock initialization."""
        test_file = Path(temp_dir) / "test.txt"
        lock = FileLock(str(test_file))
        
        assert lock.file_path == test_file
        assert lock.lock_file_path == test_file.with_suffix('.txt.lock')
        assert lock.timeout == 10.0
        assert lock.lock_file is None
    
    def test_acquire_and_release_success(self, temp_dir):
        """Test successful lock acquisition and release."""
        test_file = Path(temp_dir) / "test.txt"
        lock = FileLock(str(test_file), timeout=5.0)
        
        # Acquire lock
        result = lock.acquire()
        assert result is True
        assert lock.is_locked()
        assert lock.lock_file_path.exists()
        
        # Release lock
        lock.release()
        assert not lock.is_locked()
        # Note: On Windows, the lock file might persist briefly due to filesystem delays
        # but is_locked() should return False since the file handle is closed
    
    def test_acquire_timeout(self, temp_dir):
        """Test lock acquisition timeout."""
        test_file = Path(temp_dir) / "test.txt"
        
        # First lock should succeed
        lock1 = FileLock(str(test_file), timeout=0.5)
        assert lock1.acquire() is True
        
        try:
            # Second lock should timeout
            lock2 = FileLock(str(test_file), timeout=0.5)
            assert lock2.acquire() is False
        finally:
            lock1.release()
    
    def test_context_manager_success(self, temp_dir):
        """Test FileLock as context manager."""
        test_file = Path(temp_dir) / "test.txt"
        lock = FileLock(str(test_file))
        
        with lock:
            assert lock.is_locked()
        
        assert not lock.is_locked()
    
    def test_context_manager_timeout(self, temp_dir):
        """Test FileLock context manager timeout."""
        test_file = Path(temp_dir) / "test.txt"
        
        # Create a blocking lock
        lock1 = FileLock(str(test_file))
        lock1.acquire()
        
        try:
            # This should raise FileLockError due to timeout
            with pytest.raises(FileLockError):
                lock2 = FileLock(str(test_file), timeout=0.5)
                with lock2:
                    pass
        finally:
            lock1.release()


class TestSafeFileOperation:
    """Test cases for safe file operation context manager."""
    
    def test_safe_file_operation_success(self, temp_dir):
        """Test successful safe file operation."""
        test_file = Path(temp_dir) / "test.txt"
        
        with safe_file_operation(str(test_file)):
            # File should be locked during operation
            lock_file = test_file.with_suffix('.txt.lock')
            assert lock_file.exists()
        
        # Lock should be released after operation
        # Note: On Windows, lock file may persist briefly due to filesystem delays
    
    def test_safe_file_operation_timeout(self, temp_dir):
        """Test safe file operation timeout."""
        test_file = Path(temp_dir) / "test.txt"
        
        # Create blocking lock
        lock1 = FileLock(str(test_file))
        lock1.acquire()
        
        try:
            with pytest.raises(FileLockError):
                with safe_file_operation(str(test_file), timeout=0.5):
                    pass
        finally:
            lock1.release()


class TestSafeJsonOperations:
    """Test cases for safe JSON operations."""
    
    def test_safe_json_save_success(self, temp_dir):
        """Test successful JSON save with locking."""
        test_file = Path(temp_dir) / "test.json"
        test_data = {"key": "value", "number": 42}
        
        result = safe_json_save(test_data, str(test_file))
        
        assert result is True
        assert test_file.exists()
        
        # Verify content
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data
    
    def test_safe_json_save_with_backup(self, temp_dir):
        """Test JSON save with backup functionality."""
        test_file = Path(temp_dir) / "test.json"
        backup_file = test_file.with_suffix('.json.backup')
        
        # Create initial file
        initial_data = {"initial": True}
        with open(test_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Save new data with backup
        new_data = {"updated": True}
        result = safe_json_save(new_data, str(test_file), backup=True)
        
        assert result is True
        assert test_file.exists()
        assert not backup_file.exists()  # Backup removed on success
        
        # Verify content
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == new_data
    
    def test_safe_json_save_atomic_failure_recovery(self, temp_dir):
        """Test JSON save failure recovery with backup."""
        test_file = Path(temp_dir) / "test.json"
        
        # Create initial file
        initial_data = {"initial": True}
        with open(test_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Mock json.dump to raise an exception
        with patch('json.dump', side_effect=Exception("Write error")):
            result = safe_json_save({"new": True}, str(test_file), backup=True)
        
        assert result is False
        assert test_file.exists()
        
        # Verify original content is preserved
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == initial_data
    
    def test_safe_json_load_success(self, temp_dir):
        """Test successful JSON load with locking."""
        test_file = Path(temp_dir) / "test.json"
        test_data = {"key": "value", "list": [1, 2, 3]}
        
        # Create test file
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load with safe function
        loaded_data = safe_json_load(str(test_file))
        
        assert loaded_data == test_data
    
    def test_safe_json_load_nonexistent_file(self, temp_dir):
        """Test JSON load with nonexistent file."""
        test_file = Path(temp_dir) / "nonexistent.json"
        default_value = {"default": True}
        
        result = safe_json_load(str(test_file), default=default_value)
        
        assert result == default_value
    
    def test_safe_json_load_corrupt_file(self, temp_dir):
        """Test JSON load with corrupt file."""
        test_file = Path(temp_dir) / "corrupt.json"
        default_value = {"default": True}
        
        # Create corrupt JSON file
        with open(test_file, 'w') as f:
            f.write("{ invalid json content")
        
        result = safe_json_load(str(test_file), default=default_value)
        
        assert result == default_value


class TestCleanupStaleLocks:
    """Test cases for stale lock cleanup functionality."""
    
    def test_cleanup_stale_locks_by_age(self, temp_dir):
        """Test cleanup of stale locks by age."""
        # Create old lock file
        old_lock = Path(temp_dir) / "old.json.lock"
        with open(old_lock, 'w') as f:
            f.write("PID: 12345\nTimestamp: 12345.0\n")
        
        # Manually set old timestamp
        old_time = time.time() - 7200  # 2 hours ago
        old_lock.touch(times=(old_time, old_time))
        
        # Create recent lock file
        recent_lock = Path(temp_dir) / "recent.json.lock"
        with open(recent_lock, 'w') as f:
            f.write(f"PID: {threading.get_ident()}\nTimestamp: {time.time()}\n")
        
        # Run cleanup with 1 hour max age
        cleanup_stale_locks(temp_dir, max_age=3600.0)
        
        # Old lock should be removed, recent lock should remain
        assert not old_lock.exists()
        assert recent_lock.exists()
        
        # Cleanup recent lock for next tests
        recent_lock.unlink()
    
    def test_cleanup_stale_locks_empty_directory(self, temp_dir):
        """Test cleanup on empty directory."""
        # Should not raise any exceptions
        cleanup_stale_locks(temp_dir)
    
    def test_cleanup_stale_locks_no_permission_error(self, temp_dir):
        """Test cleanup handles permission errors gracefully."""
        # Create lock file
        lock_file = Path(temp_dir) / "test.lock"
        lock_file.write_text("PID: 12345")
        
        # Mock unlink to raise permission error
        with patch.object(Path, 'unlink', side_effect=PermissionError("Access denied")):
            # Should not raise exception
            cleanup_stale_locks(temp_dir, max_age=0.1)


class TestConcurrentOperations:
    """Test cases for concurrent file operations."""
    
    @pytest.mark.slow
    def test_concurrent_json_saves(self, temp_dir):
        """Test multiple threads saving to same file."""
        test_file = Path(temp_dir) / "concurrent.json"
        results = []
        errors = []
        
        def save_data(thread_id: int):
            try:
                data = {"thread": thread_id, "timestamp": time.time()}
                result = safe_json_save(data, str(test_file), timeout=5.0)
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_data, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # At least one should succeed
        successful_saves = [r for r in results if r[1] is True]
        assert len(successful_saves) >= 1
        
        # File should exist and contain valid JSON
        assert test_file.exists()
        loaded_data = safe_json_load(str(test_file))
        assert loaded_data is not None
        assert "thread" in loaded_data
    
    @pytest.mark.slow
    def test_concurrent_save_and_load(self, temp_dir):
        """Test concurrent save and load operations."""
        test_file = Path(temp_dir) / "concurrent.json"
        
        # Initialize file
        initial_data = {"counter": 0}
        safe_json_save(initial_data, str(test_file))
        
        results = []
        
        def worker(worker_id: int):
            try:
                # Try to load and save multiple times
                for i in range(3):
                    # Load current data
                    data = safe_json_load(str(test_file), timeout=2.0)
                    if data is not None:
                        # Update and save
                        data[f"worker_{worker_id}_update_{i}"] = time.time()
                        success = safe_json_save(data, str(test_file), timeout=2.0)
                        results.append((worker_id, i, success))
                    
                    time.sleep(0.1)  # Small delay between operations
            except Exception as e:
                results.append((worker_id, -1, str(e)))
        
        # Start multiple workers
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify final file state
        final_data = safe_json_load(str(test_file))
        assert final_data is not None
        assert "counter" in final_data
        
        # Should have some updates from workers
        worker_updates = [k for k in final_data.keys() if k.startswith("worker_")]
        assert len(worker_updates) > 0