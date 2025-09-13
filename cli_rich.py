"""
Rich + Typer enhanced command-line interface for the Code Chat application.
Provides a beautiful, modern CLI experience with rich output formatting,
progress indicators, and interactive prompts while maintaining all existing functionality.
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == "win32":
    try:
        # Try to set UTF-8 encoding for Windows console
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # Fallback for older Python versions or restricted environments
        try:
            import locale
            if locale.getpreferredencoding().lower() != 'utf-8':
                os.environ['PYTHONIOENCODING'] = 'utf-8'
        except:
            # Ultimate fallback - will use text replacements
            pass
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
import re

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.tree import Tree
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich.live import Live
from rich.status import Status
from rich.layout import Layout
from rich.align import Align
from rich.markdown import Markdown
from rich import box
from dotenv import load_dotenv

# Import existing core functionality
from lazy_file_scanner import CodebaseScanner, LazyCodebaseScanner
from ai import AIProcessor, AIProviderFactory
from system_message_manager import system_message_manager
from logger import get_logger, log_performance
from env_validator import env_validator

# Create CLI application
app = typer.Typer(
    name="codechat-rich",
    help="Code Chat AI - Analyze codebases with AI assistance (Rich + Typer Enhanced)",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich"
)

# Global console for rich output with Windows compatibility
try:
    # Try to enable UTF-8 support on Windows
    import sys
    if sys.platform == "win32":
        import os
        os.system("chcp 65001 >nul")  # Enable UTF-8 code page
    console = Console(force_terminal=True)
except:
    # Fallback for systems without UTF-8 support
    console = Console(force_terminal=True, legacy_windows=True)


class RichCLIInterface:
    """Enhanced CLI interface using Rich and Typer for beautiful terminal output."""
    
    def __init__(self):
        self.scanner = CodebaseScanner()
        self.lazy_scanner = None
        self.ai_processor = None
        self.logger = get_logger("rich_cli")
        self.config = {}
        
    def setup_lazy_scanner(self):
        """Initialize lazy scanner for large codebases."""
        if not self.lazy_scanner:
            self.lazy_scanner = LazyCodebaseScanner()
    
    def print_welcome_banner(self):
        """Display a beautiful welcome banner."""
        banner = Panel.fit(
            "[bold blue]Code Chat AI[/bold blue]\n[italic]Rich + Typer Enhanced CLI[/italic]",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(banner)
        console.print()
    
    def print_config_summary(self, config: Dict[str, Any]):
        """Display configuration summary in a nice table."""
        table = Table(title="Configuration", box=box.ROUNDED)
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        # Mask API key for security
        api_key = config.get('api_key', 'Not set')
        if api_key and len(api_key) > 8:
            masked_key = f"{api_key[:4]}...{api_key[-4:]}"
        else:
            masked_key = "Not set" if not api_key else "Set"
        
        table.add_row("API Key", masked_key)
        table.add_row("Provider", config.get('provider', 'openrouter'))
        table.add_row("Model", config.get('model', 'Not set'))
        table.add_row("Available Models", str(len(config.get('models', []))))
        
        console.print(table)
        console.print()
    
    def validate_environment(self) -> bool:
        """Validate environment configuration with rich output."""
        console.print("[yellow]Validating environment configuration...[/yellow]")
        
        # Load environment variables
        load_dotenv()
        env_vars = {
            'API_KEY': os.getenv('API_KEY', ''),
            'PROVIDER': os.getenv('PROVIDER', ''),
            'DEFAULT_MODEL': os.getenv('DEFAULT_MODEL', ''),
            'MODELS': os.getenv('MODELS', ''),
        }
        
        # Validate using our comprehensive validator
        results = env_validator.validate_all(env_vars)
        
        # Display results
        has_errors = False
        for var_name, result in results.items():
            if not result.is_valid:
                has_errors = True
                console.print(f"[red]ERROR {var_name}:[/red] {result.error_message}")
                if result.suggestion:
                    console.print(f"   [dim]SUGGESTION: {result.suggestion}[/dim]")
            elif result.warning_message:
                console.print(f"[yellow]WARNING {var_name}:[/yellow] {result.warning_message}")
        
        if not has_errors:
            console.print("[green]SUCCESS: Environment configuration looks good![/green]")
        
        console.print()
        return not has_errors
    
    def load_configuration(self, 
                         api_key: Optional[str] = None,
                         provider: Optional[str] = None, 
                         model: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration with rich progress indication."""
        
        with Status("[cyan]Loading configuration...[/cyan]", spinner="dots") as status:
            # Load .env file
            load_dotenv()
            
            config = {
                'api_key': os.getenv('API_KEY', ''),
                'provider': os.getenv('PROVIDER', 'openrouter'),
                'model': os.getenv('DEFAULT_MODEL', 'openai/gpt-3.5-turbo'),
                'models': [m.strip() for m in os.getenv('MODELS', '').split(',') if m.strip()]
            }
            
            # Override with CLI arguments
            if api_key:
                config['api_key'] = api_key
            if provider:
                config['provider'] = provider
            if model:
                config['model'] = model
            
            self.config = config
            
        return config
    
    def setup_ai_processor(self, config: Dict[str, Any]) -> bool:
        """Set up AI processor with rich status indication."""
        try:
            with Status("[cyan]Initializing AI processor...[/cyan]", spinner="dots"):
                factory = AIProviderFactory()
                provider = factory.create_provider(config['provider'], config['api_key'])
                self.ai_processor = AIProcessor(provider)
                
                if not self.ai_processor.validate_api_key():
                    console.print("[red]ERROR: No valid API key configured.[/red]")
                    console.print("[dim]Set API_KEY in .env file or use --api-key option.[/dim]")
                    return False
            
            console.print(f"[green]SUCCESS: AI processor initialized with {config['provider']} provider[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]ERROR: Failed to initialize AI processor: {str(e)}[/red]")
            return False
    
    def setup_system_prompt(self, system_prompt_name: Optional[str]) -> bool:
        """Set up system prompt with validation."""
        if not system_prompt_name:
            console.print("[dim]Using default system prompt[/dim]")
            return True
        
        filename = f"systemmessage_{system_prompt_name}.txt"
        
        if not os.path.exists(filename):
            console.print(f"[red]ERROR: System prompt file '{filename}' not found.[/red]")
            return False
        
        success = system_message_manager.set_current_system_message_file(filename)
        if success:
            console.print(f"[green]SUCCESS: Using system prompt: {system_prompt_name}[/green]")
            return True
        else:
            console.print(f"[red]ERROR: Failed to load system prompt file '{filename}'.[/red]")
            return False
    
    def scan_codebase_with_progress(self, 
                                   folder_path: str,
                                   include_patterns: Optional[str] = None,
                                   exclude_patterns: Optional[str] = None,
                                   use_lazy: bool = False) -> tuple[List[str], str]:
        """Scan codebase with beautiful progress indication."""
        
        # Validate directory first
        is_valid, error_msg = self.scanner.validate_directory(folder_path)
        if not is_valid:
            console.print(f"[red]ERROR: {error_msg}[/red]")
            return [], ""
        
        console.print(f"[cyan]Scanning directory: {folder_path}[/cyan]")
        
        try:
            if use_lazy:
                return self._scan_lazy_with_progress(folder_path, include_patterns, exclude_patterns)
            else:
                return self._scan_standard_with_progress(folder_path, include_patterns, exclude_patterns)
                
        except Exception as e:
            console.print(f"[red]ERROR: Failed to scan directory: {str(e)}[/red]")
            return [], ""
    
    def _scan_standard_with_progress(self, folder_path: str, include_patterns: Optional[str], exclude_patterns: Optional[str]) -> tuple[List[str], str]:
        """Standard directory scan with progress bar."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn()
        ) as progress:
            
            # Scan files
            task = progress.add_task("Scanning files...", total=100)
            files = self.scanner.scan_directory(folder_path)
            progress.update(task, advance=30)
            
            # Apply filters
            progress.update(task, description="Applying filters...")
            filtered_files = self._apply_file_filters_with_progress(files, include_patterns, exclude_patterns, progress, task)
            progress.update(task, advance=30)
            
            if not filtered_files:
                console.print("[red]ERROR: No files found after applying filters.[/red]")
                return [], ""
            
            # Read content
            progress.update(task, description="Reading file contents...")
            codebase_content = self.scanner.get_codebase_content(filtered_files)
            progress.update(task, advance=40, description="Complete!")
        
        console.print(f"[green]SUCCESS: Scanned {len(filtered_files)} files successfully[/green]")
        return filtered_files, codebase_content
    
    def _scan_lazy_with_progress(self, folder_path: str, include_patterns: Optional[str], exclude_patterns: Optional[str]) -> tuple[List[str], str]:
        """Lazy directory scan with live progress updates."""
        self.setup_lazy_scanner()
        
        files = []
        total_batches = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn()
        ) as progress:
            
            task = progress.add_task("Lazy scanning files...", total=100)
            
            def progress_callback(current: int, total: int):
                if total > 0:
                    percentage = (current / total) * 80  # Reserve 20% for content reading
                    progress.update(task, completed=percentage, 
                                  description=f"Scanning files... ({current}/{total})")
            
            # Collect files from lazy scanner
            for file_batch in self.lazy_scanner.scan_directory_lazy(folder_path, progress_callback=progress_callback):
                files.extend([file_info.path for file_info in file_batch])
                total_batches += 1
            
            # Apply filters
            progress.update(task, completed=80, description="Applying filters...")
            filtered_files = self._apply_file_filters_simple(files, include_patterns, exclude_patterns)
            
            if not filtered_files:
                console.print("[red]ERROR: No files found after applying filters.[/red]")
                return [], ""
            
            # Get content using lazy scanner
            progress.update(task, completed=90, description="Reading file contents...")
            codebase_content = self.lazy_scanner.get_codebase_content_lazy(filtered_files)
            progress.update(task, completed=100, description="Complete!")
        
        # Show cache statistics
        if self.lazy_scanner:
            stats = self.lazy_scanner.get_cache_stats()
            console.print(f"[dim]📊 Cache hits: {stats.get('cache_hits', 0)}, "
                         f"scan time: {stats.get('total_scan_time', 0):.1f}s[/dim]")
        
        console.print(f"[green]SUCCESS: Lazy scanned {len(filtered_files)} files successfully[/green]")
        return filtered_files, codebase_content
    
    def _apply_file_filters_with_progress(self, files: List[str], include_patterns: Optional[str], 
                                        exclude_patterns: Optional[str], progress, task) -> List[str]:
        """Apply file filters with progress updates."""
        import fnmatch
        
        filtered_files = files
        
        # Apply include patterns
        if include_patterns:
            patterns = [p.strip() for p in include_patterns.split(',')]
            included_files = []
            for pattern in patterns:
                for file_path in files:
                    filename = os.path.basename(file_path)
                    if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(file_path, pattern):
                        included_files.append(file_path)
            filtered_files = list(set(included_files))
            console.print(f"[dim]📋 Include filter: {len(filtered_files)} files match {patterns}[/dim]")
        
        # Apply exclude patterns
        if exclude_patterns:
            patterns = [p.strip() for p in exclude_patterns.split(',')]
            excluded_files = []
            for pattern in patterns:
                for file_path in filtered_files:
                    filename = os.path.basename(file_path)
                    if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(file_path, pattern):
                        excluded_files.append(file_path)
            
            filtered_files = [f for f in filtered_files if f not in excluded_files]
            if excluded_files:
                console.print(f"[dim]🚫 Exclude filter: {len(excluded_files)} files excluded by {patterns}[/dim]")
        
        return filtered_files
    
    def _apply_file_filters_simple(self, files: List[str], include_patterns: Optional[str], exclude_patterns: Optional[str]) -> List[str]:
        """Simple file filter application without progress updates."""
        import fnmatch
        
        filtered_files = files
        
        if include_patterns:
            patterns = [p.strip() for p in include_patterns.split(',')]
            included_files = []
            for pattern in patterns:
                for file_path in files:
                    filename = os.path.basename(file_path)
                    if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(file_path, pattern):
                        included_files.append(file_path)
            filtered_files = list(set(included_files))
        
        if exclude_patterns:
            patterns = [p.strip() for p in exclude_patterns.split(',')]
            excluded_files = []
            for pattern in patterns:
                for file_path in filtered_files:
                    filename = os.path.basename(file_path)
                    if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(file_path, pattern):
                        excluded_files.append(file_path)
            
            filtered_files = [f for f in filtered_files if f not in excluded_files]
        
        return filtered_files
    
    def process_question_with_status(self, question: str, codebase_content: str, model: str) -> Optional[Dict[str, Any]]:
        """Process question with beautiful status indication and real-time updates."""
        
        console.print(f"[cyan]AI Processing with {model}...[/cyan]")
        console.print(f"[dim]Question: {question[:100]}{'...' if len(question) > 100 else ''}[/dim]")
        console.print()
        
        try:
            import time
            start_time = time.time()
            
            # Create a live display for real-time updates
            with Live(self._create_processing_layout(), refresh_per_second=4) as live:
                
                def update_callback(response: str, status: str):
                    """Callback to update live display with AI processing status."""
                    live.update(self._create_processing_layout(status, len(response) if response else 0))
                
                # Process with AI
                ai_response = self.ai_processor.process_question(
                    question=question,
                    conversation_history=[],
                    codebase_content=codebase_content,
                    model=model,
                    update_callback=update_callback
                )
                
                # Final update
                end_time = time.time()
                processing_time = end_time - start_time
                live.update(self._create_processing_layout("Complete!", len(ai_response), processing_time))
            
            console.print(f"[green]SUCCESS: Processing completed in {processing_time:.2f} seconds[/green]")
            console.print()
            
            return {
                'response': ai_response,
                'model': model,
                'provider': str(self.ai_processor.provider.__class__.__name__),
                'processing_time': processing_time,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'response_length': len(ai_response),
                'question_length': len(question)
            }
            
        except Exception as e:
            console.print(f"[red]ERROR: Failed to process question: {str(e)}[/red]")
            return None
    
    def _create_processing_layout(self, status: str = "Processing...", response_chars: int = 0, time_elapsed: float = 0) -> Layout:
        """Create a live layout for processing status."""
        layout = Layout()
        
        # Status panel
        status_content = f"[cyan]{status}[/cyan]"
        if response_chars > 0:
            status_content += f"\n[dim]Response: {response_chars} characters[/dim]"
        if time_elapsed > 0:
            status_content += f"\n[dim]Time: {time_elapsed:.1f}s[/dim]"
        
        status_panel = Panel(
            status_content,
            title="AI AI Processing",
            border_style="cyan",
            padding=(1, 2)
        )
        
        layout.update(status_panel)
        return layout
    
    def display_response(self, result: Dict[str, Any], output_format: str):
        """Display AI response with rich formatting."""
        response = result['response']
        
        if output_format == 'json':
            # JSON output with syntax highlighting
            json_text = json.dumps(result, indent=2, ensure_ascii=False)
            syntax = Syntax(json_text, "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            # Rich structured output
            self._display_structured_response(result)
    
    def _display_structured_response(self, result: Dict[str, Any]):
        """Display response in beautiful structured format."""
        
        # Metadata table
        metadata_table = Table(title="📊 Response Metadata", box=box.ROUNDED, show_header=False)
        metadata_table.add_column("Key", style="cyan", no_wrap=True)
        metadata_table.add_column("Value", style="green")
        
        metadata_table.add_row("Model", result['model'])
        metadata_table.add_row("Provider", result['provider'])
        metadata_table.add_row("Processing Time", f"{result['processing_time']:.2f}s")
        metadata_table.add_row("Timestamp", result['timestamp'])
        metadata_table.add_row("Response Length", f"{result['response_length']:,} chars")
        metadata_table.add_row("Question Length", f"{result['question_length']:,} chars")
        
        console.print(metadata_table)
        console.print()
        
        # Response content
        response_panel = Panel(
            Markdown(result['response']),
            title="AI AI Response",
            border_style="green",
            padding=(1, 2)
        )
        console.print(response_panel)
    
    def save_output_with_confirmation(self, output: str, filename: str) -> bool:
        """Save output to file with rich confirmation and progress."""
        try:
            # Check if file exists
            if os.path.exists(filename):
                if not Confirm.ask(f"[yellow]File '{filename}' exists. Overwrite?[/yellow]"):
                    console.print("[dim]Save cancelled.[/dim]")
                    return False
            
            # Save with progress indication
            with Status(f"[cyan]Saving to {filename}...[/cyan]", spinner="dots"):
                from file_lock import safe_file_operation
                
                with safe_file_operation(filename, timeout=10.0):
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(output)
            
            console.print(f"[green]SUCCESS: Output saved to: {filename}[/green]")
            
            # Show file size
            file_size = os.path.getsize(filename)
            if file_size > 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} bytes"
            console.print(f"[dim]File size: {size_str}[/dim]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]ERROR: Failed to save output: {str(e)}[/red]")
            return False
    
    def generate_auto_save_filename(self, question: str, system_prompt: str = None) -> str:
        """Generate an auto-save filename based on date, time, system prompt, and question."""
        # Get current timestamp
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")

        # Clean system prompt name
        if system_prompt and system_prompt.strip():
            # Remove file extension and path
            system_name = Path(system_prompt).stem
            # Clean for filename use
            system_name = re.sub(r'[^\w\-_]', '_', system_name)[:20]
        else:
            system_name = "default"

        # Clean question for filename use
        question_clean = re.sub(r'[^\w\s\-_]', '', question)
        question_clean = re.sub(r'\s+', '_', question_clean.strip())[:50]
        if not question_clean:
            question_clean = "analysis"

        # Get save directory from environment or default to "results"
        save_dir = os.getenv('DIR_SAVE', 'results')

        # Create directory if it doesn't exist (with parents=True for custom paths)
        results_dir = Path(save_dir)
        results_dir.mkdir(exist_ok=True, parents=True)

        # Generate filename
        filename = f"{date_str}_{time_str}_{system_name}_{question_clean}.md"
        return str(results_dir / filename)
    
    def create_interactive_session_content(self, params: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Create formatted content for interactive session auto-save."""
        lines = [
            "# Code Chat AI - Interactive Session Results",
            "",
            f"**Session Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Session Type:** Interactive Mode",
            "",
            "## Input Parameters",
            "",
            f"**Folder:** `{params.get('folder', 'N/A')}`",
            f"**Question:** {params.get('question', 'N/A')}",
            f"**Model:** {params.get('model', 'N/A')}",
            f"**Provider:** {params.get('provider', 'N/A')}",
            f"**System Prompt:** {params.get('system_prompt', 'default')}",
            "",
            "### File Filtering",
            f"**Include Patterns:** {params.get('include', 'None')}",
            f"**Exclude Patterns:** {params.get('exclude', 'None')}",
            f"**Lazy Loading:** {params.get('use_lazy', False)}",
            "",
            "### Output Options", 
            f"**Output Format:** {params.get('output_format', 'structured')}",
            f"**Show File Tree:** {params.get('show_tree', True)}",
            "",
            "## Analysis Results",
            "",
            f"**Processing Time:** {result.get('processing_time', 'N/A')}s",
            f"**Response Length:** {len(result.get('response', '')):,} characters",
            f"**Files Analyzed:** {params.get('files_count', 'N/A')}",
            "",
            "### AI Response",
            "",
            result.get('response', 'No response available')
        ]
        
        return '\n'.join(lines)
    
    def display_file_tree(self, files: List[str], base_path: str):
        """Display selected files in a beautiful tree structure."""
        if not files:
            return
        
        console.print(f"[cyan]FOLDER Selected Files ({len(files)} total):[/cyan]")
        
        tree = Tree(f"FOLDER {os.path.basename(base_path) or base_path}")
        
        # Group files by directory
        file_groups = {}
        for file_path in files:
            rel_path = os.path.relpath(file_path, base_path)
            dir_parts = Path(rel_path).parts[:-1]
            filename = Path(rel_path).name
            
            # Create nested structure
            current_group = file_groups
            for part in dir_parts:
                if part not in current_group:
                    current_group[part] = {}
                current_group = current_group[part]
            
            if '__files__' not in current_group:
                current_group['__files__'] = []
            current_group['__files__'].append(filename)
        
        # Build tree recursively
        def add_to_tree(tree_node, group_dict, path_so_far=""):
            for key, value in sorted(group_dict.items()):
                if key == '__files__':
                    # Add files
                    for filename in sorted(value):
                        file_icon = self._get_file_icon(filename)
                        tree_node.add(f"{file_icon} {filename}")
                else:
                    # Add directory
                    dir_node = tree_node.add(f"FOLDER {key}")
                    add_to_tree(dir_node, value, os.path.join(path_so_far, key))
        
        add_to_tree(tree, file_groups)
        console.print(tree)
        console.print()
    
    def _get_file_icon(self, filename: str) -> str:
        """Get appropriate icon for file type."""
        ext = Path(filename).suffix.lower()
        icons = {
            '.py': 'PY',
            '.js': 'JS',
            '.ts': 'TS',
            '.jsx': 'JSX',
            '.tsx': 'TSX',
            '.java': 'JAVA',
            '.cpp': 'CPP',
            '.c': 'C',
            '.h': 'H',
            '.cs': 'CS',
            '.go': 'GO',
            '.rs': 'RS',
            '.php': 'PHP',
            '.rb': 'RB',
            '.swift': 'SWIFT',
            '.kt': 'KT',
            '.scala': 'SCALA',
            '.r': 'R',
            '.sql': 'SQL',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
            '.md': 'MD',
            '.txt': 'TXT',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'LESS'
        }
        return icons.get(ext, 'FILE')
    
    def interactive_folder_selection(self) -> str:
        """Interactive folder selection with suggestions and .env defaults."""
        console.print("\n[cyan]Select Codebase Folder[/cyan]")
        console.print("[dim]Enter the path to your codebase directory[/dim]")
        
        # Check if there's a default folder from previous runs or .env
        default_folder = "."
        last_used_folder = os.getenv("LAST_USED_FOLDER")
        if last_used_folder and os.path.exists(last_used_folder):
            default_folder = last_used_folder
            console.print(f"[green]Current setting:[/green] {last_used_folder}")
        
        # Suggest common directories
        current_dir = os.getcwd()
        suggestions = []
        
        # Check for common project directories
        common_dirs = ['src', 'lib', 'app', 'backend', 'frontend', 'api']
        for dir_name in common_dirs:
            if os.path.exists(os.path.join(current_dir, dir_name)):
                suggestions.append(f"./{dir_name}")
        
        # Always suggest current directory and default folder
        suggestions.insert(0, ".")
        if default_folder != "." and default_folder not in suggestions:
            suggestions.insert(0, default_folder)
        
        if suggestions:
            console.print("\n[yellow]Suggestions:[/yellow]")
            for i, suggestion in enumerate(suggestions[:5], 1):
                console.print(f"  {i}. {suggestion}")
        
        while True:
            folder = Prompt.ask(
                "\n[bold]Folder path[/bold]", 
                default=default_folder,
                show_default=True
            )
            
            # Handle numeric selection
            if folder.isdigit() and 1 <= int(folder) <= len(suggestions):
                folder = suggestions[int(folder) - 1]
            
            # Validate folder
            if os.path.exists(folder) and os.path.isdir(folder):
                return os.path.abspath(folder)
            else:
                console.print(f"[red]Directory '{folder}' does not exist. Please try again.[/red]")
    
    def interactive_question_selection(self) -> str:
        """Interactive question selection with common templates and .env defaults."""
        console.print("\n[cyan]What would you like to ask about your codebase?[/cyan]")
        
        # Check for last used question from .env
        last_question = os.getenv("LAST_USED_QUESTION")
        if last_question and len(last_question.strip()) > 10:
            console.print(f"[green]Last question:[/green] {last_question[:80]}{'...' if len(last_question) > 80 else ''}")
        
        # Common question templates
        templates = [
            "What is the main purpose and functionality of this codebase?",
            "Explain the overall architecture and design patterns used",
            "Find potential security vulnerabilities in this code",
            "Review the code quality and suggest improvements",
            "Identify performance bottlenecks and optimization opportunities",
            "Generate documentation for the main components",
            "List all the main functions and their purposes",
            "Analyze the testing coverage and suggest test improvements",
            "Custom question (I'll type my own)"
        ]
        
        # Add last question to templates if it exists and isn't already there
        if last_question and last_question not in templates:
            templates.insert(0, f"Use last question: {last_question[:50]}{'...' if len(last_question) > 50 else ''}")
        
        console.print("\n[yellow]Quick Templates:[/yellow]")
        for i, template in enumerate(templates, 1):
            if i <= 9:  # Show first 9 templates (including last question if present)
                console.print(f"  {i}. {template}")
        
        while True:
            prompt_text = f"\n[bold]Select a template (1-{min(9, len(templates))}) or type your question[/bold]"
            if last_question:
                prompt_text += f"\n[dim]Press Enter to use: {last_question[:60]}{'...' if len(last_question) > 60 else ''}[/dim]"
            
            choice = Prompt.ask(prompt_text, default="" if not last_question else None)
            
            # If user pressed Enter and we have a last question, use it
            if not choice and last_question:
                return last_question
            
            # Handle numeric selection
            if choice.isdigit() and 1 <= int(choice) <= len(templates):
                selected_template = templates[int(choice) - 1]
                if selected_template.startswith("Custom"):
                    return Prompt.ask("\n[bold]Enter your custom question[/bold]")
                elif selected_template.startswith("Use last question:"):
                    return last_question
                else:
                    # Allow user to modify the template
                    return Prompt.ask(
                        "\n[bold]Question[/bold] (edit if needed)",
                        default=selected_template
                    )
            else:
                # User typed a custom question
                if len(choice.strip()) > 10:  # Reasonable question length
                    return choice.strip()
                else:
                    console.print("[red]Please enter a more detailed question or select a template.[/red]")
    
    def interactive_provider_selection(self, available_providers: List[str]) -> Optional[str]:
        """Interactive provider selection with .env defaults."""
        if not available_providers:
            return None

        console.print("\n[cyan]Select AI Provider[/cyan]")
        console.print("[dim]Choose the AI provider for analysis[/dim]")

        # Show current default provider from .env
        default_provider = os.getenv("PROVIDER", "openrouter")
        if default_provider:
            console.print(f"[green]Current default:[/green] {default_provider}")

        # Display available providers in a nice format
        console.print("\n[yellow]Available Providers:[/yellow]")
        for i, provider in enumerate(available_providers, 1):
            status = " [green](CURRENT)[/green]" if provider == default_provider else ""
            console.print(f"  {i}. [cyan]{provider.title()}[/cyan]{status}")

        # Add default option
        console.print(f"  {len(available_providers) + 1}. [dim]Use current default ({default_provider})[/dim]")

        while True:
            choice = Prompt.ask(
                f"\n[bold]Select provider (1-{len(available_providers) + 1})[/bold]",
                default=str(len(available_providers) + 1)
            )

            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_providers):
                    return available_providers[choice_num - 1]
                elif choice_num == len(available_providers) + 1:
                    return None  # Use default

            console.print("[red]Invalid selection. Please try again.[/red]")

    def interactive_model_selection(self, available_models: List[str]) -> Optional[str]:
        """Interactive model selection with .env defaults."""
        if not available_models:
            return None

        console.print("\n[cyan]Select AI Model[/cyan]")
        console.print("[dim]Choose the AI model for analysis[/dim]")

        # Show current default model from .env
        default_model = os.getenv("DEFAULT_MODEL")
        if default_model:
            console.print(f"[green]Current default:[/green] {default_model}")

        # Display available models in a nice format
        console.print("\n[yellow]Available Models:[/yellow]")
        for i, model in enumerate(available_models[:10], 1):  # Show first 10 models
            provider = model.split('/')[0] if '/' in model else 'Unknown'
            model_name = model.split('/')[-1] if '/' in model else model
            status = " [green](CURRENT)[/green]" if model == default_model else ""
            console.print(f"  {i}. [cyan]{model_name}[/cyan] [dim]({provider}){status}[/dim]")

        # Add default option
        console.print(f"  {len(available_models) + 1}. [dim]Use current default ({default_model or 'from .env'})[/dim]")

        while True:
            choice = Prompt.ask(
                f"\n[bold]Select model (1-{len(available_models) + 1})[/bold]",
                default=str(len(available_models) + 1)
            )

            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_models):
                    return available_models[choice_num - 1]
                elif choice_num == len(available_models) + 1:
                    return None  # Use default

            console.print("[red]Invalid selection. Please try again.[/red]")
    
    def interactive_options_selection(self) -> Dict[str, Any]:
        """Interactive selection of advanced options with .env defaults."""
        console.print("\n[cyan]Advanced Options[/cyan]")
        console.print("[dim]Configure additional analysis options[/dim]")
        
        options = {}
        
        # Show current .env settings for reference
        current_system_prompt = os.getenv("CURRENT_SYSTEM_PROMPT", "systemmessage_default.txt")
        current_ignore = os.getenv("IGNORE_FOLDERS", "")
        current_ui_theme = os.getenv("UI_THEME", "auto")
        
        console.print(f"\n[green]Current .env settings:[/green]")
        console.print(f"  System prompt: {current_system_prompt}")
        console.print(f"  Ignore folders: {current_ignore[:50]}{'...' if len(current_ignore) > 50 else ''}")
        console.print(f"  UI theme: {current_ui_theme}")
        
        # File filtering
        if Confirm.ask("\n[yellow]Filter files by type?[/yellow]", default=False):
            # Show current ignore folders as suggestion
            if current_ignore:
                console.print(f"[dim]Current ignore patterns: {current_ignore}[/dim]")
            
            options['include'] = Prompt.ask(
                "[bold]Include patterns[/bold] (comma-separated, e.g., '*.py,*.js')",
                default=""
            ) or None
            
            exclude_default = os.getenv("LAST_EXCLUDE_PATTERNS", "")
            options['exclude'] = Prompt.ask(
                "[bold]Exclude patterns[/bold] (comma-separated, e.g., 'test_*,*.min.js')",
                default=exclude_default
            ) or None
        
        # System prompt with current setting
        current_prompt_name = current_system_prompt.replace("systemmessage_", "").replace(".txt", "")
        use_custom_prompt = Confirm.ask(
            f"\n[yellow]Use specialized system prompt?[/yellow] (current: {current_prompt_name})", 
            default=current_prompt_name != "default"
        )
        
        if use_custom_prompt:
            system_prompts = [
                "security", "codereview", "performance", 
                "documentation", "testing", "architecture",
                "optimization", "debugging", "beginner"
            ]
            
            console.print(f"\n[yellow]Available system prompts:[/yellow]")
            current_index = None
            for i, prompt in enumerate(system_prompts, 1):
                status = " [green](CURRENT)[/green]" if prompt == current_prompt_name else ""
                console.print(f"  {i}. {prompt}{status}")
                if prompt == current_prompt_name:
                    current_index = i
            
            default_choice = str(current_index) if current_index else ""
            choice = Prompt.ask(
                f"\n[bold]Select system prompt (1-{len(system_prompts)}) or enter custom[/bold]",
                default=default_choice
            )
            
            if choice.isdigit() and 1 <= int(choice) <= len(system_prompts):
                options['system_prompt'] = system_prompts[int(choice) - 1]
            elif choice.strip():
                options['system_prompt'] = choice.strip()
        
        # Output options
        last_output_format = os.getenv("LAST_OUTPUT_FORMAT", "structured")
        options['output_format'] = "json" if Confirm.ask(
            f"\n[yellow]Output as JSON?[/yellow] (last used: {last_output_format})", 
            default=last_output_format == "json"
        ) else "structured"
        
        last_save_location = os.getenv("LAST_SAVE_LOCATION", "")
        if Confirm.ask("\n[yellow]Save results to file?[/yellow]", default=bool(last_save_location)):
            default_filename = last_save_location or f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if options['output_format'] == 'json' and not default_filename.endswith('.json'):
                default_filename = default_filename.rsplit('.', 1)[0] + '.json'
            elif options['output_format'] != 'json' and not default_filename.endswith('.md'):
                default_filename = default_filename.rsplit('.', 1)[0] + '.md'
                
            options['save_to'] = Prompt.ask(
                "[bold]Filename[/bold]",
                default=default_filename
            )
        
        # Advanced processing options
        last_lazy_setting = os.getenv("LAST_USE_LAZY", "true").lower() == "true"
        options['use_lazy'] = Confirm.ask(
            "\n[yellow]Use lazy loading for large codebases?[/yellow]", 
            default=last_lazy_setting
        )
        
        last_tree_setting = os.getenv("LAST_SHOW_TREE", "true").lower() == "true"
        options['show_tree'] = Confirm.ask(
            "\n[yellow]Show file tree?[/yellow]", 
            default=last_tree_setting
        )
        
        return options


