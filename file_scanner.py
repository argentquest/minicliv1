"""Compatibility exports for codebase scanners."""
from __future__ import annotations

from lazy_file_scanner import CodebaseScanner as _LazyWrapper, LazyCodebaseScanner

# Re-export the lazy scanner wrapper so legacy imports continue to work.
CodebaseScanner = _LazyWrapper

__all__ = ["CodebaseScanner", "LazyCodebaseScanner"]
