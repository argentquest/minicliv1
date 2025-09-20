#!/usr/bin/env python3
"""
Enhanced UI Launcher - Forces Window Visibility

Delegates to minicli.launch_gui with visibility forcing enabled.
"""

import sys

from minicli import launch_gui


def main() -> int:
    """Launch the GUI with forced window visibility."""
    return launch_gui(force_visibility=True, verbose=True)


if __name__ == "__main__":
    sys.exit(main())