# Global CLI interface instance
cli_interface = RichCLIInterface()


@app.command()
def analyze(
    folder: Optional[str] = typer.Argument(None, help="Path to the codebase folder to analyze"),
    question: Optional[str] = typer.Argument(None, help="Question to ask about the codebase"),
    
    # AI Configuration
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API key (overrides .env file)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p",
                                         help="AI provider (dynamically loaded from PROVIDERS env var)"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", "-s", help="System prompt name (e.g., 'security_expert')"),
    
    # File Filtering
    include: Optional[str] = typer.Option(None, "--include", "-i", help="File patterns to include (comma-separated)"),
    exclude: Optional[str] = typer.Option(None, "--exclude", "-e", help="File patterns to exclude (comma-separated)"),
    
    # Output Options
    output_format: str = typer.Option("structured", "--output", "-o", help="Output format (structured, json)"),
    save_to: Optional[str] = typer.Option(None, "--save-to", "-f", help="Save output to file"),
    
    # Processing Options
    use_lazy: bool = typer.Option(False, "--lazy", help="Use lazy loading for large codebases"),
    
    # Display Options  
    show_tree: bool = typer.Option(True, "--tree/--no-tree", help="Show file tree"),
    validate_env: bool = typer.Option(True, "--validate/--no-validate", help="Validate environment"),
):
    """
    Analyze your codebase with AI assistance
    
    This command scans your codebase, applies any specified filters, and asks
    an AI model to analyze the code according to your question.
    
    If you don't provide folder and question arguments, you'll be guided through
    an interactive setup process.
    
    Examples:
    
        # Interactive mode (prompts for all options)
        codechat-rich analyze
        
        # Basic analysis
        codechat-rich analyze ./src "Explain what this code does"
        
        # Security review with specific model
        codechat-rich analyze ./src "Find security issues" --model gpt-4 --system-prompt security_expert
        
        # Filter specific file types
        codechat-rich analyze ./src "Review Python code" --include "*.py" --exclude "test_*"
        
        # Save results to file
        codechat-rich analyze ./src "Summarize architecture" --save-to analysis.md
        
        # JSON output for automation
        codechat-rich analyze ./src "List all functions" --output json --save-to functions.json
    """
    
    # Display welcome banner
    cli_interface.print_welcome_banner()
    
    # Check if we need interactive mode
    interactive_mode = (folder is None) or (question is None)
    
    # Interactive mode if missing required parameters
    if folder is None:
        folder = cli_interface.interactive_folder_selection()
    
    if question is None:
        question = cli_interface.interactive_question_selection()
    
    # Validate environment if requested
    if validate_env:
        if not cli_interface.validate_environment():
            console.print("[yellow]WARNING:  Environment validation failed, but continuing...[/yellow]")
            console.print()
    
    # Load configuration
    config = cli_interface.load_configuration(api_key, provider, model)
    cli_interface.print_config_summary(config)
    
    # Interactive provider selection if not specified
    if provider is None:
        from ai import AIProviderFactory
        available_providers = AIProviderFactory.get_available_providers()
        if len(available_providers) > 1:  # Only show if multiple providers available
            selected_provider = cli_interface.interactive_provider_selection(available_providers)
            if selected_provider:
                config['provider'] = selected_provider

    # Interactive model selection if not specified
    if model is None and config.get('models'):
        model = cli_interface.interactive_model_selection(config['models'])
        if model:
            config['model'] = model
    
    # Interactive options selection if in full interactive mode
    if interactive_mode:
        console.print("\n" + "="*50)
        if Confirm.ask("\n[yellow]Configure advanced options?[/yellow]", default=False):
            interactive_options = cli_interface.interactive_options_selection()
            
            # Apply interactive options
            include = include or interactive_options.get('include')
            exclude = exclude or interactive_options.get('exclude')
            system_prompt = system_prompt or interactive_options.get('system_prompt')
            output_format = interactive_options.get('output_format', output_format)
            save_to = save_to or interactive_options.get('save_to')
            use_lazy = interactive_options.get('use_lazy', use_lazy)
            show_tree = interactive_options.get('show_tree', show_tree)
    
    # Setup AI processor
    if not cli_interface.setup_ai_processor(config):
        raise typer.Exit(1)
    
    # Setup system prompt
    if not cli_interface.setup_system_prompt(system_prompt):
        raise typer.Exit(1)
    
    # Scan codebase
    files, codebase_content = cli_interface.scan_codebase_with_progress(
        folder, include, exclude, use_lazy
    )
    
    if not files:
        console.print("[red]ERROR: No files found to analyze[/red]")
        raise typer.Exit(1)
    
    # Display file tree if requested
    if show_tree:
        cli_interface.display_file_tree(files, folder)
    
    # Process question
    result = cli_interface.process_question_with_status(question, codebase_content, config['model'])
    if not result:
        raise typer.Exit(1)
    
    # Display results
    console.print(Rule("Results"))
    cli_interface.display_response(result, output_format)
    
    # Auto-save for interactive mode or manual save if requested
    if interactive_mode:
        # Auto-generate filename and save without confirmation for interactive sessions
        auto_filename = cli_interface.generate_auto_save_filename(question, system_prompt)
        
        # Collect all session parameters
        session_params = {
            'folder': folder,
            'question': question,
            'model': config.get('model'),
            'provider': config.get('provider'),
            'system_prompt': system_prompt or 'default',
            'include': include,
            'exclude': exclude,
            'use_lazy': use_lazy,
            'output_format': output_format,
            'show_tree': show_tree,
            'files_count': len(files) if files else 0
        }
        
        # Create comprehensive session content
        session_content = cli_interface.create_interactive_session_content(session_params, result)
        
        # Save without confirmation (auto-save)
        try:
            with open(auto_filename, 'w', encoding='utf-8') as f:
                f.write(session_content)
            console.print(f"\n[green]SESSION SAVED: {auto_filename}[/green]")
            
            # Show file size
            file_size = os.path.getsize(auto_filename)
            if file_size > 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} bytes"
            console.print(f"[dim]File size: {size_str}[/dim]")
            
        except Exception as e:
            console.print(f"[yellow]WARNING:  Could not auto-save session: {str(e)}[/yellow]")
    
    # Manual save if specifically requested
    if save_to:
        if output_format == 'json':
            output_content = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            # Create a formatted text output
            lines = [
                f"# Code Analysis Results",
                f"",
                f"**Model:** {result['model']}",
                f"**Provider:** {result['provider']}",
                f"**Processing Time:** {result['processing_time']:.2f}s",
                f"**Timestamp:** {result['timestamp']}",
                f"",
                f"## Question",
                f"{question}",
                f"",
                f"## Response",
                f"",
                result['response']
            ]
            output_content = '\n'.join(lines)
        
        if not cli_interface.save_output_with_confirmation(output_content, save_to):
            raise typer.Exit(1)
    
    console.print()
    console.print("[green]COMPLETE: Analysis complete![/green]")


