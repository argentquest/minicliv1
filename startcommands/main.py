"""
Main entry point for the Start Commands launcher.

This module provides the command-line interface for launching the interactive
startup command selector.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger
import argparse
from .launcher import CommandLauncher
from .commands import command_registry

# Initialize logger for main module
logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for the launcher."""
    parser = argparse.ArgumentParser(
        description="Code Chat AI - Startup Command Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m startcommands              # Interactive launcher
  python -m startcommands --list       # List all commands
  python -m startcommands --run main_gui  # Run specific command
  python -m startcommands --category "GUI Applications"  # Show category
        """
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available commands'
    )

    parser.add_argument(
        '--category', '-c',
        type=str,
        help='Show commands in specific category'
    )

    parser.add_argument(
        '--run', '-r',
        type=str,
        help='Run specific command by ID'
    )

    parser.add_argument(
        '--search', '-s',
        type=str,
        help='Search commands by keyword'
    )

    return parser


def list_all_commands():
    """List all available commands."""
    console = CommandLauncher().console

    console.print("[bold blue]🚀 Code Chat AI - All Available Commands[/bold blue]")
    console.print()

    for category in command_registry.get_all_categories():
        console.print(f"[bold cyan]{category}:[/bold cyan]")
        commands = command_registry.get_commands_by_category(category)

        for cmd in commands:
            status = cmd.get_status()
            console.print(f"  {cmd.icon} [green]{cmd.id}[/green] - {cmd.name}")
            console.print(f"    {status}")
            console.print(f"    {cmd.description}")
            console.print()

        console.print()


def show_category_commands(category: str):
    """Show commands in a specific category."""
    launcher = CommandLauncher()
    launcher.show_category_commands(category)


def run_specific_command(command_id: str):
    """Run a specific command by ID."""
    console = CommandLauncher().console
    command = command_registry.get_command(command_id)

    if not command:
        console.print(f"[red]❌ Command not found: {command_id}[/red]")
        console.print("[yellow]Use --list to see all available commands[/yellow]")
        return False

    launcher = CommandLauncher()
    return launcher.execute_command(command)


def search_commands(query: str):
    """Search commands by keyword."""
    console = CommandLauncher().console
    results = command_registry.search_commands(query)

    if not results:
        console.print(f"[red]❌ No commands found matching: '{query}'[/red]")
        return

    console.print(f"[green]✅ Found {len(results)} matching commands:[/green]")
    console.print()

    for cmd in results:
        status = cmd.get_status()
        console.print(f"  {cmd.icon} [green]{cmd.id}[/green] - {cmd.name}")
        console.print(f"    {status}")
        console.print(f"    {cmd.description}")
        console.print()


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle different modes
    if args.list:
        list_all_commands()
    elif args.category:
        show_category_commands(args.category)
    elif args.run:
        success = run_specific_command(args.run)
        sys.exit(0 if success else 1)
    elif args.search:
        search_commands(args.search)
    else:
        # Default: interactive mode
        launcher = CommandLauncher()
        launcher.run_interactive()


if __name__ == "__main__":
    main()