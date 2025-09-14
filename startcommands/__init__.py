"""
Start Commands Module for Code Chat AI

This module provides a unified interface to launch different components
of the Code Chat AI application with clear categorization and descriptions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger

# Module metadata
__version__ = "1.0.0"
__author__ = "Code Chat AI Team"

# Initialize logger for the startcommands module
logger = get_logger(__name__)

# Log module initialization
logger.info("Start Commands module initialized")
logger.debug(f"Module version: {__version__}, Author: {__author__}")