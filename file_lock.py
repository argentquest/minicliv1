"""
File locking utilities for safe concurrent file operations.
Provides cross-platform file locking for conversation history persistence.
"""
import os
import time
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Any, Dict, List
try:
    import fcntl
except ImportError:
    fcntl = None
try:
    import msvcrt
except ImportError:
    msvcrt = None


class FileLockError(Exception):
    """Exception raised when file locking operations fail."""
    pass


class FileLock:
    """Cross-platform file locking implementation."""
    
    def __init__(self, file_path: str, timeout: float = 10.0):
        """
        Initialize file lock.
        
        Args:
            file_path: Path to the file to lock
            timeout: Maximum time to wait for lock acquisition
        """
        self.file_path = Path(file_path)
        self.lock_file_path = self.file_path.with_suffix(self.file_path.suffix + '.lock')
        self.timeout = timeout
        self.lock_file = None
    
    def acquire(self) -> bool:
        """
        Acquire the file lock.
        
        Returns:
            True if lock was acquired, False if timeout occurred
        """
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                # Create lock file with exclusive access
                if os.name == 'nt' and msvcrt:
                    # Windows implementation
                    self.lock_file = open(self.lock_file_path, 'w')
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                elif fcntl:
                    # Unix/Linux implementation
                    self.lock_file = open(self.lock_file_path, 'w')
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    # Fallback: basic file-based locking
                    self.lock_file = open(self.lock_file_path, 'w')
                
                # Write process info to lock file
                self.lock_file.write(f"PID: {os.getpid()}\nTimestamp: {time.time()}\n")
                self.lock_file.flush()
                return True
                
            except (IOError, OSError):
                # Lock file exists or is locked, wait and retry
                if self.lock_file:
                    self.lock_file.close()
                    self.lock_file = None
                time.sleep(0.1)
        
        return False
    
    def release(self):
        """Release the file lock."""
        if self.lock_file:
            try:
                if os.name == 'nt' and msvcrt:
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                elif fcntl:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                
                self.lock_file.close()
                self.lock_file = None  # Set to None before attempting file removal
                
                # Small delay for Windows file system to release handle
                if os.name == 'nt':
                    time.sleep(0.01)
                
                # Remove lock file with retry for Windows
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        if self.lock_file_path.exists():
                            self.lock_file_path.unlink()
                            break
                    except (IOError, OSError, PermissionError) as e:
                        if attempt == max_retries - 1:
                            # Last attempt failed, but we've already closed the file handle
                            # so consider the lock released
                            pass
                        else:
                            time.sleep(0.01)  # Brief retry delay
                    
            except (IOError, OSError):
                # If we can't remove the file, still mark as unlocked
                # The lock file might have been removed by another process or we don't have permission
                if self.lock_file:
                    self.lock_file.close()
                    self.lock_file = None
    
    def is_locked(self) -> bool:
        """Check if the file is currently locked."""
        return self.lock_file is not None and self.lock_file_path.exists()
    
    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise FileLockError(f"Failed to acquire lock for {self.file_path} within {self.timeout} seconds")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


@contextmanager
def safe_file_operation(file_path: str, timeout: float = 10.0):
    """
    Context manager for safe file operations with locking.
    
    Args:
        file_path: Path to the file to lock
        timeout: Maximum time to wait for lock acquisition
        
    Yields:
        FileLock instance
    """
    lock = FileLock(file_path, timeout)
    try:
        with lock:
            yield lock
    except FileLockError:
        raise
    except Exception as e:
        raise FileLockError(f"File operation failed: {str(e)}")


def safe_json_save(data: Any, file_path: str, timeout: float = 10.0, 
                   backup: bool = True) -> bool:
    """
    Safely save data to JSON file with file locking and backup.
    
    Args:
        data: Data to save as JSON
        file_path: Path to save the file
        timeout: Lock acquisition timeout
        backup: Whether to create backup before overwriting
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path = Path(file_path)
        
        # Create backup if requested and file exists
        backup_path = None
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            backup_path.write_bytes(file_path.read_bytes())
        
        with safe_file_operation(str(file_path), timeout):
            # Write to temporary file first, then rename for atomic operation
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Atomic rename on most platforms
                if os.name == 'nt':
                    # Windows doesn't support atomic rename over existing files
                    if file_path.exists():
                        file_path.unlink()
                    temp_path.rename(file_path)
                else:
                    temp_path.rename(file_path)
                
                # Remove backup if save was successful
                if backup_path and backup_path.exists():
                    backup_path.unlink()
                
                return True
                
            except Exception as e:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                
                # Restore backup if available
                if backup_path and backup_path.exists():
                    if file_path.exists():
                        file_path.unlink()
                    backup_path.rename(file_path)
                
                raise e
        
    except Exception:
        return False


def safe_json_load(file_path: str, timeout: float = 10.0, 
                   default: Optional[Any] = None) -> Any:
    """
    Safely load data from JSON file with file locking.
    
    Args:
        file_path: Path to load the file from
        timeout: Lock acquisition timeout
        default: Default value to return if file doesn't exist or loading fails
        
    Returns:
        Loaded data or default value
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return default
        
        with safe_file_operation(str(file_path), timeout):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
    except Exception:
        return default


def cleanup_stale_locks(directory: str, max_age: float = 3600.0):
    """
    Clean up stale lock files older than max_age seconds.
    
    Args:
        directory: Directory to scan for lock files
        max_age: Maximum age in seconds before considering a lock stale
    """
    try:
        directory = Path(directory)
        current_time = time.time()
        
        for lock_file in directory.glob('*.lock'):
            try:
                # Check lock file age
                file_age = current_time - lock_file.stat().st_mtime
                
                if file_age > max_age:
                    # Try to read PID from lock file
                    try:
                        with open(lock_file, 'r') as f:
                            content = f.read()
                        
                        # Extract PID if available
                        pid = None
                        for line in content.split('\n'):
                            if line.startswith('PID:'):
                                pid = int(line.split(':')[1].strip())
                                break
                        
                        # Check if process is still running
                        if pid:
                            try:
                                os.kill(pid, 0)  # Signal 0 checks if process exists
                                continue  # Process is still running, don't remove lock
                            except (OSError, ProcessLookupError):
                                pass  # Process is dead, safe to remove lock
                    
                    except (IOError, ValueError):
                        pass  # Can't read lock file, assume it's stale
                    
                    # Remove stale lock file
                    lock_file.unlink()
                    
            except (OSError, IOError):
                continue  # Skip files we can't access
    
    except Exception:
        pass  # Don't let cleanup errors affect main application