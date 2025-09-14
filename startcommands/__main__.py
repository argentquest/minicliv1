"""
Main entry point for running startcommands as a module.

This file allows the startcommands package to be executed with:
    python -m startcommands

It simply imports and runs the main function from main.py.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger
from .main import main

# Get logger from the startcommands module
logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Starting startcommands module execution")
    logger.debug("Calling main() function from startcommands.main")

    try:
        main()
        logger.info("Startcommands module execution completed successfully")
    except Exception as e:
        logger.error(f"Error during startcommands module execution: {e}")
        raise