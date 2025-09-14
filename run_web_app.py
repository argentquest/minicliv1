#!/usr/bin/env python3
"""
Web Application Launcher

This script provides an easy way to start the complete Code Chat AI
web application, which includes both the FastAPI backend server and
the NiceGUI frontend interface.

Usage:
    python run_web_app.py                    # Start both backend and frontend
    python run_web_app.py --backend-only     # Start only FastAPI backend
    python run_web_app.py --frontend-only    # Start only NiceGUI frontend
    python run_web_app.py --help            # Show help
"""

import argparse
import subprocess
import sys
import time


def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting FastAPI Backend Server")
    print("=" * 50)

    try:
        # Start fastapi_server.py
        backend_process = subprocess.Popen([
            sys.executable, "fastapi_server.py"
        ], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)

        print("✅ FastAPI backend started (PID: {})".format(
            backend_process.pid))
        print("📡 Backend will be available at: http://localhost:8000")
        print("📚 API documentation at: http://localhost:8000/docs")
        print()

        return backend_process

    except FileNotFoundError:
        print("❌ Error: fastapi_server.py not found!")
        print("Please ensure the FastAPI server file exists in the current "
              "directory.")
        return None
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None


def start_frontend():
    """Start the NiceGUI frontend interface."""
    print("💻 Starting NiceGUI Frontend Interface")
    print("=" * 50)

    try:
        # Start nicegui_frontend.py
        frontend_process = subprocess.Popen([
            sys.executable, "nicegui_frontend.py"
        ], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)

        print("✅ NiceGUI frontend started (PID: {})".format(
            frontend_process.pid))
        print("🌐 Frontend will be available at: http://localhost:8080")
        print()

        return frontend_process

    except FileNotFoundError:
        print("❌ Error: nicegui_frontend.py not found!")
        print("Please ensure the NiceGUI frontend file exists in the current "
              "directory.")
        return None
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None


def wait_for_servers(backend_process, frontend_process):
    """Wait for both servers to be ready."""
    print("⏳ Waiting for servers to initialize...")
    time.sleep(5)  # Give servers time to start

    # Check if processes are still running
    backend_running = (backend_process.poll() is None
                      if backend_process else False)
    frontend_running = (frontend_process.poll() is None
                       if frontend_process else False)

    if backend_running and frontend_running:
        print("🎉 Both servers are running successfully!")
        print()
        print("🌐 Access your Code Chat AI web application at:")
        print("   Frontend: http://localhost:8080")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print()
        print("Press Ctrl+C to stop both servers")
    elif backend_running:
        print("⚠️  Only backend is running. Frontend failed to start.")
    elif frontend_running:
        print("⚠️  Only frontend is running. Backend failed to start.")
    else:
        print("❌ Both servers failed to start!")
        return False

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Code Chat AI Web Application Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_web_app.py                    # Start complete web application
  python run_web_app.py --backend-only     # Start only FastAPI backend
  python run_web_app.py --frontend-only    # Start only NiceGUI frontend

The web application consists of:
- FastAPI Backend: Provides REST API for code analysis
- NiceGUI Frontend: Modern web interface for user interaction

Both servers will run in the background. Use Ctrl+C to stop them.
        """
    )

    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Start only the FastAPI backend server"
    )

    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Start only the NiceGUI frontend interface"
    )

    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for servers to initialize (useful for automation)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.backend_only and args.frontend_only:
        print("❌ Error: Cannot specify both --backend-only and "
              "--frontend-only")
        sys.exit(1)

    print("🤖 Code Chat AI - Web Application Launcher")
    print("=" * 50)
    print()

    backend_process = None
    frontend_process = None

    try:
        # Start backend if requested or both
        if not args.frontend_only:
            backend_process = start_backend()
            if backend_process is None:
                sys.exit(1)

        # Start frontend if requested or both
        if not args.backend_only:
            frontend_process = start_frontend()
            if frontend_process is None:
                sys.exit(1)

        # Wait for servers if both are running and not no-wait
        if not args.no_wait and backend_process and frontend_process:
            if not wait_for_servers(backend_process, frontend_process):
                sys.exit(1)

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
                # Check if any process has died
                if backend_process and backend_process.poll() is not None:
                    print("❌ Backend server has stopped unexpectedly!")
                    break
                if frontend_process and frontend_process.poll() is not None:
                    print("❌ Frontend server has stopped unexpectedly!")
                    break
        except KeyboardInterrupt:
            print()
            print("🛑 Shutting down servers...")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

    finally:
        # Clean up processes
        if backend_process:
            print("Stopping backend server...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()

        if frontend_process:
            print("Stopping frontend server...")
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()

        print("✅ All servers stopped.")


if __name__ == "__main__":
    main()