"""Utility helpers for applying include/exclude file pattern filters."""
from __future__ import annotations

import os
from fnmatch import fnmatch
from typing import Iterable, List, Optional, Sequence, Union

PatternInput = Optional[Union[str, Sequence[str]]]


def _normalize_patterns(patterns: PatternInput) -> List[str]:
    """Convert a pattern specification into a clean list of glob patterns."""
    if not patterns:
        return []

    if isinstance(patterns, str):
        raw_patterns = patterns.split(',')
    else:
        raw_patterns = patterns

    normalized: List[str] = []
    for pattern in raw_patterns:
        if pattern is None:
            continue
        trimmed = pattern.strip()
        if trimmed:
            normalized.append(trimmed)
    return normalized


def _matches_any(patterns: Sequence[str], file_path: str) -> bool:
    """Check whether a path matches any pattern (full path or basename)."""
    if not patterns:
        return False

    filename = os.path.basename(file_path)
    return any(
        fnmatch(filename, pattern) or fnmatch(file_path, pattern)
        for pattern in patterns
    )


def filter_files(
    files: Iterable[str],
    include: PatternInput = None,
    exclude: PatternInput = None,
) -> List[str]:
    """Apply include/exclude glob filters to a list of file paths."""
    files_list = list(files)
    include_patterns = _normalize_patterns(include)
    exclude_patterns = _normalize_patterns(exclude)

    filtered = files_list

    if include_patterns:
        included: List[str] = []
        for pattern in include_patterns:
            for file_path in files_list:
                if _matches_any([pattern], file_path):
                    included.append(file_path)
        # Preserve first-seen order while removing duplicates
        seen = dict.fromkeys(included)
        filtered = list(seen.keys())

    if exclude_patterns:
        filtered = [
            file_path for file_path in filtered
            if not _matches_any(exclude_patterns, file_path)
        ]

    return filtered

