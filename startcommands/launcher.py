"""
Interactive launcher for Code Chat AI startup commands.

This module provides an interactive command-line interface that allows users
to browse and select from all available startup commands with clear categorization
and detailed descriptions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.columns import Columns
from rich.layout import Layout
from rich.align import Align
from rich.rule import Rule
from rich.status import Status
import subprocess

from .commands import command_registry, StartupCommand

# Initialize logger for launcher module
logger = get_logger(__name__)


class CommandLauncher:
    """Interactive launcher for startup commands."""

    def __init__(self):
        self.console = Console()
        self.selected_category: Optional[str] = None

    def print_welcome(self):
        """Print welcome banner."""
        welcome_text = Text("🚀 Code Chat AI - Startup Command Launcher", style="bold blue")
        subtitle = Text("Choose how you want to start the application", style="dim")

        panel = Panel.fit(
            Align.center(f"{welcome_text}\n{subtitle}"),
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()

    def show_categories(self) -> List[str]:
        """Show available categories and return them."""
        categories = command_registry.get_all_categories()

        table = Table(title="📂 Available Categories", box=None)
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Commands", style="green", justify="right")
        table.add_column("Description", style="dim")

        category_descriptions = {
            "GUI Applications": "Desktop graphical interfaces",
            "Web Applications": "Browser-based web interfaces",
            "CLI Applications": "Command-line interfaces",
            "Server Components": "Backend servers and APIs",
            "Development & Testing": "Testing and development tools",
            "Legacy & Special": "Legacy versions and special launchers"
        }

        for category in categories:
            commands = command_registry.get_commands_by_category(category)
            count = len(commands)
            description = category_descriptions.get(category, "Various startup options")
            table.add_row(category, str(count), description)

        self.console.print(table)
        self.console.print()
        return categories

    def show_category_commands(self, category: str):
        """Show all commands in a specific category."""
        commands = command_registry.get_commands_by_category(category)

        if not commands:
            self.console.print(f"[red]No commands found in category: {category}[/red]")
            return

        # Category header
        self.console.print(Rule(f"📋 {category}", style="blue"))
        self.console.print()

        # Commands table
        table = Table(box=None, show_header=False)
        table.add_column("ID", style="dim", width=3)
        table.add_column("Icon", width=3)
        table.add_column("Command", style="bold cyan")
        table.add_column("Status", style="green", width=15)
        table.add_column("Description", style="white")

        for i, cmd in enumerate(commands, 1):
            status = cmd.get_status()
            table.add_row(
                str(i),
                cmd.icon,
                cmd.name,
                status,
                cmd.description
            )

        self.console.print(table)
        self.console.print()

    def select_category(self, categories: List[str]) -> Optional[str]:
        """Let user select a category."""
        if len(categories) == 1:
            return categories[0]

        self.console.print("[yellow]Select a category by number:[/yellow]")

        for i, category in enumerate(categories, 1):
            self.console.print(f"  {i}. {category}")

        self.console.print()

        while True:
            try:
                choice = IntPrompt.ask("Enter category number", default=1)
                if 1 <= choice <= len(categories):
                    return categories[choice - 1]
                else:
                    self.console.print(f"[red]Please enter a number between 1 and {len(categories)}[/red]")
            except (ValueError, KeyboardInterrupt):
                self.console.print("[red]Invalid input. Please enter a number.[/red]")

    def select_command(self, commands: List[StartupCommand]) -> Optional[StartupCommand]:
        """Let user select a command from the list."""
        if len(commands) == 1:
            return commands[0]

        self.console.print("[yellow]Select a command by number:[/yellow]")

        for i, cmd in enumerate(commands, 1):
            status = cmd.get_status()
            self.console.print(f"  {i}. {cmd.icon} {cmd.name}")
            self.console.print(f"     {status}")
            self.console.print(f"     {cmd.description}")
            self.console.print()

        while True:
            try:
                choice = IntPrompt.ask("Enter command number", default=1)
                if 1 <= choice <= len(commands):
                    return commands[choice - 1]
                else:
                    self.console.print(f"[red]Please enter a number between 1 and {len(commands)}[/red]")
            except (ValueError, KeyboardInterrupt):
                self.console.print("[red]Invalid input. Please enter a number.[/red]")

    def execute_command(self, command: StartupCommand) -> bool:
        """Execute the selected command."""
        self.console.print(Rule(f"🚀 Executing: {command.name}", style="green"))
        self.console.print(f"[dim]Command: {' '.join(command.get_full_command())}[/dim]")
        self.console.print()

        # Check if command can run
        if not command.can_run():
            self.console.print("[red]❌ Cannot execute command - requirements not met[/red]")
            if command.requires_env:
                self.console.print("[yellow]💡 This command requires environment setup. Run 'python -m startcommands setup' first.[/yellow]")
            return False

        # Special handling for server components
        if command.category == "Server Components":
            return self._execute_server_command(command)
        elif command.category == "Web Applications":
            return self._execute_web_command(command)
        else:
            return self._execute_standard_command(command)

    def _execute_server_command(self, command: StartupCommand) -> bool:
        """Execute server-based commands with special handling."""
        self.console.print("[blue]🔧 Server Command Detected[/blue]")
        self.console.print("[dim]Server will run in background. Use Ctrl+C in server terminal to stop.[/dim]")
        self.console.print()

        # Confirm execution for servers
        if not Confirm.ask(f"Start server '{command.name}'? (runs in background)", default=True):
            self.console.print("[yellow]❌ Server start cancelled by user[/yellow]")
            return False

        try:
            # Execute server command in background
            with Status(f"[cyan]Starting server {command.name}...[/cyan]", spinner="dots") as status:
                process = subprocess.Popen(
                    command.get_full_command(),
                    cwd=os.getcwd(),
                    env=os.environ.copy(),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )

                # Give server more time to start (increased from 2 to 5 seconds)
                import time
                time.sleep(5)

                # Check if process is still running
                if process.poll() is None:
                    self.console.print("[green]✅ Server started successfully in background[/green]")
                    self.console.print(f"[dim]Process ID: {process.pid}[/dim]")
                    self.console.print("[yellow]💡 Server is running. You can now use other commands or exit the launcher.[/yellow]")
                    self.console.print("[yellow]💡 To stop the server, find the process and terminate it manually.[/yellow]")
                    return True
                else:
                    # Process terminated early - check for errors
                    return_code = process.returncode
                    self.console.print(f"[red]❌ Server failed to start (exit code: {return_code})[/red]")
                    self.console.print("[yellow]💡 Try running the server directly to see error messages[/yellow]")
                    return False

        except FileNotFoundError:
            self.console.print(f"[red]❌ Server command file not found: {command.command}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Error starting server: {str(e)}[/red]")
            return False

    def _execute_web_command(self, command: StartupCommand) -> bool:
        """Execute web application commands."""
        self.console.print("[blue]🌐 Web Application Command Detected[/blue]")

        # Check if this is a full web app or component
        if "frontend" in command.id.lower() and "backend" not in command.id.lower():
            self.console.print("[yellow]⚠️  This is frontend-only. Make sure backend is running separately.[/yellow]")
        elif "backend" in command.id.lower() and "frontend" not in command.id.lower():
            self.console.print("[yellow]⚠️  This is backend-only. Frontend will need to connect separately.[/yellow]")
        else:
            self.console.print("[green]✅ Full web application (frontend + backend)[/green]")

        self.console.print()

        # Confirm execution
        if not Confirm.ask(f"Start web application '{command.name}'?", default=True):
            self.console.print("[yellow]❌ Web application start cancelled by user[/yellow]")
            return False

        try:
            # Execute web command
            with Status(f"[cyan]Starting web application {command.name}...[/cyan]", spinner="dots") as status:
                process = subprocess.Popen(
                    command.get_full_command(),
                    cwd=os.getcwd(),
                    env=os.environ.copy(),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )

                # Give web app more time to start (increased from 3 to 5 seconds)
                import time
                time.sleep(5)

                # Check if process is still running
                if process.poll() is None:
                    self.console.print("[green]✅ Web application started successfully[/green]")
                    self.console.print(f"[dim]Process ID: {process.pid}[/dim]")

                    # Try to detect the URL
                    if "web_port" in os.environ:
                        port = os.environ.get("WEB_PORT", "8080")
                        self.console.print(f"[blue]🌐 Web interface should be available at: http://localhost:{port}[/blue]")
                    elif "api_port" in os.environ:
                        port = os.environ.get("API_PORT", "8000")
                        self.console.print(f"[blue]🔗 API should be available at: http://localhost:{port}[/blue]")
                    else:
                        # Default FastAPI port
                        self.console.print(f"[blue]🔗 API should be available at: http://localhost:8000[/blue]")

                    return True
                else:
                    # Process terminated early
                    return_code = process.returncode
                    self.console.print(f"[red]❌ Web application failed to start (exit code: {return_code})[/red]")
                    self.console.print("[yellow]💡 Try running the application directly to see error messages[/yellow]")
                    return False

        except FileNotFoundError:
            self.console.print(f"[red]❌ Web application file not found: {command.command}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Error starting web application: {str(e)}[/red]")
            return False

    def _execute_standard_command(self, command: StartupCommand) -> bool:
        """Execute standard commands (GUI, CLI, etc.)."""
        # Confirm execution
        if not Confirm.ask(f"Execute '{command.name}'?", default=True):
            self.console.print("[yellow]❌ Execution cancelled by user[/yellow]")
            return False

        try:
            # Execute the command
            with Status(f"[cyan]Starting {command.name}...[/cyan]", spinner="dots") as status:
                process = subprocess.Popen(
                    command.get_full_command(),
                    cwd=os.getcwd(),
                    env=os.environ.copy()
                )

                # For GUI applications and interactive CLI applications, don't wait
                if command.category == "GUI Applications" or command.interactive:
                    if command.interactive:
                        self.console.print("[green]✅ Interactive CLI launched successfully[/green]")
                        self.console.print("[yellow]💡 You can now interact with the CLI. The launcher will continue in background.[/yellow]")
                        self.console.print("[dim]Press Ctrl+C in the CLI window to exit when done.[/dim]")
                    else:
                        self.console.print("[green]✅ GUI application launched in background[/green]")
                        self.console.print("[yellow]💡 GUI window should appear shortly. You can continue using the launcher.[/yellow]")
                    return True
                else:
                    # For other applications, wait for completion
                    return_code = process.wait()
                    if return_code == 0:
                        self.console.print("[green]✅ Command completed successfully[/green]")
                        return True
                    else:
                        self.console.print(f"[red]❌ Command failed with return code: {return_code}[/red]")
                        return False

        except FileNotFoundError:
            self.console.print(f"[red]❌ Command file not found: {command.command}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Error executing command: {str(e)}[/red]")
            return False

    def search_commands(self) -> Optional[StartupCommand]:
        """Search for commands by keyword."""
        query = Prompt.ask("[yellow]🔍 Enter search term[/yellow]")
        results = command_registry.search_commands(query)

        if not results:
            self.console.print(f"[red]❌ No commands found matching: '{query}'[/red]")
            return None

        self.console.print(f"[green]✅ Found {len(results)} matching commands:[/green]")
        self.console.print()

        return self.select_command(results)

    def show_help(self):
        """Show help information."""
        help_text = """