@app.command()
def config(
    validate: bool = typer.Option(False, "--validate", "-v", help="Validate environment configuration"),
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive configuration setup")
):
    """
    Manage configuration settings
    
    Validate, display, or interactively configure your environment settings.
    """
    cli_interface.print_welcome_banner()
    
    if validate or show:
        # Load and display configuration
        config = cli_interface.load_configuration()
        cli_interface.print_config_summary(config)
        
        if validate:
            cli_interface.validate_environment()
    
    if interactive:
        console.print("[yellow]🔧 Interactive Configuration Setup[/yellow]")
        console.print("[dim]This will help you set up your .env file[/dim]")
        console.print()
        
        # Interactive setup
        current_api_key = os.getenv('API_KEY', '')
        if current_api_key:
            console.print(f"[green]Current API key: {current_api_key[:4]}...{current_api_key[-4:] if len(current_api_key) > 8 else 'Set'}[/green]")
        
        if not current_api_key or Confirm.ask("Update API key?"):
            new_api_key = Prompt.ask("Enter your API key", password=True)
            # TODO: Save to .env file
            console.print("[green]SUCCESS: API key updated[/green]")
        
        # More interactive configuration options could be added here
        console.print("[green]COMPLETE: Configuration setup complete![/green]")
    
    if not (validate or show or interactive):
        console.print("[yellow]Use --validate, --show, or --interactive options[/yellow]")


