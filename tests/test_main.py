"""
Unit tests for main CLI module
"""
import pytest
from unittest.mock import Mock, patch, call
from pathlib import Path
import os

from invoice_processor.main import app
from typer.testing import CliRunner


class TestMainCLI:
    """Test main CLI functionality"""
    
    def setUp(self):
        self.runner = CliRunner()
    
    @pytest.fixture(autouse=True)
    def setup_runner(self):
        """Setup CLI runner for each test"""
        self.runner = CliRunner()
    
    def test_process_command_success(self, temp_dir):
        """
        Given valid directories and configuration
        When running process command
        Then processing should complete successfully
        """
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        input_dir.mkdir()
        
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.os.getenv') as mock_getenv:
            
            mock_getenv.side_effect = lambda key: "test-key" if "API_KEY" in key else None
            mock_process.return_value = "Successfully processed 5 invoices"
            
            result = self.runner.invoke(app, [
                'process',
                '--input', str(input_dir),
                '--output', str(output_dir),
                '--processed', str(processed_dir)
            ])
            
            assert result.exit_code == 0
            assert "Starting Invoice Processing" in result.stdout
            assert "Successfully processed" in result.stdout
    
    def test_process_command_with_defaults(self):
        """
        Given no custom directories specified
        When running process command
        Then default directories should be used
        """
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.Path.mkdir'), \
             patch('invoice_processor.main.os.getenv') as mock_getenv:
            
            mock_getenv.side_effect = lambda key: "test-key" if "API_KEY" in key else None
            mock_process.return_value = "Processing complete"
            
            result = self.runner.invoke(app, ['process'])
            
            assert result.exit_code == 0
            mock_process.assert_called_once_with("data/input", "data/output", "data/processed")
    
    def test_process_command_no_api_keys(self, temp_dir):
        """
        Given no API keys configured
        When running process command
        Then warning should be displayed but processing should continue
        """
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.os.getenv', return_value=None):
            
            mock_process.return_value = "Processing with OCR only"
            
            result = self.runner.invoke(app, ['process', '--input', str(input_dir)])
            
            assert result.exit_code == 0
            assert "Warning: No AI API keys found" in result.stdout
            assert "OCR extraction" in result.stdout
    
    def test_process_command_with_openai_only(self, temp_dir):
        """
        Given only OpenAI API key configured
        When running process command
        Then OpenAI should be listed as available
        """
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.os.getenv') as mock_getenv:
            
            mock_getenv.side_effect = lambda key: "openai-key" if key == "OPENAI_API_KEY" else None
            mock_process.return_value = "Processing complete"
            
            result = self.runner.invoke(app, ['process', '--input', str(input_dir)])
            
            assert result.exit_code == 0
            assert "AI providers available: OpenAI" in result.stdout
    
    def test_process_command_with_both_api_keys(self, temp_dir):
        """
        Given both API keys configured
        When running process command
        Then both providers should be listed
        """
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.os.getenv') as mock_getenv:
            
            def mock_env(key):
                if key == "OPENAI_API_KEY":
                    return "openai-key"
                elif key == "ANTHROPIC_API_KEY":
                    return "anthropic-key"
                return None
            
            mock_getenv.side_effect = mock_env
            mock_process.return_value = "Processing complete"
            
            result = self.runner.invoke(app, ['process', '--input', str(input_dir)])
            
            assert result.exit_code == 0
            assert "OpenAI, Anthropic" in result.stdout
    
    def test_process_command_creates_directories(self, temp_dir):
        """
        Given non-existent directories
        When running process command
        Then directories should be created
        """
        input_dir = temp_dir / "new_input"
        output_dir = temp_dir / "new_output"
        processed_dir = temp_dir / "new_processed"
        
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.os.getenv') as mock_getenv:
            
            mock_getenv.side_effect = lambda key: "test-key" if "API_KEY" in key else None
            mock_process.return_value = "Processing complete"
            
            result = self.runner.invoke(app, [
                'process',
                '--input', str(input_dir),
                '--output', str(output_dir),
                '--processed', str(processed_dir)
            ])
            
            assert result.exit_code == 0
            assert input_dir.exists()
            assert output_dir.exists()
            assert processed_dir.exists()
    
    def test_process_command_error_handling(self, temp_dir):
        """
        Given processing error occurs
        When running process command
        Then error should be handled gracefully
        """
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.os.getenv') as mock_getenv:
            
            mock_getenv.side_effect = lambda key: "test-key" if "API_KEY" in key else None
            mock_process.side_effect = Exception("Processing failed")
            
            result = self.runner.invoke(app, ['process', '--input', str(input_dir)])
            
            assert result.exit_code == 1
            assert "Error: Processing failed" in result.stdout
    
    def test_setup_command_creates_structure(self, temp_dir):
        """
        Given setup command
        When running setup
        Then directory structure and env file should be created
        """
        with patch('invoice_processor.main.Path.mkdir') as mock_mkdir, \
             patch('invoice_processor.main.Path.exists', return_value=False), \
             patch('invoice_processor.main.Path.write_text') as mock_write:
            
            result = self.runner.invoke(app, ['setup'])
            
            assert result.exit_code == 0
            assert "Setting up Invoice Processor" in result.stdout
            assert "Setup completed!" in result.stdout
            
            # Check directories were created
            expected_dirs = ["data/input", "data/output", "data/processed"]
            for directory in expected_dirs:
                assert directory in result.stdout
    
    def test_setup_command_env_file_exists(self, temp_dir):
        """
        Given .env file already exists
        When running setup
        Then existing .env file should not be overwritten
        """
        env_file = temp_dir / ".env"
        env_file.write_text("existing content")
        
        with patch('invoice_processor.main.Path.mkdir'), \
             patch('invoice_processor.main.Path.exists') as mock_exists:
            
            def exists_side_effect(path_arg=None):
                if path_arg is None:
                    # Called on Path object
                    return str(env_file) in str(path_arg) if hasattr(path_arg, '__str__') else False
                return False
            
            mock_exists.side_effect = lambda: True  # .env exists
            
            result = self.runner.invoke(app, ['setup'])
            
            assert result.exit_code == 0
            # Should not mention creating .env file
            assert "Created .env file" not in result.stdout
    
    def test_status_command_shows_directories(self, temp_dir):
        """
        Given status command
        When running status
        Then directory information should be displayed
        """
        # Create test directories with files
        input_dir = temp_dir / "data" / "input"
        output_dir = temp_dir / "data" / "output"
        processed_dir = temp_dir / "data" / "processed"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        
        # Add some test files
        (input_dir / "test1.pdf").write_text("test")
        (input_dir / "test2.pdf").write_text("test")
        (output_dir / "result.csv").write_text("test")
        
        with patch('invoice_processor.main.Path') as mock_path:
            # Mock Path behavior
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.glob.return_value = ["file1", "file2"]
            
            result = self.runner.invoke(app, ['status'])
            
            assert result.exit_code == 0
            assert "Invoice Processor Status" in result.stdout
            assert "Input:" in result.stdout
            assert "Output:" in result.stdout
            assert "Processed:" in result.stdout
    
    def test_status_command_shows_api_configuration(self):
        """
        Given various API key configurations
        When running status command
        Then API configuration should be displayed correctly
        """
        with patch('invoice_processor.main.os.getenv') as mock_getenv, \
             patch('invoice_processor.main.Path') as mock_path:
            
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.glob.return_value = []
            
            # Test with both API keys
            mock_getenv.side_effect = lambda key: "test-key" if "API_KEY" in key else None
            
            result = self.runner.invoke(app, ['status'])
            
            assert result.exit_code == 0
            assert "AI Configuration:" in result.stdout
            assert "OpenAI API Key: ✅" in result.stdout
            assert "Anthropic API Key: ✅" in result.stdout
    
    def test_status_command_no_api_keys(self):
        """
        Given no API keys configured
        When running status command
        Then warning about OCR-only mode should be shown
        """
        with patch('invoice_processor.main.os.getenv', return_value=None), \
             patch('invoice_processor.main.Path') as mock_path:
            
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.glob.return_value = []
            
            result = self.runner.invoke(app, ['status'])
            
            assert result.exit_code == 0
            assert "OpenAI API Key: ❌" in result.stdout
            assert "Anthropic API Key: ❌" in result.stdout
            assert "No AI providers configured" in result.stdout
    
    def test_status_command_missing_directories(self):
        """
        Given missing directories
        When running status command  
        Then missing directories should be indicated
        """
        with patch('invoice_processor.main.Path') as mock_path, \
             patch('invoice_processor.main.os.getenv', return_value=None):
            
            mock_path.return_value.exists.return_value = False
            
            result = self.runner.invoke(app, ['status'])
            
            assert result.exit_code == 0
            assert "❌ (missing)" in result.stdout