[bold blue]Code Chat AI - Startup Command Launcher[/bold blue]

[dim]This launcher helps you choose the right way to start the Code Chat AI application.[/dim]

[bold cyan]Available Actions:[/bold cyan]
• Browse by category - Select from organized command groups
• Search commands - Find specific commands by name or description
• Quick launch - Direct execution of common commands

[bold cyan]Command Categories:[/bold cyan]
• [green]GUI Applications[/green] - Desktop interfaces with full features
• [blue]Web Applications[/blue] - Browser-based interfaces
• [yellow]CLI Applications[/yellow] - Command-line tools for automation
• [magenta]Server Components[/magenta] - Backend services and APIs
• [red]Development & Testing[/red] - Testing and development utilities

[bold cyan]Usage Tips:[/bold cyan]
• Use ↑/↓ arrows to navigate options
• Press Enter to select default option
• Type 'q' or Ctrl+C to quit
• GUI applications launch in background
• CLI applications run in foreground

[dim]For more information, visit the project documentation.[/dim]
        """

        panel = Panel.fit(
            help_text.strip(),
            border_style="blue",
            padding=(1, 2),
            title="📖 Help"
        )
        self.console.print(panel)
        self.console.print()

    def run_interactive(self):
        """Run the interactive launcher."""
        self.print_welcome()

        while True:
            try:
                # Show main menu
                self.console.print("[bold cyan]🚀 Main Menu[/bold cyan]")
                self.console.print("1. 📂 Browse by category")
                self.console.print("2. 🔍 Search commands")
                self.console.print("3. 📖 Show help")
                self.console.print("4. 🚪 Exit launcher")
                self.console.print()

                choice = Prompt.ask(
                    "Select option",
                    choices=["1", "2", "3", "4", "q", "quit", "exit"],
                    default="1",
                    show_choices=False
                )

                if choice in ["4", "q", "quit", "exit"]:
                    # Quit
                    self.console.print("[yellow]👋 Goodbye! Thanks for using Code Chat AI![/yellow]")
                    break

                elif choice == "1":
                    # Browse by category
                    categories = self.show_categories()
                    selected_category = self.select_category(categories)

                    if selected_category:
                        self.show_category_commands(selected_category)
                        commands = command_registry.get_commands_by_category(selected_category)
                        selected_command = self.select_command(commands)

                        if selected_command:
                            success = self.execute_command(selected_command)
                            if success:
                                # For server/web apps, continue in launcher
                                if selected_command.category in ["Server Components", "Web Applications"]:
                                    self.console.print("[green]✅ Application is running in background[/green]")
                                    self.console.print("[dim]You can continue using the launcher or exit when done.[/dim]")
                                    self.console.print()
                                    continue
                                # For CLI apps, exit after completion (unless interactive)
                                elif selected_command.category == "CLI Applications":
                                    if selected_command.interactive:
                                        self.console.print("[green]✅ Interactive CLI launched successfully[/green]")
                                        self.console.print("[dim]You can continue using the launcher or exit when done.[/dim]")
                                        self.console.print()
                                        continue
                                    else:
                                        self.console.print("[green]✅ CLI application completed[/green]")
                                        break
                                # For GUI apps, continue (they run in background)
                                # Don't break - let user continue using launcher

                elif choice == "2":
                    # Search commands
                    selected_command = self.search_commands()
                    if selected_command:
                        success = self.execute_command(selected_command)
                        if success:
                            # Same logic as above for different command types
                            if selected_command.category in ["Server Components", "Web Applications"]:
                                self.console.print("[green]✅ Application is running in background[/green]")
                                self.console.print("[dim]You can continue using the launcher or exit when done.[/dim]")
                                self.console.print()
                                continue
                            elif selected_command.category == "CLI Applications":
                                if selected_command.interactive:
                                    self.console.print("[green]✅ Interactive CLI launched successfully[/green]")
                                    self.console.print("[dim]You can continue using the launcher or exit when done.[/dim]")
                                    self.console.print()
                                    continue
                                else:
                                    self.console.print("[green]✅ CLI application completed[/green]")
                                    break

                elif choice == "3":
                    # Show help
                    self.show_help()

            except KeyboardInterrupt:
                self.console.print("\n[yellow]👋 Goodbye! Thanks for using Code Chat AI![/yellow]")
                break
            except EOFError:
                # Handle Ctrl+D on Unix/Linux
                self.console.print("\n[yellow]👋 Goodbye! Thanks for using Code Chat AI![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {str(e)}[/red]")
                self.console.print("[yellow]Returning to main menu...[/yellow]")
                self.console.print()


def main():
    """Main entry point for the launcher."""
    launcher = CommandLauncher()
    launcher.run_interactive()


if __name__ == "__main__":
    main()