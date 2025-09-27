"""
Tests for Mermaid rendering helper functions.

These tests cover the individual rendering methods and edge cases.
"""

import pytest
import tempfile
import subprocess
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import (
    _render_with_mermaid_cli, 
    _render_with_puppeteer, 
    _render_with_python_mermaid,
    _create_simple_flowchart_svg
)


class TestMermaidCLIRendering:
    """Test mermaid-cli rendering method."""
    
    @patch('api.subprocess.run')
    def test_mermaid_cli_success(self, mock_run):
        """Test successful mermaid-cli rendering."""
        # Mock version check success
        mock_run.side_effect = [
            Mock(returncode=0, stdout="@mermaid-js/mermaid-cli: 10.0.0"),  # version check
            Mock(returncode=0, stdout="", stderr="")  # render command
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mermaid_file = temp_path / "test.mmd"
            output_file = temp_path / "test.png"
            
            # Create test files
            mermaid_file.write_text("graph TD\nA --> B")
            output_file.write_bytes(b"fake_png_data")
            
            success, result = _render_with_mermaid_cli(mermaid_file, output_file)
            
            assert success is True
            assert "data:image/png;base64," in result
    
    @patch('api.subprocess.run')
    def test_mermaid_cli_not_installed(self, mock_run):
        """Test mermaid-cli not installed."""
        # Mock version check failure
        mock_run.return_value = Mock(returncode=1, stderr="command not found")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mermaid_file = temp_path / "test.mmd"
            output_file = temp_path / "test.png"
            
            success, result = _render_with_mermaid_cli(mermaid_file, output_file)
            
            assert success is False
            assert result == ""
    
    @patch('api.subprocess.run')
    def test_mermaid_cli_render_failure(self, mock_run):
        """Test mermaid-cli render command failure."""
        # Mock version check success, render failure
        mock_run.side_effect = [
            Mock(returncode=0, stdout="@mermaid-js/mermaid-cli: 10.0.0"),  # version check
            Mock(returncode=1, stderr="Render failed")  # render command failure
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mermaid_file = temp_path / "test.mmd"
            output_file = temp_path / "test.png"
            
            success, result = _render_with_mermaid_cli(mermaid_file, output_file)
            
            assert success is False
            assert result == ""
    
    @patch('api.subprocess.run')
    def test_mermaid_cli_timeout(self, mock_run):
        """Test mermaid-cli timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("mmdc", 30)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mermaid_file = temp_path / "test.mmd"
            output_file = temp_path / "test.png"
            
            success, result = _render_with_mermaid_cli(mermaid_file, output_file)
            
            assert success is False
            assert result == ""


class TestPuppeteerRendering:
    """Test Puppeteer rendering method."""
    
    @patch('api.subprocess.run')
    def test_puppeteer_success(self, mock_run):
        """Test successful Puppeteer rendering."""
        mock_run.return_value = Mock(returncode=0, stdout="SUCCESS", stderr="")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / "test.png"
            
            # Create fake output file
            output_file.write_bytes(b"fake_puppeteer_png")
            
            success, result = _render_with_puppeteer("graph TD\nA --> B", output_file)
            
            assert success is True
            assert "data:image/png;base64," in result
    
    @patch('api.subprocess.run')
    def test_puppeteer_failure(self, mock_run):
        """Test Puppeteer rendering failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Node.js error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / "test.png"
            
            success, result = _render_with_puppeteer("invalid mermaid", output_file)
            
            assert success is False
            assert result == ""
    
    @patch('api.subprocess.run')
    def test_puppeteer_file_not_created(self, mock_run):
        """Test Puppeteer when output file is not created."""
        mock_run.return_value = Mock(returncode=0, stdout="SUCCESS", stderr="")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / "test.png"
            # Don't create the output file
            
            success, result = _render_with_puppeteer("graph TD\nA --> B", output_file)
            
            assert success is False
            assert result == ""


class TestPythonMermaidRendering:
    """Test Python mermaid rendering method."""
    
    def test_python_mermaid_flowchart(self):
        """Test Python mermaid rendering for flowcharts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / "test.svg"
            
            success, result = _render_with_python_mermaid("graph TD\nA --> B", output_file)
            
            # Should succeed with basic flowchart
            assert success is True
            assert "data:image/svg+xml;base64," in result
    
    def test_python_mermaid_non_flowchart(self):
        """Test Python mermaid rendering for non-flowchart diagrams."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / "test.svg"
            
            success, result = _render_with_python_mermaid("sequenceDiagram\nA->>B: Hello", output_file)
            
            # Should fail for non-flowchart diagrams
            assert success is False
            assert result == ""
    
    def test_python_mermaid_with_cairosvg(self):
        """Test Python mermaid rendering with cairosvg conversion."""
        # Mock cairosvg import and functionality
        mock_cairosvg = Mock()
        mock_cairosvg.svg2png.return_value = b"fake_png_data"
        
        with patch.dict('sys.modules', {'cairosvg': mock_cairosvg}):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                output_file = temp_path / "test.png"
                
                success, result = _render_with_python_mermaid("flowchart TD\nA --> B", output_file)
                
                assert success is True
                assert "data:image/png;base64," in result
                mock_cairosvg.svg2png.assert_called_once()


class TestSimpleFlowchartSVG:
    """Test simple flowchart SVG generation."""
    
    def test_create_simple_flowchart_svg(self):
        """Test SVG flowchart creation."""
        mermaid_code = "graph TD\nA --> B\nB --> C"
        
        svg_content = _create_simple_flowchart_svg(mermaid_code)
        
        assert svg_content.startswith('<svg')
        assert '</svg>' in svg_content
        assert 'Start' in svg_content
        assert 'Process' in svg_content
        assert 'End' in svg_content
        assert 'WhisperCode' in svg_content
    
    def test_create_simple_flowchart_svg_empty(self):
        """Test SVG flowchart creation with empty input."""
        svg_content = _create_simple_flowchart_svg("")
        
        # Should still create basic SVG
        assert svg_content.startswith('<svg')
        assert '</svg>' in svg_content
    
    def test_create_simple_flowchart_svg_invalid(self):
        """Test SVG flowchart creation with invalid input."""
        svg_content = _create_simple_flowchart_svg("invalid syntax")
        
        # Should handle gracefully and create basic SVG
        assert svg_content.startswith('<svg')
        assert '</svg>' in svg_content


class TestMermaidHelperEdgeCases:
    """Test edge cases for Mermaid helper functions."""
    
    def test_render_with_mermaid_cli_file_not_found(self):
        """Test mermaid-cli with non-existent files."""
        non_existent_input = Path("/non/existent/input.mmd")
        non_existent_output = Path("/non/existent/output.png")
        
        success, result = _render_with_mermaid_cli(non_existent_input, non_existent_output)
        
        assert success is False
        assert result == ""
    
    @patch('api.subprocess.run')
    def test_puppeteer_exception_handling(self, mock_run):
        """Test Puppeteer exception handling."""
        mock_run.side_effect = Exception("Unexpected error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / "test.png"
            
            success, result = _render_with_puppeteer("graph TD\nA --> B", output_file)
            
            assert success is False
            assert result == ""
    
    def test_python_mermaid_exception_handling(self):
        """Test Python mermaid exception handling."""
        # Use invalid output path to trigger exception
        invalid_output = Path("/invalid/path/output.svg")
        
        # The function should still succeed because it creates SVG even with invalid path
        # since it doesn't actually write to the file for SVG output
        success, result = _render_with_python_mermaid("graph TD\nA --> B", invalid_output)
        
        # Should succeed and return SVG data URL
        assert success is True
        assert "data:image/svg+xml;base64," in result
    
    def test_create_simple_flowchart_svg_exception(self):
        """Test SVG creation exception handling."""
        # This should not raise an exception even with problematic input
        result = _create_simple_flowchart_svg(None)
        
        # Should return empty string on exception
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])