"""
Command-line interface for the Code Chat application.
Provides headless operation for automation and scripting.
"""
import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from lazy_file_scanner import CodebaseScanner, LazyCodebaseScanner
from ai import AIProcessor
from system_message_manager import system_message_manager


class CLIInterface:
    """Command-line interface for Code Chat application."""
    
    def __init__(self):
        self.scanner = CodebaseScanner()
        self.ai_processor = None
        self.verbose = False
        
    def setup_argument_parser(self) -> argparse.ArgumentParser:
        """Set up and return the argument parser."""
        parser = argparse.ArgumentParser(
            description="Code Chat AI - Analyze codebases with AI assistance",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python minicli.py --cli --folder ./src --question "Explain what this code does"
  python minicli.py --cli --folder ./src --question "Find security issues" --model gpt-4
  python minicli.py --cli --folder ./src --question "Review code" --system-prompt security_expert
  python minicli.py --cli --folder ./src --question "Summarize" --output json --verbose
  python minicli.py --cli --folder ./src --question "Check" --include "*.py" --exclude "test_*"
            """
        )
        
        # Mode selection
        parser.add_argument('--cli', action='store_true', 
                          help='Run in CLI mode (headless operation)')
        
        # Required arguments for CLI mode
        parser.add_argument('--folder', type=str, required='--cli' in sys.argv,
                          help='Path to the codebase folder to analyze')
        parser.add_argument('--question', type=str, required='--cli' in sys.argv,
                          help='Question to ask about the codebase')
        
        # AI configuration overrides
        parser.add_argument('--api-key', type=str,
                          help='API key (overrides .env file)')
        parser.add_argument('--model', type=str,
                          help='AI model to use (overrides .env DEFAULT_MODEL)')
        parser.add_argument('--provider', type=str, choices=['openrouter', 'tachyon'],
                          help='AI provider to use (overrides .env PROVIDER)')
        parser.add_argument('--system-prompt', type=str,
                          help='System prompt file to use (e.g., security_expert for systemmessage_security_expert.txt)')
        
        # File filtering options
        parser.add_argument('--include', type=str,
                          help='File patterns to include (comma-separated, e.g., "*.py,*.js")')
        parser.add_argument('--exclude', type=str,
                          help='File patterns to exclude (comma-separated, e.g., "test_*,*_test.py")')
        
        # Output options
        parser.add_argument('--output', type=str, choices=['structured', 'json'], 
                          default='structured',
                          help='Output format (default: structured)')
        parser.add_argument('--save-to', type=str,
                          help='Save output to file instead of stdout')
        
        # Verbosity
        parser.add_argument('--verbose', '-v', action='store_true',
                          help='Show detailed progress information')
        
        return parser
    
    def log(self, message: str, force: bool = False):
        """Log a message if verbose mode is enabled."""
        if self.verbose or force:
            print(f"[CLI] {message}", file=sys.stderr)
    
    def load_configuration(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Load configuration from .env file and CLI arguments."""
        # Load .env file first
        load_dotenv()
        
        config = {
            'api_key': os.getenv('API_KEY', ''),
            'provider': os.getenv('PROVIDER', 'openrouter'),
            'model': os.getenv('DEFAULT_MODEL', 'openai/gpt-3.5-turbo'),
            'models': [m.strip() for m in os.getenv('MODELS', '').split(',') if m.strip()]
        }
        
        # Override with CLI arguments
        if args.api_key:
            config['api_key'] = args.api_key
            self.log(f"Using API key from CLI argument")
        
        if args.provider:
            config['provider'] = args.provider
            self.log(f"Using provider: {config['provider']}")
        
        if args.model:
            config['model'] = args.model
            self.log(f"Using model: {config['model']}")
        
        return config
    
    def setup_ai_processor(self, config: Dict[str, Any]) -> bool:
        """Set up the AI processor with configuration."""
        try:
            self.ai_processor = AIProcessor(config['api_key'], config['provider'])
            
            if not self.ai_processor.validate_api_key():
                print("ERROR: No API key configured. Set API_KEY in .env file or use --api-key argument.", file=sys.stderr)
                return False
            
            self.log(f"Initialized AI processor with {config['provider']} provider")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to initialize AI processor: {str(e)}", file=sys.stderr)
            return False
    
    def setup_system_prompt(self, system_prompt_name: Optional[str]) -> bool:
        """Set up system prompt if specified."""
        if not system_prompt_name:
            self.log("Using default system prompt")
            return True
        
        # Construct filename from prompt name
        filename = f"systemmessage_{system_prompt_name}.txt"
        
        if not os.path.exists(filename):
            print(f"ERROR: System prompt file '{filename}' not found.", file=sys.stderr)
            return False
        
        # Set current system message file
        success = system_message_manager.set_current_system_message_file(filename)
        if success:
            self.log(f"Using system prompt: {system_prompt_name} ({filename})")
            return True
        else:
            print(f"ERROR: Failed to load system prompt file '{filename}'.", file=sys.stderr)
            return False
    
    def apply_file_filters(self, files: List[str], include_patterns: Optional[str], 
                          exclude_patterns: Optional[str]) -> List[str]:
        """Apply include/exclude filters to file list."""
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
            filtered_files = list(set(included_files))  # Remove duplicates
            self.log(f"Include filter applied: {len(filtered_files)} files match patterns {patterns}")
        
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
            self.log(f"Exclude filter applied: {len(excluded_files)} files excluded by patterns {patterns}")
        
        return filtered_files
    
    def scan_codebase(self, folder_path: str, include_patterns: Optional[str], 
                      exclude_patterns: Optional[str]) -> tuple[List[str], str]:
        """Scan codebase and return files and combined content."""
        self.log("Scanning directory...")
        
        # Validate directory
        is_valid, error_msg = self.scanner.validate_directory(folder_path)
        if not is_valid:
            print(f"ERROR: {error_msg}", file=sys.stderr)
            return [], ""
        
        # Scan for files
        try:
            files = self.scanner.scan_directory(folder_path)
            self.log(f"Found {len(files)} files in directory")
            
            # Apply filters
            filtered_files = self.apply_file_filters(files, include_patterns, exclude_patterns)
            self.log(f"After filtering: {len(filtered_files)} files selected")
            
            if not filtered_files:
                print("ERROR: No files found after applying filters.", file=sys.stderr)
                return [], ""
            
            # Get combined content
            self.log("Reading file contents...")
            codebase_content = self.scanner.get_codebase_content(filtered_files)
            
            return filtered_files, codebase_content
            
        except Exception as e:
            print(f"ERROR: Failed to scan directory: {str(e)}", file=sys.stderr)
            return [], ""
    
    def process_question(self, question: str, codebase_content: str, model: str) -> Optional[Dict[str, Any]]:
        """Process the question with AI and return result."""
        self.log(f"Processing question with {model}...")
        
        try:
            import time
            start_time = time.time()
            
            # Process with AI
            ai_response = self.ai_processor.process_question(
                question=question,
                conversation_history=[],
                codebase_content=codebase_content,
                model=model
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            self.log(f"Processing completed in {processing_time:.2f} seconds")
            
            return {
                'response': ai_response,
                'model': model,
                'provider': self.ai_processor.provider,
                'processing_time': processing_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"ERROR: Failed to process question: {str(e)}", file=sys.stderr)
            return None
    
    def format_output(self, result: Dict[str, Any], output_format: str) -> str:
        """Format the output according to specified format."""
        if output_format == 'json':
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        # Structured format (default)
        lines = [
            f"Model: {result['model']}",
            f"Provider: {result['provider']}",
            f"Time: {result['processing_time']:.2f}s",
            f"Timestamp: {result['timestamp']}",
            "",
            "Response:",
            result['response']
        ]
        
        return '\n'.join(lines)
    
    def save_output(self, output: str, filename: str) -> bool:
        """Save output to file with file locking."""
        try:
            from file_lock import safe_file_operation
            
            with safe_file_operation(filename, timeout=10.0):
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(output)
            
            self.log(f"Output saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to save output to '{filename}': {str(e)}", file=sys.stderr)
            return False
    
    def run_cli(self, args: argparse.Namespace) -> int:
        """Run the CLI interface with given arguments."""
        self.verbose = args.verbose
        
        self.log("Starting CLI mode...")
        
        # Load configuration
        config = self.load_configuration(args)
        
        # Setup AI processor
        if not self.setup_ai_processor(config):
            return 1
        
        # Setup system prompt
        if not self.setup_system_prompt(args.system_prompt):
            return 1
        
        # Scan codebase
        files, codebase_content = self.scan_codebase(args.folder, args.include, args.exclude)
        if not files:
            return 1
        
        # Process question
        result = self.process_question(args.question, codebase_content, config['model'])
        if not result:
            return 1
        
        # Format output
        output = self.format_output(result, args.output)
        
        # Save or print output
        if args.save_to:
            if self.save_output(output, args.save_to):
                self.log(f"Analysis complete - saved to {args.save_to}")
            else:
                return 1
        else:
            print(output)
        
        self.log("CLI processing complete")
        return 0


def create_cli_interface() -> CLIInterface:
    """Factory function to create a CLI interface instance."""
    return CLIInterface()