class TestMainCLIIntegration:
    """Integration tests for CLI functionality"""
    
    def setUp(self):
        self.runner = CliRunner()
    
    @pytest.fixture(autouse=True)
    def setup_runner(self):
        """Setup CLI runner for each test"""
        self.runner = CliRunner()
    
    def test_complete_workflow_through_cli(self, temp_dir):
        """
        Given complete CLI workflow
        When running setup, process, and status commands
        Then all should work together correctly
        """
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.os.getenv') as mock_getenv:
            
            mock_getenv.side_effect = lambda key: "test-key" if "API_KEY" in key else None
            mock_process.return_value = "Successfully processed 3 invoices"
            
            # Run setup
            setup_result = self.runner.invoke(app, ['setup'])
            assert setup_result.exit_code == 0
            
            # Run process
            process_result = self.runner.invoke(app, ['process'])
            assert process_result.exit_code == 0
            
            # Run status
            with patch('invoice_processor.main.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.glob.return_value = ["file1", "file2"]
                
                status_result = self.runner.invoke(app, ['status'])
                assert status_result.exit_code == 0
    
    def test_cli_with_environment_variables(self, temp_dir, monkeypatch):
        """
        Given environment variables set
        When running CLI commands
        Then environment should be properly utilized
        """
        # Set environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        with patch('invoice_processor.main.run_invoice_processing') as mock_process:
            mock_process.return_value = "Processing complete"
            
            result = self.runner.invoke(app, ['process', '--input', str(input_dir)])
            
            assert result.exit_code == 0
            assert "AI providers available: OpenAI" in result.stdout
    
    def test_cli_help_commands(self):
        """
        Given help commands
        When running --help
        Then help information should be displayed
        """
        # Test main help
        result = self.runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert "invoice-processor" in result.stdout.lower()
        
        # Test process command help
        result = self.runner.invoke(app, ['process', '--help'])
        assert result.exit_code == 0
        assert "Process invoices" in result.stdout
        
        # Test setup command help
        result = self.runner.invoke(app, ['setup', '--help'])
        assert result.exit_code == 0
        assert "Setup the invoice processing environment" in result.stdout
        
        # Test status command help
        result = self.runner.invoke(app, ['status', '--help'])
        assert result.exit_code == 0
        assert "Check system status" in result.stdout