#!/usr/bin/env python3
"""
Simple script to run the FastAPI server for Code Chat AI.

Usage:
    python run_server.py [--port PORT] [--host HOST]

Environment variables:
    API_PORT: Port to run the server on (default: 8000)
    API_HOST: Host to bind to (default: 0.0.0.0)
"""

import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run FastAPI server for Code Chat AI")
    parser.add_argument("--port", type=int, default=8000, help="Port to run server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")

    args = parser.parse_args()

    # Set environment variables
    os.environ["API_PORT"] = str(args.port)
    os.environ["API_HOST"] = args.host

    # Import and run the server
    try:
        from fastapi_server import app
        import uvicorn

        print(f"Starting Code Chat AI FastAPI server on {args.host}:{args.port}")
        print(f"API documentation: http://{args.host}:{args.port}/docs")
        print(f"Alternative docs: http://{args.host}:{args.port}/redoc")

        uvicorn.run(
            "fastapi_server:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info"
        )

    except ImportError as e:
        print(f"ERROR: Missing dependencies: {e}")
        print("Please install required packages:")
        print("pip install fastapi uvicorn pydantic")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()