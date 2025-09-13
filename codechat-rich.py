#!/usr/bin/env python3
"""
Code Chat Rich CLI - Enhanced Command Line Interface

This module provides a beautiful, interactive command-line interface for Code Chat AI
using the Rich library for enhanced terminal output, progress bars, and user experience.

Features:
- Beautiful terminal interface with colors and formatting
- Interactive prompts and guided workflows
- Progress bars for long-running operations
- Rich tables and layouts for data display
- Command history and auto-completion
- Comprehensive help system
- Configuration management with validation

Usage:
    python codechat-rich.py <command> [options]

Available commands:
    analyze     Analyze codebase with AI
    interactive Start interactive analysis mode
    config      Manage configuration settings
    models      List and test available AI models
    version     Show version information
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

# Rich imports for beautiful CLI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown

# Typer for CLI framework
import typer

# Local imports
from ai import create_ai_processor, AIProviderFactory
from file_scanner import CodebaseScanner
from lazy_file_scanner import LazyCodebaseScanner
from env_manager import EnvManager
from logger import get_logger

# Initialize Rich console
console = Console()
logger = get_logger(__name__)

# Initialize managers
env_manager = EnvManager()
ai_processor = None
scanner = None

# Typer app
app = typer.Typer(
    name="codechat-rich",
    help="🤖 Code Chat AI - Enhanced Rich CLI",
    add_completion=False,
    rich_markup_mode="rich"
)

def initialize_components():
    """Initialize AI processor and scanners."""
    global ai_processor, scanner

    try:
        # Initialize scanners
        scanner = CodebaseScanner()

        # Get API key from environment
        env_vars = env_manager.load_env_file()
        api_key = env_vars.get("API_KEY", "")
        provider = env_vars.get("DEFAULT_PROVIDER", "openrouter")

        if not api_key:
            console.print("[red]❌ No API_KEY found in environment variables[/red]")
            console.print("Please set your API key using: [cyan]python codechat-rich.py config --interactive[/cyan]")
            return False

        # Initialize AI processor
        ai_processor = create_ai_processor(api_key=api_key, provider=provider)
        return True

    except Exception as e:
        console.print(f"[red]❌ Failed to initialize components: {e}[/red]")
        return False

def create_header(title: str, subtitle: Optional[str] = None):
    """Create a beautiful header panel."""
    header_text = f"[bold blue]🤖 {title}[/bold blue]"
    if subtitle:
        header_text += f"\n[dim]{subtitle}[/dim]"

    panel = Panel(
        header_text,
        border_style="blue",
        padding=(1, 2)
    )
    return panel

def validate_directory(directory: str) -> bool:
    """Validate if directory exists and is accessible."""
    if not directory:
        console.print("[red]❌ No directory specified[/red]")
        return False

    if not os.path.exists(directory):
        console.print(f"[red]❌ Directory does not exist: {directory}[/red]")
        return False

    if not os.path.isdir(directory):
        console.print(f"[red]❌ Path is not a directory: {directory}[/red]")
        return False

    if not os.access(directory, os.R_OK):
        console.print(f"[red]❌ Directory is not readable: {directory}[/red]")
        return False

    return True

def analyze_codebase(
    directory: str,
    question: str,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    output: str = "structured"
):
    """Analyze codebase with AI using Rich progress indicators."""
    if not ai_processor or not scanner:
        console.print("[red]❌ Components not initialized[/red]")
        return

    # Validate directory
    if not validate_directory(directory):
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        # Step 1: Scanning directory
        scan_task = progress.add_task("🔍 Scanning directory...", total=100)

        try:
            files = scanner.scan_directory(directory)
            if not files:
                console.print("[red]❌ No supported files found in directory[/red]")
                return

            progress.update(scan_task, completed=50, description=f"📁 Found {len(files)} files")

            # Apply filters
            if include or exclude:
                filtered_files = []
                include_patterns = [p.strip() for p in include.split(',')] if include else []
                exclude_patterns = [p.strip() for p in exclude.split(',')] if exclude else []

                for file_path in files:
                    filename = os.path.basename(file_path)

                    # Check include patterns
                    if include_patterns:
                        if not any(pattern in filename for pattern in include_patterns):
                            continue

                    # Check exclude patterns
                    if exclude_patterns:
                        if any(pattern in filename for pattern in exclude_patterns):
                            continue

                    filtered_files.append(file_path)

                files = filtered_files
                progress.update(scan_task, completed=75, description=f"🎯 Filtered to {len(files)} files")

            progress.update(scan_task, completed=100, description=f"✅ Scanned {len(files)} files")

            # Step 2: Processing content
            process_task = progress.add_task("🧠 Processing codebase content...", total=100)

            codebase_content = scanner.get_codebase_content(files)
            progress.update(process_task, completed=100, description="✅ Content processed")

            # Step 3: AI Analysis
            analysis_task = progress.add_task("🤖 Analyzing with AI...", total=100)

            # Set model/provider if specified
            if provider and provider != ai_processor.provider:
                ai_processor.set_provider(provider)

            # Process question
            response = ai_processor.process_question(
                question=question,
                conversation_history=[],
                codebase_content=codebase_content,
                model=model or "gpt-3.5-turbo"
            )

            progress.update(analysis_task, completed=100, description="✅ Analysis complete")

        except Exception as e:
            console.print(f"[red]❌ Analysis failed: {e}[/red]")
            return

    # Display results
    console.print("\n" + "="*60)
    console.print("[bold green]🎉 Analysis Results[/bold green]")
    console.print("="*60)

    # Summary table
    summary_table = Table(title="📊 Analysis Summary")
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="magenta")

    summary_table.add_row("Files Processed", str(len(files)))
    summary_table.add_row("Model Used", model or "gpt-3.5-turbo")
    summary_table.add_row("Provider Used", ai_processor.provider)
    summary_table.add_row("Directory", directory)

    console.print(summary_table)
    console.print()

    # AI Response
    response_panel = Panel(
        response,
        title="💬 AI Response",
        border_style="green",
        padding=(1, 2)
    )
    console.print(response_panel)

@app.command()
def analyze(
    directory: str = typer.Argument(..., help="Path to the codebase directory"),
    question: str = typer.Argument(..., help="Question about the codebase"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    include: Optional[str] = typer.Option(None, "--include", "-i", help="File patterns to include (comma-separated)"),
    exclude: Optional[str] = typer.Option(None, "--exclude", "-e", help="File patterns to exclude (comma-separated)"),
    output: str = typer.Option("structured", "--output", "-o", help="Output format")
):
    """Analyze codebase with AI using Rich progress indicators."""
    console.print(create_header("Code Chat AI - Analysis", "Analyzing your codebase with AI"))

    if not initialize_components():
        return

    analyze_codebase(directory, question, model, provider, include, exclude, output)

@app.command()
def interactive():
    """Start interactive analysis mode with guided prompts."""
    console.print(create_header("Code Chat AI - Interactive Mode", "Guided codebase analysis"))

    if not initialize_components():
        return

    console.print("[bold cyan]Welcome to Interactive Analysis Mode![/bold cyan]")
    console.print("I'll guide you through analyzing your codebase step by step.\n")

    # Get directory
    directory = Prompt.ask("📁 Enter the path to your codebase directory")
    while not validate_directory(directory):
        directory = Prompt.ask("📁 Please enter a valid directory path")

    # Get question
    question = Prompt.ask("❓ What would you like to know about this codebase?")

    # Optional advanced options
    if Confirm.ask("🔧 Would you like to configure advanced options?", default=False):
        model = Prompt.ask("🤖 AI Model", default="gpt-3.5-turbo")
        provider = Prompt.ask("🏢 AI Provider", default="openrouter")
        include = Prompt.ask("✅ Include patterns (comma-separated)", default="")
        exclude = Prompt.ask("❌ Exclude patterns (comma-separated)", default="")
    else:
        model = provider = include = exclude = None

    console.print("\n[bold green]🚀 Starting analysis...[/bold green]\n")

    analyze_codebase(directory, question, model, provider, include, exclude)

@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    validate: bool = typer.Option(False, "--validate", help="Validate current configuration"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive configuration setup")
):
    """Manage configuration settings."""
    if show:
        console.print(create_header("Configuration Settings", "Current environment configuration"))

        env_vars = env_manager.load_env_file()

        table = Table(title="🔧 Current Configuration")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_column("Description", style="green")

        descriptions = env_manager.get_env_descriptions()

        for key, value in env_vars.items():
            if key == 'API_KEY' and value:
                # Mask API key
                value = value[:8] + '...' if len(value) > 8 else '***'
            description = descriptions.get(key, "")
            table.add_row(key, value or "[not set]", description)

        console.print(table)

    elif validate:
        console.print(create_header("Configuration Validation", "Checking your setup"))

        env_vars = env_manager.load_env_file()
        validation_results = env_manager.validate_all_env_vars(env_vars)

        table = Table(title="✅ Validation Results")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Message", style="yellow")

        all_valid = True
        for key, (is_valid, message) in validation_results.items():
            status = "✅ Valid" if is_valid else "❌ Invalid"
            table.add_row(key, status, message or "")
            if not is_valid:
                all_valid = False

        console.print(table)

        if all_valid:
            console.print("\n[bold green]🎉 All configuration settings are valid![/bold green]")
        else:
            console.print("\n[yellow]⚠️  Some configuration issues found. Run with --interactive to fix.[/yellow]")

    elif interactive:
        console.print(create_header("Interactive Configuration", "Set up your environment"))

        env_vars = env_manager.load_env_file()

        # API Key
        current_key = env_vars.get('API_KEY', '')
        if current_key:
            masked_key = current_key[:8] + '...' if len(current_key) > 8 else '***'
            console.print(f"Current API Key: [cyan]{masked_key}[/cyan]")

        if Confirm.ask("🔑 Set API Key?", default=not bool(current_key)):
            api_key = Prompt.ask("Enter your OpenRouter API key", password=True)
            env_vars['API_KEY'] = api_key

        # Default model
        current_model = env_vars.get('DEFAULT_MODEL', 'gpt-3.5-turbo')
        console.print(f"Current default model: [cyan]{current_model}[/cyan]")
        if Confirm.ask("🤖 Change default model?", default=False):
            model = Prompt.ask("Enter default model", default=current_model)
            env_vars['DEFAULT_MODEL'] = model

        # Save configuration
        if env_manager.save_env_file(env_vars):
            console.print("[bold green]✅ Configuration saved successfully![/bold green]")
        else:
            console.print("[red]❌ Failed to save configuration[/red]")

    else:
        console.print("[yellow]Use --show, --validate, or --interactive to manage configuration[/yellow]")

@app.command()
def models(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    test: Optional[str] = typer.Option(None, "--test", "-t", help="Test a specific model")
):
    """List and test available AI models."""
    console.print(create_header("AI Models", "Available models and providers"))

    if not initialize_components():
        return

    if test:
        console.print(f"[bold cyan]🧪 Testing model: {test}[/bold cyan]")

        try:
            # Simple test question
            test_question = "Hello, can you respond with a simple greeting?"
            response = ai_processor.process_question(
                question=test_question,
                conversation_history=[],
                codebase_content="",
                model=test
            )

            console.print("[green]✅ Model test successful![/green]")
            console.print(f"[bold]Response:[/bold] {response[:100]}...")

        except Exception as e:
            console.print(f"[red]❌ Model test failed: {e}[/red]")

    else:
        # List models
        try:
            providers = AIProviderFactory.get_available_providers()

            if provider and provider not in providers:
                console.print(f"[red]❌ Provider '{provider}' not found. Available: {', '.join(providers)}[/red]")
                return

            table = Table(title="🤖 Available AI Models")
            table.add_column("Provider", style="cyan", no_wrap=True)
            table.add_column("Models", style="magenta")

            for p in providers:
                if provider and p != provider:
                    continue

                try:
                    temp_processor = create_ai_processor(provider=p)
                    provider_info = temp_processor.get_provider_info()
                    models = provider_info.get('models', [])

                    if models:
                        table.add_row(p, ', '.join(models[:5]) + ('...' if len(models) > 5 else ''))
                    else:
                        table.add_row(p, "[dim]No models available[/dim]")

                except Exception as e:
                    table.add_row(p, f"[red]Error: {e}[/red]")

            console.print(table)

        except Exception as e:
            console.print(f"[red]❌ Failed to list models: {e}[/red]")

@app.command()
def version():
    """Show version information."""
    version_info = """
[bold blue]🤖 Code Chat AI - Rich CLI[/bold blue]
[dim]Enhanced command-line interface with Rich formatting[/dim]

[cyan]Version:[/cyan] 1.0.0
[cyan]Python:[/cyan] {}.{}.{}
[cyan]Platform:[/cyan] {}
    """.format(
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
        sys.platform
    )

    console.print(Panel(version_info, border_style="blue"))

if __name__ == "__main__":
    app()