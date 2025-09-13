#!/usr/bin/env python3
"""
FastAPI Integration Test Runner

This script provides an easy way to run integration tests for the FastAPI server.
It includes both unit-style tests with mocked dependencies and real server tests.

Usage:
    python run_fastapi_tests.py                # Run all tests
    python run_fastapi_tests.py --unit-only    # Run only mocked unit tests
    python run_fastapi_tests.py --real-server  # Test against running server
    python run_fastapi_tests.py --help         # Show help
"""

import argparse
import sys
import os
from pathlib import Path

def run_unit_tests():
    """Run unit tests with mocked dependencies."""
    print("🧪 Running FastAPI Integration Tests (Mocked)")
    print("=" * 50)

    # Import and run pytest programmatically
    import pytest
    import subprocess

    try:
        # Run pytest on the test file
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "test_fastapi_integration.py",
            "-v",
            "--tb=short"
        ], capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_real_server_tests():
    """Run tests against a real running FastAPI server."""
    print("🌐 Testing Real FastAPI Server")
    print("=" * 50)
    print("Note: Make sure the FastAPI server is running on http://localhost:8000")
    print("Start it with: python fastapi_server.py")
    print()

    # Import the real server test function
    from test_fastapi_integration import test_with_real_server

    try:
        test_with_real_server()
        return True
    except Exception as e:
        print(f"❌ Error testing real server: {e}")
        return False

def show_test_summary():
    """Show a summary of available tests."""
    print("📋 FastAPI Integration Test Suite")
    print("=" * 50)
    print()
    print("Available Tests:")
    print("  🧪 Unit Tests (Mocked)")
    print("    - Health endpoint")
    print("    - POST /analyze with JSON body")
    print("    - GET /analyze with query parameters")
    print("    - Parameter validation")
    print("    - Error handling")
    print("    - File filtering")
    print("    - File saving")
    print()
    print("  🌐 Real Server Tests")
    print("    - Health check")
    print("    - Models endpoint")
    print("    - Providers endpoint")
    print("    - Basic analysis request")
    print()
    print("Test Files:")
    print("  - test_fastapi_integration.py (main test suite)")
    print("  - run_fastapi_tests.py (this runner)")
    print()
    print("Usage Examples:")
    print("  python run_fastapi_tests.py")
    print("  python run_fastapi_tests.py --unit-only")
    print("  python run_fastapi_tests.py --real-server")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FastAPI Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_fastapi_tests.py                # Run all tests
  python run_fastapi_tests.py --unit-only    # Run only mocked unit tests
  python run_fastapi_tests.py --real-server  # Test against running server
  python run_fastapi_tests.py --summary      # Show test summary
        """
    )

    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="Run only unit tests with mocked dependencies"
    )

    parser.add_argument(
        "--real-server",
        action="store_true",
        help="Test against a real running FastAPI server"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show test summary and exit"
    )

    args = parser.parse_args()

    # Show summary if requested
    if args.summary:
        show_test_summary()
        return

    # Determine what tests to run
    run_unit = not args.real_server  # Run unit tests by default unless real-server only
    run_real = args.real_server

    if args.unit_only:
        run_real = False

    success = True

    # Run unit tests
    if run_unit:
        if not run_unit_tests():
            success = False
        print()

    # Run real server tests
    if run_real:
        if not run_real_server_tests():
            success = False

    # Final result
    print()
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()