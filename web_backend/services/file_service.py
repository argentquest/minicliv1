"""File scanning utilities for the web backend."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from common.lazy_file_scanner import LazyCodebaseScanner, FileInfo
from common.logger import get_logger

logger = get_logger(__name__)


class FileService:
    """Wraps the existing scanners to expose REST-friendly helpers."""

    def __init__(self) -> None:
        logger.info("Initializing FileService")
        self._scanner = LazyCodebaseScanner()
        logger.info("FileService initialized with scanner")

    # ------------------------------------------------------------------
    # Directory helpers
    # ------------------------------------------------------------------
    def validate_directory(self, directory: str) -> Dict[str, Any]:
        is_valid, error_message = self._scanner.validate_directory(directory)
        return {
            "is_valid": is_valid,
            "error": error_message,
        }

    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Return metadata for all supported files under a directory."""
        logger.info(f"Scanning directory: {directory}")
        files: List[Dict[str, Any]] = []
        for batch in self._scanner.scan_directory_lazy(directory):
            for info in batch:
                files.append(self._serialize_file_info(info, directory))
        logger.info(f"Scan complete for {directory}: {len(files)} files")
        return files

    def build_directory_tree(self, directory: str) -> Dict[str, Any]:
        """Return a nested tree of directories and supported files."""
        root_path = Path(directory)
        tree = {
            "name": root_path.name,
            "path": str(root_path),
            "type": "directory",
            "children": [],
        }
        children_map: Dict[Path, Dict[str, Any]] = {root_path: tree}

        for batch in self._scanner.scan_directory_lazy(directory):
            for info in batch:
                file_path = Path(info.path)
                parent = file_path.parent
                node = self._ensure_directory(children_map, parent, root_path)
                node.setdefault("children", []).append(
                    {
                        "name": file_path.name,
                        "path": str(file_path),
                        "relativePath": os.path.relpath(info.path, directory),
                        "type": "file",
                        "size": info.size,
                        "modifiedTime": info.modified_time,
                        "extension": info.extension,
                        "isSpecial": info.is_special,
                    }
                )
        return tree

    # ------------------------------------------------------------------
    # File content helpers
    # ------------------------------------------------------------------
    def read_file(self, file_path: str) -> str:
        return self._scanner.read_file_content(file_path)

    def read_files(self, file_paths: Iterable[str]) -> str:
        return self._scanner.get_codebase_content(list(file_paths))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_directory(
        self,
        children_map: Dict[Path, Dict[str, Any]],
        directory: Path,
        root_path: Path,
    ) -> Dict[str, Any]:
        if directory in children_map:
            return children_map[directory]
        if directory == root_path:
            return children_map[root_path]

        parent_node = self._ensure_directory(
            children_map, directory.parent, root_path
        )
        node = {
            "name": directory.name,
            "path": str(directory),
            "type": "directory",
            "children": [],
        }
        parent_node.setdefault("children", []).append(node)
        children_map[directory] = node
        return node

    def _serialize_file_info(
        self, info: FileInfo, base_directory: str
    ) -> Dict[str, Any]:
        return {
            "path": info.path,
            "relativePath": os.path.relpath(info.path, base_directory),
            "size": info.size,
            "modifiedTime": info.modified_time,
            "extension": info.extension,
            "isSpecial": info.is_special,
        }

    def get_folder_file_counts(self, directory: str) -> List[Dict[str, Any]]:
        """Return recursive subfolders with file counts."""
        import os
        from pathlib import Path

        root = Path(directory).resolve()
        results = []
        for root_dir, dirs, files in os.walk(root):
            rel_path = os.path.relpath(root_dir, root)
            folder_path = "." if rel_path == "." else rel_path
            file_count = len(files)
            results.append({
                "path": folder_path,
                "fileCount": file_count
            })
        results.sort(key=lambda x: x["path"])
        return results


file_service = FileService()
