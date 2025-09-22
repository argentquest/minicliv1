"""
Lazy-loading file scanner for optimized performance with large codebases.
Implements caching, progressive loading, and memory-efficient file handling.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Generator
from dataclasses import dataclass
from dotenv import load_dotenv
import hashlib
from .file_filters import _normalize_patterns, _matches_any
from common.logger import get_logger, log_performance


@dataclass
class FileInfo:
    """Information about a file for lazy loading."""

    path: str
    relative_path: str
    size: int
    modified_time: float
    extension: str
    is_special: bool = False


@dataclass
class FileContent:
    """Cached file content with metadata."""

    content: str
    hash: str
    timestamp: float
    size: int


class LazyCodebaseScanner:
    """
    Lazy-loading file scanner with caching and progressive loading for large
    codebases.

    Features:
    - Lazy file content loading (only read when requested)
    - LRU caching of file contents
    - Progressive directory scanning for UI responsiveness
    - File change detection and cache invalidation
    - Memory-efficient handling of large codebases
    """

    def __init__(
        self, cache_size: int = 100, max_file_size: int = 1024 * 1024  # 1MB limit
    ) -> None:
        """
        Initialize lazy scanner.

        Args:
            cache_size: Maximum number of files to cache in memory
            max_file_size: Maximum file size to cache (bytes)
        """
        self.logger = get_logger("lazy_scanner")
        self.logger.info(
            "Initializing LazyCodebaseScanner",
            cache_size=cache_size,
            max_file_size=max_file_size,
        )
        self.cache_size = cache_size
        self.max_file_size = max_file_size

        # File content cache
        self._content_cache: Dict[str, FileContent] = {}
        self._cache_access_times: Dict[str, float] = {}

        # File metadata cache
        self._file_info_cache: Dict[str, List[FileInfo]] = {}
        self._directory_scan_times: Dict[str, float] = {}

        # Configuration
        self.supported_extensions = [
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".cs",
            ".rb",
            ".php",
            ".go",
            ".rs",
            ".kt",
            ".scala",
            ".html",
            ".css",
            ".sql",
            ".yaml",
            ".yml",
            ".json",
            ".xml",
            ".md",
            ".txt",
            ".sh",
            ".bat",
            ".ps1",
        ]
        self.special_files = [
            ".env",
            ".gitignore",
            "requirements.txt",
            "package.json",
            "Dockerfile",
            "docker-compose.yml",
            "Makefile",
            "README.md",
        ]

        # Load ignore folders from environment
        load_dotenv()
        ignore_folders_env = os.getenv(
            "IGNORE_FOLDERS",
            "venv,.venv,env,__pycache__,node_modules,dist,build,.git,"
            + ".mypy_cache,.claude,.github,.vscode,.idea,.roo,results,logs,"
            + ".tox,.nox,.pytest_cache,htmlcov,cover",
        )
        self.ignore_folders = set(
            folder.strip()
            for folder in ignore_folders_env.split(",")
            if folder.strip()
        )

        # Add folders from .gitignore to ignore_folders
        gitignore_path = os.path.join(os.getcwd(), ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and line.endswith("/"):
                            folder_name = line.rstrip("/").split("/")[-1]
                            if folder_name:
                                self.ignore_folders.add(folder_name)
            except Exception as e:
                self.logger.warning(
                    "Failed to parse .gitignore for ignore_folders",
                    path=gitignore_path,
                    error=str(e),
                )
        
        self.hardcoded_excludes = ["jink"]

        self.logger.debug("Ignore folders set", folders=list(self.ignore_folders))


        # Statistics
        self.stats = {
            "files_scanned": 0,
            "files_cached": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_scan_time": 0.0,
            "total_read_time": 0.0,
        }
        self.logger.debug("LazyCodebaseScanner initialized with stats tracking")

    @log_performance()
    def scan_directory_lazy(
        self, directory: str, progress_callback=None
    ) -> Generator[List[FileInfo], None, None]:
        """
        Lazily scan directory and yield file information in batches.

        Args:
            directory: Directory to scan
            progress_callback: Optional callback for progress updates

        Yields:
            Batches of FileInfo objects
        """
        self.logger.info("Starting lazy directory scan", directory=directory)
        start_time = time.time()

        if not self._is_directory_valid(directory):
            self.logger.warning("Invalid directory for scanning", directory=directory)
            return

        # Load gitignore patterns for file exclusion
        gitignore_patterns = []
        gitignore_path = os.path.join(directory, ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                self.logger.debug("Loading .gitignore patterns", path=gitignore_path)
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    raw_patterns = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]
                    gitignore_patterns = _normalize_patterns(raw_patterns)
                    self.logger.debug(
                        f"Loaded {len(gitignore_patterns)} gitignore patterns"
                    )
            except Exception as e:
                self.logger.warning(
                    "Failed to load .gitignore", path=gitignore_path, error=str(e)
                )
                pass
        exclude_patterns = gitignore_patterns + self.hardcoded_excludes

        # Check if we have cached results that are still valid
        cached_info = self._get_cached_directory_info(directory)
        if cached_info:
            self.logger.info(
                "Using cached directory info",
                directory=directory,
                cached_files=len(cached_info),
            )
            # Yield cached results in batches
            batch_size = 50
            for i in range(0, len(cached_info), batch_size):
                batch = cached_info[i : i + batch_size]
                if progress_callback:
                    progress_callback(i + len(batch), len(cached_info))
                self.logger.debug("Yielding cached batch", batch_size=len(batch))
                yield batch
            self.logger.info("Completed cached scan yield", directory=directory)
            return

        # Perform fresh scan
        self.logger.info("Performing fresh directory scan", directory=directory)
        file_infos = []
        processed_files = 0

        try:

            # Second pass: collect file info
            self.logger.debug("Starting collection of file info", directory=directory)

            for root, dirs, filenames in os.walk(directory):
                # Skip ignored directories
                if self._should_skip_directory(root):
                    self.logger.debug("Skipping directory during scan", dir=root)
                    dirs.clear()  # Don't recurse into this directory
                    continue

                # Filter subdirectories based on .gitignore patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not _matches_any(gitignore_patterns, os.path.join(root, d))
                ]

                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    if not self._is_supported_file(filename):
                        continue

                    if _matches_any(exclude_patterns, full_path):
                        continue

                    file_path = full_path
                    try:
                        stat = os.stat(file_path)
                        if stat.st_size == 0:
                            continue
                        relative_path = os.path.relpath(file_path, directory)

                        file_info = FileInfo(
                            path=file_path,
                            relative_path=relative_path,
                            size=stat.st_size,
                            modified_time=stat.st_mtime,
                            extension=Path(filename).suffix.lower(),
                            is_special=filename in self.special_files,
                        )

                        file_infos.append(file_info)
                        processed_files += 1

                    except OSError:
                        continue  # Skip files we can't access

            # Cache the results
            self._cache_directory_info(directory, file_infos)
            self.logger.info(
                "Cached directory info",
                directory=directory,
                total_files=len(file_infos),
            )

        except Exception as e:
            self.logger.error(
                "Error during directory scan", directory=directory, error=str(e)
            )
            raise Exception(f"Error scanning directory: {str(e)}")
        finally:
            scan_time = time.time() - start_time
            self.stats["total_scan_time"] += scan_time
            self.stats["files_scanned"] += len(file_infos)
            self.logger.info(
                "Completed directory scan",
                directory=directory,
                files_scanned=len(file_infos),
                scan_time=scan_time,
            )

    @log_performance()
    def get_file_content_lazy(self, file_path: str, force_reload: bool = False) -> str:
        """
        Get file content with lazy loading and caching.

        Args:
            file_path: Path to the file
            force_reload: Force reload even if cached

        Returns:
            File content
        """
        self.logger.debug(
            "Getting file content",
            file=os.path.basename(file_path),
            force_reload=force_reload,
        )
        start_time = time.time()

        # Check cache first
        if not force_reload and file_path in self._content_cache:
            cached_content = self._content_cache[file_path]

            # Verify file hasn't changed
            try:
                current_mtime = os.path.getmtime(file_path)
                if current_mtime <= cached_content.timestamp:
                    self._cache_access_times[file_path] = time.time()
                    self.stats["cache_hits"] += 1
                    self.logger.debug(
                        "Cache hit for file", file=os.path.basename(file_path)
                    )
                    return cached_content.content
            except OSError:
                # File doesn't exist anymore, remove from cache
                self.logger.warning(
                    "Cached file no longer exists, removing from cache", file=file_path
                )
                self._remove_from_cache(file_path)

        # Load file content
        self.logger.debug("Cache miss, reading file", file=file_path)
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()

            # Calculate content hash
            content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

            # Cache if file is not too large
            file_size = len(content.encode("utf-8"))
            if file_size <= self.max_file_size:
                self.logger.debug(
                    "Caching file content",
                    file=os.path.basename(file_path),
                    size=file_size,
                )
                self._cache_file_content(file_path, content, content_hash, file_size)
            else:
                self.logger.debug(
                    "File too large to cache",
                    file=os.path.basename(file_path),
                    size=file_size,
                    max_size=self.max_file_size,
                )

            self.stats["cache_misses"] += 1
            self.logger.debug("File read completed", file=os.path.basename(file_path))
            return content

        except Exception as e:
            self.logger.error("Error reading file", file=file_path, error=str(e))
            return f"Error reading file {os.path.basename(file_path)}: {str(e)}"
        finally:
            read_time = time.time() - start_time
            self.stats["total_read_time"] += read_time

    @log_performance()
    def get_codebase_content_lazy(
        self, file_paths: List[str], max_total_size: int = 10 * 1024 * 1024
    ) -> str:
        """
        Get combined content from multiple files with size limits.

        Args:
            file_paths: List of file paths
            max_total_size: Maximum total content size (10MB default)

        Returns:
            Combined file content with separators
        """
        self.logger.info(
            "Getting codebase content from files",
            num_files=len(file_paths),
            max_size=max_total_size,
        )
        content_parts = []
        total_size = 0
        files_included = 0
        files_skipped = 0

        # Sort files by priority: special files first, then by size (smaller first)
        def file_priority(path: str) -> Tuple[int, int]:
            filename = os.path.basename(path)
            is_special = 1 if filename in self.special_files else 2
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            return (is_special, size)

        sorted_files = sorted(file_paths, key=file_priority)

        for file_path in sorted_files:
            # Check if adding this file would exceed size limit
            try:
                file_size = os.path.getsize(file_path)
                if total_size + file_size > max_total_size and files_included > 0:
                    self.logger.debug(
                        "Skipping file due to size limit",
                        file=os.path.basename(file_path),
                        current_size=total_size,
                        file_size=file_size,
                    )
                    files_skipped += 1
                    continue
            except OSError:
                self.logger.warning("Could not get file size, skipping", file=file_path)
                files_skipped += 1
                continue

            filename = os.path.basename(file_path)
            file_content = self.get_file_content_lazy(file_path)

            content_parts.append(f"\n\n=== File: {filename} ===")
            content_parts.append(file_content)

            total_size += len(file_content.encode("utf-8"))
            files_included += 1
            self.logger.debug(
                "Included file in codebase content",
                file=filename,
                size=len(file_content.encode("utf-8")),
            )

        # Add summary if files were skipped
        if files_skipped > 0:
            summary = f"\n\n=== Summary ===\nIncluded {files_included} files, skipped {files_skipped} files due to size limits."
            content_parts.append(summary)

        return "\n".join(content_parts)

    def get_directory_stats(self, directory: str) -> Dict:
        """Get statistics about a directory without loading all content."""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "file_types": {},
            "largest_files": [],
            "special_files": [],
        }

        try:
            for file_batch in self.scan_directory_lazy(directory):
                for file_info in file_batch:
                    stats["total_files"] += 1
                    stats["total_size"] += file_info.size

                    # Count by extension
                    ext = file_info.extension or "no extension"
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

                    # Track special files
                    if file_info.is_special:
                        stats["special_files"].append(file_info.relative_path)

                    # Track largest files (keep top 10)
                    stats["largest_files"].append(
                        (file_info.relative_path, file_info.size)
                    )
                    stats["largest_files"].sort(key=lambda x: x[1], reverse=True)
                    if len(stats["largest_files"]) > 10:
                        stats["largest_files"] = stats["largest_files"][:10]

        except Exception:
            pass  # Return partial stats on error

        return stats

    def clear_cache(self):
        """Clear all caches."""
        self._content_cache.clear()
        self._cache_access_times.clear()
        self._file_info_cache.clear()
        self._directory_scan_times.clear()
        self.stats["files_cached"] = 0

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            **self.stats,
            "cache_size": len(self._content_cache),
            "max_cache_size": self.cache_size,
            "cache_hit_rate": (
                self.stats["cache_hits"]
                / max(1, self.stats["cache_hits"] + self.stats["cache_misses"])
            )
            * 100,
        }

    def scan_directory(self, directory: str) -> List[str]:
        """Scan directory and return file paths (compatibility method)."""
        file_paths: List[str] = []
        try:
            for file_batch in self.scan_directory_lazy(directory):
                for file_info in file_batch:
                    file_paths.append(file_info.path)
        except Exception:
            pass
        return sorted(file_paths)

    def get_relative_paths(self, files: List[str], base_directory: str) -> List[str]:
        """Convert absolute paths to relative paths."""
        relative_paths = []
        for file_path in files:
            try:
                relative_path = os.path.relpath(file_path, base_directory)
                relative_paths.append(relative_path)
            except ValueError:
                relative_paths.append(os.path.basename(file_path))
        return relative_paths

    def read_file_content(self, file_path: str) -> str:
        """Read file content (alias for compatibility)."""
        return self.get_file_content_lazy(file_path)

    def get_codebase_content(self, files: List[str]) -> str:
        """Get combined codebase content (alias for compatibility)."""
        # Filter out ignored folders
        filtered_files = [
            file_path
            for file_path in files
            if not self._should_skip_directory(os.path.dirname(file_path))
        ]
        return self.get_codebase_content_lazy(filtered_files)

    def validate_directory(self, directory: str) -> Tuple[bool, str]:
        """Validate directory (compatibility method)."""
        if not directory:
            return False, "No directory specified"

        if not os.path.exists(directory):
            return False, f"Directory does not exist: {directory}"

        if not os.path.isdir(directory):
            return False, f"Path is not a directory: {directory}"

        if not os.access(directory, os.R_OK):
            return False, f"Directory is not readable: {directory}"

        return True, ""

    def _is_directory_valid(self, directory: str) -> bool:
        """Check if directory is valid and accessible."""
        return (
            directory
            and os.path.exists(directory)
            and os.path.isdir(directory)
            and os.access(directory, os.R_OK)
        )

    def _should_skip_directory(self, directory_path: str) -> bool:
        """Check if directory should be skipped based on ignore folders."""
        path_parts = set(Path(directory_path).parts)
        return bool(path_parts.intersection(self.ignore_folders))

    def _is_supported_file(self, filename: str) -> bool:
        """Check if file is supported."""
        return (
            any(filename.endswith(ext) for ext in self.supported_extensions)
            or filename in self.special_files
        )

    def _get_cached_directory_info(self, directory: str) -> Optional[List[FileInfo]]:
        """Get cached directory info if still valid."""
        if directory not in self._file_info_cache:
            return None

        # Check if cache is too old (5 minutes)
        if directory in self._directory_scan_times:
            age = time.time() - self._directory_scan_times[directory]
            if age > 300:  # 5 minutes
                del self._file_info_cache[directory]
                del self._directory_scan_times[directory]
                return None

        return self._file_info_cache[directory]

    def _cache_directory_info(self, directory: str, file_infos: List[FileInfo]):
        """Cache directory scan results."""
        self._file_info_cache[directory] = file_infos
        self._directory_scan_times[directory] = time.time()

    def _cache_file_content(
        self, file_path: str, content: str, content_hash: str, size: int
    ):
        """Cache file content with LRU eviction."""
        # Remove oldest entries if cache is full
        while len(self._content_cache) >= self.cache_size:
            oldest_file = min(
                self._cache_access_times.keys(),
                key=lambda k: self._cache_access_times[k],
            )
            self._remove_from_cache(oldest_file)

        # Add to cache
        self._content_cache[file_path] = FileContent(
            content=content, hash=content_hash, timestamp=time.time(), size=size
        )
        self._cache_access_times[file_path] = time.time()
        self.stats["files_cached"] += 1

    def _remove_from_cache(self, file_path: str):
        """Remove file from cache."""
        if file_path in self._content_cache:
            del self._content_cache[file_path]
        if file_path in self._cache_access_times:
            del self._cache_access_times[file_path]
