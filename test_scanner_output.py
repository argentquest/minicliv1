import os
from common.lazy_file_scanner import LazyCodebaseScanner

def main():
    scanner = LazyCodebaseScanner()
    directory = "."
    
    # Validate directory
    is_valid, error = scanner.validate_directory(directory)
    if not is_valid:
        print(f"Invalid directory: {error}")
        return
    
    # Scan for files
    files = scanner.scan_directory(directory)
    
    # Get relative paths
    relative_paths = scanner.get_relative_paths(files, directory)
    
    print(f"Scanning directory: {os.path.abspath(directory)}")
    print(f"Total files found: {len(relative_paths)}")
    print("\nFiles (relative paths):")
    for path in sorted(relative_paths):
        print(f"  - {path}")
    
    # Check for common exclusions
    excluded_indicators = [".env", ".gitignore", ".mypy_cache", ".claude", ".github", "__pycache__"]
    excluded_count = sum(1 for p in relative_paths if any(ind in p for ind in excluded_indicators))
    print(f"\nExcluded files count (should be 0): {excluded_count}")
    if excluded_count == 0:
        print("✓ All exclusions working correctly")
    else:
        print("⚠ Some excluded files found")

if __name__ == "__main__":
    main()