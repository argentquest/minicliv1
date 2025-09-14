#!/usr/bin/env python3
"""
NiceGUI Frontend for Code Chat AI

This module provides a modern web interface for the Code Chat AI application
using NiceGUI framework. It connects to the FastAPI backend to provide
codebase analysis capabilities through an intuitive web interface.

Features:
- Modern tabbed interface for parameter configuration
- Real-time form validation and error handling
- Results display in new browser tabs
- Responsive design with custom styling
- Integration with FastAPI backend API

Usage:
    python nicegui_frontend.py

The frontend will start on http://localhost:8080 by default.
"""

import os
import sys
from pathlib import Path
import asyncio
import json
from typing import Dict, Any, Optional

from nicegui import ui, app
import httpx
import requests

# Configuration
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8001")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))

class CodeChatWebApp:
    """Main web application class for Code Chat AI."""

    def __init__(self):
        self.backend_url = FASTAPI_URL
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
        self.models = []
        self.providers = []
        self.system_prompts = []

        # Form data
        self.form_data = {
            'folder': '',
            'question': '',
            'model': 'gpt-3.5-turbo',
            'provider': 'openrouter',
            'include': '*.py,*.js,*.ts,*.java,*.cpp,*.c,*.h',
            'exclude': 'test_*,__pycache__,*.pyc,node_modules,venv,.venv',
            'output': 'structured',
            'api_key': ''
        }

        # UI elements (will be set during UI setup)
        self.status_label = None
        self.analyze_button = None
        self.folder_input = None
        self.question_input = None

    async def initialize(self):
        """Initialize the application and load data from backend."""
        try:
            await self.load_backend_data()
            self.setup_ui()
        except Exception as e:
            ui.notify(f"Failed to initialize: {e}", type="negative")
            self.setup_fallback_ui()

    async def load_backend_data(self):
        """Load models, providers, and system prompts from backend."""
        try:
            # Load models
            response = await self.client.get(f"{self.backend_url}/models")
            if response.status_code == 200:
                data = response.json()
                self.models = data.get('models', [])
                if data.get('default'):
                    self.form_data['model'] = data['default']

            # Load providers
            response = await self.client.get(f"{self.backend_url}/providers")
            if response.status_code == 200:
                data = response.json()
                self.providers = data.get('providers', [])
                if data.get('default'):
                    self.form_data['provider'] = data['default']

            # Load system prompts
            response = await self.client.get(f"{self.backend_url}/system-prompts")
            if response.status_code == 200:
                data = response.json()
                self.system_prompts = data.get('prompts', [])

        except Exception as e:
            print(f"Warning: Could not load backend data: {e}")
            # Set defaults
            self.models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
            self.providers = ['openrouter', 'tachyon', 'custom']

    def setup_ui(self):
        """Set up the main user interface."""
        # Custom CSS
        ui.add_css("""
            .main-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .tab-content {
                padding: 20px 0;
            }
            .form-group {
                margin-bottom: 15px;
            }
            .status-info {
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
            .status-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .status-error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .results-container {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;
            }
        """)

        with ui.column().classes('main-container'):
            # Header
            with ui.row().classes('items-center gap-4'):
                ui.icon('smart_toy', size='2rem', color='primary')
                ui.label('🤖 Code Chat AI').classes('text-2xl font-bold')
                ui.label('Advanced Codebase Analysis with AI').classes('text-gray-600')

            # Status indicator
            self.status_label = ui.label("Ready").classes('status-info status-success')

            # Main tabs
            with ui.tabs().classes('w-full') as tabs:
                main_tab = ui.tab('⚙️ Configuration')
                output_tab = ui.tab('📤 Output')

            with ui.tab_panels(tabs, value=main_tab).classes('w-full'):
                with ui.tab_panel(main_tab).classes('tab-content'):
                    self.setup_main_tab()

                with ui.tab_panel(output_tab).classes('tab-content'):
                    self.setup_output_tab()

            # Action buttons
            with ui.row().classes('gap-4 mt-6'):
                self.analyze_button = ui.button('🔍 Analyze Code',
                                              on_click=self.analyze_code).classes('bg-primary text-white px-6 py-2')
                ui.button('🔄 Reset Form', on_click=self.reset_form).classes('px-6 py-2')

    def setup_main_tab(self):
        """Set up the main configuration tab combining basic, AI, and file settings."""
        with ui.card().classes('w-full'):
            ui.label('📋 Complete Configuration').classes('text-xl font-bold mb-6')

            # Basic Configuration Section
            ui.label('📁 Codebase & Question').classes('text-lg font-semibold mb-3 text-blue-600')
            ui.label('Configure the basic settings for your code analysis.').classes('text-sm text-gray-600 mb-4')

            # Codebase folder
            with ui.row().classes('form-group items-center gap-4'):
                with ui.column().classes('flex-1'):
                    self.folder_input = ui.input(
                        label='📂 Codebase Folder Path',
                        placeholder='e.g., /path/to/your/project or C:\\path\\to\\project',
                        value=self.form_data['folder']
                    ).classes('w-full').on_value_change(lambda e: self.update_form_data('folder', e.value))
                    ui.label('💡 The root directory of your codebase to analyze').classes('text-xs text-gray-500 mt-1')
                    ui.label('📝 Enter the full path manually (browsers cannot access local paths for security)').classes('text-xs text-blue-600 mt-1')

                ui.button('📂 Browse', on_click=self.browse_folder).classes('px-4 py-2 h-10')
                ui.button('ℹ️ Help', on_click=self.show_path_help).classes('px-4 py-2 h-10')

            # Analysis question
            with ui.column().classes('mt-4'):
                self.question_input = ui.textarea(
                    label='❓ Analysis Question',
                    placeholder='e.g., "Explain the main architecture" or "Find security vulnerabilities"',
                    value=self.form_data['question']
                ).classes('w-full').on_value_change(lambda e: self.update_form_data('question', e.value))
                ui.label('💡 Ask specific questions about your codebase. Be detailed for better results.').classes('text-xs text-gray-500 mt-1')

            ui.separator().classes('my-6')

            # AI Configuration Section
            ui.label('🤖 AI Model & Provider').classes('text-lg font-semibold mb-3 text-green-600')
            ui.label('Choose the AI model and provider for your analysis.').classes('text-sm text-gray-600 mb-4')

            # Provider selection
            with ui.column().classes('mb-4'):
                ui.select(
                    label='🔌 AI Provider',
                    options=self.providers,
                    value=self.form_data['provider']
                ).classes('w-full').on_value_change(lambda e: self.update_form_data('provider', e.value))
                ui.label('💡 The AI service provider (OpenRouter, Tachyon, etc.)').classes('text-xs text-gray-500 mt-1')

            # Model selection
            with ui.column().classes('mb-4'):
                ui.select(
                    label='🧠 AI Model',
                    options=self.models,
                    value=self.form_data['model']
                ).classes('w-full').on_value_change(lambda e: self.update_form_data('model', e.value))
                ui.label('💡 The specific AI model to use for analysis (affects quality and speed)').classes('text-xs text-gray-500 mt-1')

            # API Key (optional)
            with ui.column().classes('mb-4'):
                ui.input(
                    label='🔑 API Key (Optional)',
                    placeholder='Leave empty to use environment variable',
                    value=self.form_data['api_key'],
                    password=True
                ).classes('w-full').on_value_change(lambda e: self.update_form_data('api_key', e.value))
                ui.label('💡 API key for the selected provider. If empty, uses environment variables.').classes('text-xs text-gray-500 mt-1')

            ui.separator().classes('my-6')

            # File Filtering Section
            ui.label('🎯 File Filtering').classes('text-lg font-semibold mb-3 text-purple-600')
            ui.label('Control which files are included or excluded from analysis.').classes('text-sm text-gray-600 mb-4')

            # Include patterns
            with ui.column().classes('mb-4'):
                ui.textarea(
                    label='✅ Include Patterns',
                    placeholder='*.py,*.js,*.ts,*.java,*.cpp,*.c,*.h',
                    value=self.form_data['include']
                ).classes('w-full').on_value_change(lambda e: self.update_form_data('include', e.value))
                ui.label('💡 File extensions to analyze (comma-separated). Use * for wildcards.').classes('text-xs text-gray-500 mt-1')

            # Exclude patterns
            with ui.column():
                ui.textarea(
                    label='❌ Exclude Patterns',
                    placeholder='test_*,__pycache__,*.pyc,node_modules,venv,.venv',
                    value=self.form_data['exclude']
                ).classes('w-full').on_value_change(lambda e: self.update_form_data('exclude', e.value))
                ui.label('💡 Files/directories to skip (comma-separated). Common: tests, cache, dependencies.').classes('text-xs text-gray-500 mt-1')

    def setup_output_tab(self):
        """Set up the output settings tab."""
        with ui.card().classes('w-full'):
            ui.label('Output Configuration').classes('text-lg font-semibold mb-4')

            # Output format
            ui.select(
                label='Output Format',
                options=['structured', 'json', 'text'],
                value=self.form_data['output']
            ).classes('w-full mb-4').on_value_change(lambda e: self.update_form_data('output', e.value))

            # Save to file option
            ui.checkbox('Save results to file').classes('mb-4')

            # Verbose logging
            ui.checkbox('Enable verbose logging').classes('mb-4')

    def setup_fallback_ui(self):
        """Set up a fallback UI when backend is not available."""
        with ui.column().classes('main-container'):
            ui.label('🤖 Code Chat AI').classes('text-2xl font-bold mb-4')
            ui.label('⚠️ Backend server not available').classes('text-red-600 mb-4')
            ui.label('Please ensure the FastAPI server is running on ' + self.backend_url)

    def update_form_data(self, key: str, value: str):
        """Update form data."""
        self.form_data[key] = value

    def browse_folder(self):
        """Open folder browser dialog using JavaScript."""
        # Use JavaScript to open a directory picker
        js_code = """
        async function selectFolder() {
            try {
                // Check if the File System Access API is supported
                if ('showDirectoryPicker' in window) {
                    const dirHandle = await window.showDirectoryPicker();
                    const path = dirHandle.name; // This gives us the folder name, not full path

                    // For security reasons, browsers don't expose full paths
                    // We'll show a helpful message instead
                    alert('Folder selected: ' + path + '\\n\\nNote: For security reasons, web browsers cannot access the full file path. Please manually enter the complete path in the input field above.');

                    // Try to get the folder contents to show user what was selected
                    let fileCount = 0;
                    for await (const [name, handle] of dirHandle.entries()) {
                        fileCount++;
                        if (fileCount > 10) break; // Limit to avoid too many iterations
                    }

                    alert('Selected folder contains approximately ' + fileCount + ' items.\\nPlease enter the full path manually in the input field.');
                } else {
                    // Fallback for browsers that don't support the File System Access API
                    alert('Your browser does not support the File System Access API.\\n\\nPlease manually enter the complete folder path in the input field above.\\n\\nExample:\\n- Windows: C:\\\\Users\\\\YourName\\\\Documents\\\\project\\n- Linux/Mac: /home/username/projects/myproject');
                }
            } catch (error) {
                if (error.name !== 'AbortError') {
                    alert('Error selecting folder: ' + error.message + '\\n\\nPlease manually enter the folder path in the input field above.');
                }
            }
        }
        selectFolder();
        """
        ui.run_javascript(js_code)

    def show_path_help(self):
        """Show help for entering file paths."""
        help_text = """
        📂 How to Enter File Paths:

        For security reasons, web browsers cannot directly access your local file system.
        Please manually enter the complete path to your project folder:

        🪟 Windows Examples:
        • C:\\Users\\YourName\\Documents\\myproject
        • C:\\Projects\\codebase
        • D:\\workspace\\app

        🐧 Linux/Mac Examples:
        • /home/username/projects/myapp
        • /Users/username/Documents/code
        • /workspace/project

        💡 Tips:
        • Use forward slashes (/) on all systems (they work on Windows too)
        • Make sure the folder exists and is accessible
        • The path should point to the root directory of your codebase

        🔍 You can also:
        • Copy the path from your file explorer
        • Use relative paths if running the server locally
        • Use the Browse button to see folder contents (limited browser support)
        """

        ui.notify(help_text, type="info", duration=10000)

    async def analyze_code(self):
        """Analyze the codebase using the backend API."""
        try:
            # Validate form data
            if not self.form_data['folder']:
                ui.notify("Please select a codebase folder", type="warning")
                return

            if not self.form_data['question']:
                ui.notify("Please enter an analysis question", type="warning")
                return

            # Update status
            self.status_label.text = "🔄 Analyzing codebase..."
            self.status_label.classes('status-info')
            self.analyze_button.disable()

            # Prepare request data
            request_data = {
                'folder': self.form_data['folder'],
                'question': self.form_data['question'],
                'model': self.form_data['model'],
                'provider': self.form_data['provider'],
                'include': self.form_data['include'],
                'exclude': self.form_data['exclude'],
                'output': self.form_data['output']
            }

            if self.form_data['api_key']:
                request_data['api_key'] = self.form_data['api_key']

            # Make API request
            response = await self.client.post(
                f"{self.backend_url}/analyze",
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()

                # Update status
                self.status_label.text = f"✅ Analysis completed in {result['processing_time']:.2f}s"
                self.status_label.classes('status-info status-success')

                # Show results in new tab
                self.show_results(result)

            else:
                error_detail = response.json().get('detail', 'Unknown error')
                raise Exception(f"API Error: {error_detail}")

        except Exception as e:
            error_msg = str(e)
            self.status_label.text = f"❌ Analysis failed: {error_msg}"
            self.status_label.classes('status-info status-error')
            ui.notify(f"Analysis failed: {error_msg}", type="negative")

        finally:
            self.analyze_button.enable()

    def show_results(self, result: Dict[str, Any]):
        """Display analysis results in a new browser tab."""
        # Create HTML content for results
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Code Chat AI - Analysis Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ background: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 15px; }}
                .response {{ background: #f8f9fa; padding: 15px; border-radius: 5px; white-space: pre-wrap; }}
                .copy-btn {{ background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Code Chat AI - Analysis Results</h1>
                <div class="summary">
                    <strong>📊 Analysis Summary</strong><br>
                    📁 Files: {result['files_count']} |
                    🧠 Model: {result['model']} |
                    ⏱️ Time: {result['processing_time']:.2f}s |
                    📅 {result['timestamp']}
                </div>
            </div>

            <h2>💬 AI Response</h2>
            <div class="response">{result['response']}</div>

            <br>
            <button class="copy-btn" onclick="copyToClipboard()">📋 Copy Response</button>

            <script>
                function copyToClipboard() {{
                    const responseText = `{result['response']}`;
                    navigator.clipboard.writeText(responseText).then(() => {{
                        alert('Response copied to clipboard!');
                    }});
                }}
            </script>
        </body>
        </html>
        """

        # Open results in new tab (this is a simplified approach)
        # In a real implementation, you might use JavaScript or a more sophisticated method
        escaped_content = html_content.replace('\n', '').replace('\r', '').replace("'", r"\'")
        js_command = "window.open('data:text/html," + escaped_content + "')"
        ui.run_javascript(js_command)

    def reset_form(self):
        """Reset the form to default values."""
        self.form_data = {
            'folder': '',
            'question': '',
            'model': 'gpt-3.5-turbo',
            'provider': 'openrouter',
            'include': '*.py,*.js,*.ts,*.java,*.cpp,*.c,*.h',
            'exclude': 'test_*,__pycache__,*.pyc,node_modules,venv,.venv',
            'output': 'structured',
            'api_key': ''
        }

        # Update UI elements
        if self.folder_input:
            self.folder_input.value = ''
        if self.question_input:
            self.question_input.value = ''

        self.status_label.text = "Form reset"
        self.status_label.classes('status-info status-success')

        ui.notify("Form has been reset", type="info")

# Global app instance
web_app = CodeChatWebApp()

@ui.page('/')
async def main_page():
    """Main page handler."""
    await web_app.initialize()

def main():
    """Main entry point."""
    print("🚀 Starting Code Chat AI NiceGUI Frontend")
    print(f"🌐 Frontend will be available at: http://localhost:{WEB_PORT}")
    print(f"🔗 Backend API: {FASTAPI_URL}")
    print("=" * 50)

    # Start the web server
    ui.run(
        title="Code Chat AI",
        port=WEB_PORT,
        reload=False,
        show=False  # Don't auto-open browser
    )

if __name__ == "__main__":
    main()