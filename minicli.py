"""
Code Chat with AI - Modern Desktop Application

This module implements the main CLI application for Code Chat with AI,
a desktop application that enables users to chat with AI models about
their codebase. The application provides:

- Modern tabbed interface with conversation history management
- Advanced codebase scanning with lazy loading for large projects
- Support for multiple AI providers (OpenAI, Anthropic, etc.)
- Customizable system messages for different analysis types
- Secure API key management and environment configuration
- Theme support (light/dark) with modern UI components
- File selection and persistent context across conversation turns
- Conversation history save/load functionality

The application supports three modes:
- GUI mode (default): Full graphical interface
- CLI mode (--cli): Command-line interface for automation
- Rich CLI mode (--rich-cli): Enhanced CLI with progress bars

Architecture:
- Uses Tkinter for the GUI framework (GUI code moved to oldnicegui/)
- Implements MVC pattern with UIController managing interface components
- Supports both standard and lazy file scanning for performance optimization
- Threaded processing for non-blocking AI interactions
- Comprehensive error handling and user feedback
"""

import os
import sys

# Initialize logging first for proper error tracking
from common.logger import get_logger

# Import GUI functions from oldnicegui folder
from oldnicegui.main_gui_app import launch_gui


def main():
    """Main entry point - handles CLI, Rich CLI, GUI, and Server modes."""
    import sys

    # Check if server mode is requested
    if '--server' in sys.argv:
        try:
            # Remove --server from args and launch FastAPI server
            sys.argv.remove('--server')
            from fastapi_server import app
            import uvicorn
            import os

            # Get port from environment or command line
            port = 8000
            if '--port' in sys.argv:
                port_idx = sys.argv.index('--port')
                if port_idx + 1 < len(sys.argv):
                    port = int(sys.argv[port_idx + 1])
                    sys.argv.pop(port_idx + 1)
                    sys.argv.pop(port_idx)

            port = int(os.getenv("API_PORT", port))
            host = os.getenv("API_HOST", "0.0.0.0")

            print(f"Starting FastAPI server on {host}:{port}")
            print(f"API documentation available at: http://{host}:{port}/docs")

            uvicorn.run(
                "fastapi_server:app",
                host=host,
                port=port,
                reload=True,
                log_level="info"
            )
        except ImportError as e:
            print(f"ERROR: FastAPI server dependencies not available: {e}", file=sys.stderr)
            print("Please install: pip install fastapi uvicorn pydantic", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nServer stopped by user.", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: Server error: {str(e)}", file=sys.stderr)
            sys.exit(1)

    # Check if Rich CLI mode is requested
    elif '--rich-cli' in sys.argv:
        try:
            # Remove --rich-cli from args and launch Rich CLI
            sys.argv.remove('--rich-cli')
            from cli_rich import app
            app()
        except ImportError as e:
            print(f"ERROR: Rich CLI dependencies not available: {e}", file=sys.stderr)
            print("Please install: pip install rich typer", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Rich CLI error: {str(e)}", file=sys.stderr)
            sys.exit(1)
    # Check if standard CLI mode is requested
    elif '--cli' in sys.argv:
        # Standard CLI mode
        from cli_interface import CLIInterface

        cli = CLIInterface()
        parser = cli.setup_argument_parser()

        try:
            args = parser.parse_args()
            exit_code = cli.run_cli(args)
            sys.exit(exit_code)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Unexpected error: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        # Default to GUI mode
        try:
            exit_code = launch_gui()
            sys.exit(exit_code)
        except KeyboardInterrupt:
            print("\nApplication closed by user.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: GUI error: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()