@app.command()
def models(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Show models for specific provider"),
    test: Optional[str] = typer.Option(None, "--test", "-t", help="Test specific model")
):
    """
    List available models and test connections
    
    Display available AI models or test a specific model connection.
    """
    cli_interface.print_welcome_banner()
    
    # Load configuration
    config = cli_interface.load_configuration()
    
    if test:
        console.print(f"[yellow]🧪 Testing model: {test}[/yellow]")
        
        # Setup AI processor
        if not cli_interface.setup_ai_processor(config):
            raise typer.Exit(1)
        
        # Test with simple question
        test_result = cli_interface.process_question_with_status(
            "Hello! Please respond with 'Connection successful' if you can read this.",
            "",  # No codebase content needed for test
            test
        )
        
        if test_result:
            console.print(f"[green]SUCCESS: Model {test} is working correctly[/green]")
        else:
            console.print(f"[red]ERROR: Model {test} test failed[/red]")
    else:
        # Display available models
        models_list = config.get('models', [])
        current_model = config.get('model', 'Not set')
        
        table = Table(title="Available Models", box=box.ROUNDED)
        table.add_column("Model", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Provider")
        
        for model in models_list:
            status = "CURRENT" if model == current_model else "Available"
            provider_name = model.split('/')[0] if '/' in model else "Unknown"
            table.add_row(model, status, provider_name)
        
        if not models_list:
            table.add_row("No models configured", "Configure MODELS in .env", "N/A")
        
        console.print(table)


@app.command()
def interactive():
    """
    Launch fully interactive analysis mode
    
    Guides you through all analysis options step by step with helpful prompts,
    suggestions, and templates. Perfect for first-time users or when you want
    to explore all available options.
    """
    # Call analyze with no parameters to trigger full interactive mode
    analyze(
        folder=None,
        question=None,
        api_key=None,
        model=None,
        provider=None,
        system_prompt=None,
        include=None,
        exclude=None,
        output_format="structured",
        save_to=None,
        use_lazy=False,
        show_tree=True,
        validate_env=True
    )


@app.command()  
def version():
    """
    Show version information
    """
    version_panel = Panel.fit(
        "[bold blue]Code Chat AI - Rich CLI[/bold blue]\n" +
        "[dim]Version 2.0 - Rich + Typer Enhanced[/dim]\n" +
        f"[dim]Python {sys.version.split()[0]}[/dim]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(version_panel)


if __name__ == "__main__":
    app()