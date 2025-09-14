#!/usr/bin/env python3
"""
Standard CLI Interface for Code Chat AI

This module provides a command-line interface for the Code Chat AI application,
allowing users to analyze codebases from the terminal with various configuration options.
"""

import argparse
import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Import core functionality
from lazy_file_scanner import CodebaseScanner
from ai import AIProcessor, AIProviderFactory
from system_message_manager import system_message_manager
from logger import get_logger


class CLIInterface:
    """Command-line interface for Code Chat AI."""

    def __init__(self):
        """Initialize the CLI interface."""
        self.scanner = CodebaseScanner()
        self.ai_processor = None
        self.verbose = False
        self.logger = get_logger("cli")

    def setup_argument_parser(self) -> argparse.ArgumentParser:
        """Set up the argument parser for CLI options."""
        parser = argparse.ArgumentParser(
            description="Code Chat AI - Analyze codebases with AI assistance",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python minicli.py --cli --folder ./src --question "What does this code do?"
  python minicli.py --cli --folder ./src --question "Find security issues" --system-prompt security_expert
  python minicli.py --cli --folder ./src --question "Review code quality" --include "*.py" --exclude "test_*"
  python minicli.py --cli --folder ./src --question "Summarize architecture" --output json --save-to analysis.json
            """
        )

        # Core arguments
        parser.add_argument(
            '--cli',
            action='store_true',
            help='Run in CLI mode (required when using other CLI options)'
        )

        parser.add_argument(
            '--folder', '-f',
            type=str,
            required=True,
            help='Path to the codebase folder to analyze'
        )

        parser.add_argument(
            '--question', '-q',
            type=str,
            required=True,
            help='Question to ask about the codebase'
        )

        # AI Configuration
        parser.add_argument(
            '--api-key', '-k',
            type=str,
            help='API key (overrides environment variable)'
        )

        parser.add_argument(
            '--model', '-m',
            type=str,
            help='AI model to use (overrides environment variable)'
        )

        parser.add_argument(
            '--provider', '-p',
            type=str,
            help='AI provider to use (overrides environment variable)'
        )

        parser.add_argument(
            '--system-prompt', '-s',
            type=str,
            help='System prompt name (e.g., security_expert, default, etc.)'
        )

        # File Filtering
        parser.add_argument(
            '--include', '-i',
            type=str,
            help='File patterns to include (comma-separated, e.g., "*.py,*.js")'
        )

        parser.add_argument(
            '--exclude', '-e',
            type=str,
            help='File patterns to exclude (comma-separated, e.g., "test_*,*.min.js")'
        )

        # Output Options
        parser.add_argument(
            '--output', '-o',
            type=str,
            choices=['structured', 'json'],
            default='structured',
            help='Output format (default: structured)'
        )

        parser.add_argument(
            '--save-to',
            type=str,
            help='Save output to file'
        )

        # Other Options
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )

        return parser

    def log(self, message: str, force: bool = False):
        """Log a message if verbose mode is enabled or forced."""
        if self.verbose or force:
            print(f"[CLI] {message}", file=sys.stderr)

    def load_configuration(self, args) -> Dict[str, Any]:
        """Load configuration from environment variables and CLI arguments."""
        # Load environment variables
        load_dotenv()

        config = {
            'api_key': os.getenv('API_KEY', ''),
            'provider': os.getenv('PROVIDER', 'openrouter'),
            'model': os.getenv('DEFAULT_MODEL', 'openai/gpt-3.5-turbo'),
            'models': [m.strip() for m in os.getenv('MODELS', '').split(',') if m.strip()]
        }

        # Override with CLI arguments if provided
        if args.api_key:
            config['api_key'] = args.api_key
        if args.provider:
            config['provider'] = args.provider
        if args.model:
            config['model'] = args.model

        return config

    def setup_ai_processor(self, config: Dict[str, Any]) -> bool:
        """Set up the AI processor with the given configuration."""
        try:
            # Create provider instance
            factory = AIProviderFactory()
            provider = factory.create_provider(config['provider'], config['api_key'])

            # Create AI processor
            self.ai_processor = AIProcessor(provider)

            # Validate API key
            if not self.ai_processor.validate_api_key():
                self.log("ERROR: No API key configured. Please set API_KEY in .env file or use --api-key option.", force=True)
                return False

            self.log(f"SUCCESS: AI processor initialized with {config['provider']} provider")
            return True

        except Exception as e:
            self.log(f"ERROR: Failed to initialize AI processor: {str(e)}", force=True)
            return False

    def setup_system_prompt(self, system_prompt_name: Optional[str]) -> bool:
        """Set up the system prompt."""
        if not system_prompt_name:
            self.log("Using default system prompt")
            return True

        filename = f"systemmessage_{system_prompt_name}.txt"

        if not os.path.exists(filename):
            self.log(f"ERROR: System prompt file '{filename}' not found.", force=True)
            return False

        success = system_message_manager.set_current_system_message_file(filename)
        if success:
            self.log(f"SUCCESS: Using system prompt: {system_prompt_name}")
            return True
        else:
            self.log(f"ERROR: Failed to load system prompt file '{filename}'.", force=True)
            return False

    def apply_file_filters(self, files: List[str], include_patterns: Optional[str],
                          exclude_patterns: Optional[str]) -> List[str]:
        """Apply include/exclude filters to the file list."""
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

        return filtered_files

    def scan_codebase(self, folder_path: str, include_patterns: Optional[str],
                     exclude_patterns: Optional[str]) -> Tuple[List[str], str]:
        """Scan the codebase and return files and content."""
        # Validate directory
        is_valid, error_msg = self.scanner.validate_directory(folder_path)
        if not is_valid:
            self.log(f"ERROR: {error_msg}", force=True)
            return [], ""

        self.log(f"Scanning directory: {folder_path}")

        try:
            # Scan for files
            files = self.scanner.scan_directory(folder_path)

            if not files:
                self.log("WARNING: No files found in directory", force=True)
                return [], ""

            # Apply filters
            filtered_files = self.apply_file_filters(files, include_patterns, exclude_patterns)

            if not filtered_files:
                self.log("WARNING: No files remain after applying filters", force=True)
                return [], ""

            # Get codebase content
            codebase_content = self.scanner.get_codebase_content(filtered_files)

            self.log(f"SUCCESS: Scanned {len(filtered_files)} files")
            return filtered_files, codebase_content

        except Exception as e:
            self.log(f"ERROR: Failed to scan directory: {str(e)}", force=True)
            return [], ""

    def process_question(self, question: str, codebase_content: str, model: str) -> Optional[Dict[str, Any]]:
        """Process a question with the AI."""
        if not self.ai_processor:
            self.log("ERROR: AI processor not initialized", force=True)
            return None

        try:
            self.log(f"Processing question with {model}...")
            start_time = time.time()

            # Process the question
            response = self.ai_processor.process_question(
                question=question,
                conversation_history=[],
                codebase_content=codebase_content,
                model=model
            )

            processing_time = time.time() - start_time

            result = {
                'response': response,
                'model': model,
                'provider': self.ai_processor.provider,
                'processing_time': processing_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            self.log(".2f")
            return result

        except Exception as e:
            self.log(f"ERROR: Failed to process question: {str(e)}", force=True)
            return None

    def format_output(self, result: Dict[str, Any], output_format: str) -> str:
        """Format the result for output."""
        if output_format == 'json':
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            # Structured text format
            lines = [
                "=" * 50,
                "Code Chat AI - Analysis Results",
                "=" * 50,
                "",
                f"Model: {result['model']}",
                f"Provider: {result['provider']}",
                f"Processing Time: {result['processing_time']:.2f}s",
                f"Timestamp: {result['timestamp']}",
                "",
                "Question:",
                result.get('question', 'N/A'),
                "",
                "Response:",
                result['response'],
                "",
                "=" * 50
            ]
            return "\n".join(lines)

    def save_output(self, output: str, filename: str) -> bool:
        """Save output to a file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(output)
            self.log(f"SUCCESS: Output saved to {filename}")
            return True
        except Exception as e:
            self.log(f"ERROR: Failed to save output to {filename}: {str(e)}", force=True)
            return False

    def run_cli(self, args) -> int:
        """Run the CLI workflow."""
        try:
            # Set verbose mode
            self.verbose = args.verbose

            self.log("Starting Code Chat AI CLI")

            # Load configuration
            config = self.load_configuration(args)
            self.log(f"Configuration loaded - Provider: {config['provider']}, Model: {config['model']}")

            # Setup AI processor
            if not self.setup_ai_processor(config):
                return 1

            # Setup system prompt
            if not self.setup_system_prompt(args.system_prompt):
                return 1

            # Scan codebase
            files, codebase_content = self.scan_codebase(
                args.folder, args.include, args.exclude
            )

            if not files:
                return 1

            # Process question
            result = self.process_question(args.question, codebase_content, config['model'])
            if not result:
                return 1

            # Add question to result for output formatting
            result['question'] = args.question

            # Format and display output
            output = self.format_output(result, args.output)
            print(output)

            # Save to file if requested
            if args.save_to:
                if not self.save_output(output, args.save_to):
                    return 1

            self.log("CLI workflow completed successfully")
            return 0

        except KeyboardInterrupt:
            self.log("Operation cancelled by user", force=True)
            return 1
        except Exception as e:
            self.log(f"Unexpected error: {str(e)}", force=True)
            return 1


# Main entry point for testing
if __name__ == "__main__":
    cli = CLIInterface()
    parser = cli.setup_argument_parser()
    args = parser.parse_args()

    if not args.cli:
        print("ERROR: Use --cli flag to run in CLI mode", file=sys.stderr)
        sys.exit(1)

    exit_code = cli.run_cli(args)
    sys.exit(exit_code)