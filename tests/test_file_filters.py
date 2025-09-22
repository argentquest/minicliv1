"""Tests for the file filtering utilities."""
from common.file_filters import filter_files


class TestFilterFiles:
    """Validate include and exclude filtering behaviour."""

    def test_include_patterns_filter_by_glob(self):
        files = [
            "src/app.py",
            "src/module.js",
            "tests/test_app.py",
            "README.md",
        ]

        result = filter_files(files, include="*.py", exclude=None)

        assert set(result) == {"src/app.py", "tests/test_app.py"}

    def test_exclude_patterns_remove_matches(self):
        files = [
            "src/app.py",
            "src/module.py",
            "tests/test_app.py",
            "tests/test_module.py",
        ]

        result = filter_files(files, include=None, exclude="tests/*")

        assert result == ["src/app.py", "src/module.py"]

    def test_order_preserved_after_include_and_exclude(self):
        files = [
            "a.py",
            "b.py",
            "c.py",
        ]

        result = filter_files(files, include="*.py", exclude="b.py")

        assert result == ["a.py", "c.py"]
