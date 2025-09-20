#!/usr/bin/env python3
"""
Modern Code Chat with AI - Primary Application Launcher

Delegates to minicli.launch_gui for the standard GUI experience.
"""

import sys

from minicli import launch_gui


def main() -> int:
    """Main entry point for the modern Code Chat GUI."""
    return launch_gui()


if __name__ == "__main__":
    sys.exit(main())
