#!/usr/bin/env python3
"""
Modern Code Chat with AI - Primary Application Launcher

Delegates to oldnicegui.main_gui_app.launch_gui for the standard GUI experience.
"""

import sys

from oldnicegui.main_gui_app import launch_gui


def main() -> int:
    """Main entry point for the modern Code Chat GUI."""
    return launch_gui()


if __name__ == "__main__":
    sys.exit(main())
