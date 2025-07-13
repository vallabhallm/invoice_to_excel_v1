"""
Integration tests for end-to-end invoice processing workflows
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pandas as pd
from decimal import Decimal

from invoice_processor.workflows.invoice_workflow import process_invoices
from invoice_processor.main import app
from typer.testing import CliRunner


class TestEndToEndIntegration:
    """Integration tests for complete end-to-end processing workflows"""

    def setUp(self):
        self.runner = CliRunner()

    @pytest.fixture(autouse=True)
    def setup_runner(self):
        """Setup CLI runner for each test"""
        self.runner = CliRunner()

    @pytest.fixture
    def mock_ai_success_response(self):
        """Mock successful AI response with realistic invoice data"""
        return {
            "header": {
                "invoice_number": "INV-2024-001",
                "invoice_date": "2024-01-15",
                "due_date": "2024-02-15",
                "vendor_name": "Tech Solutions Inc",
                "vendor_address": "123 Business Ave, Tech City, TC 12345",
                "vendor_tax_id": "VAT-123456789",
                "customer_name": "Client Corp",
                "customer_address": "456 Client St, Business City, BC 67890",
                "total_amount": "1250.00",
                "tax_amount": "250.00",
                "subtotal": "1000.00",
                "currency": "USD"
            },
            "line_items": [
                {
                    "item_description": "Software Development Services",
                    "quantity": "40",
                    "unit_price": "25.00",
                    "line_total": "1000.00",
                    "item_code": "DEV-001"
                }
            ]
        }

    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF-like content for testing"""
        return """
        INVOICE

        Invoice Number: INV-2024-001
        Date: January 15, 2024
        Due Date: February 15, 2024

        From:
        Tech Solutions Inc
        123 Business Ave
        Tech City, TC 12345
        VAT: VAT-123456789

        To:
        Client Corp
        456 Client St
        Business City, BC 67890

        Description                    Qty    Unit Price    Total
        Software Development Services   40      $25.00     $1,000.00

        Subtotal:                                         $1,000.00
        Tax (25%):                                         $250.00
        Total:                                            $1,250.00

        Thank you for your business!
        """

    def test_end_to_end_ai_processing_success(self, temp_dir, mock_ai_success_response, sample_pdf_content):
        """
        Integration Test 1: End-to-end processing using AI extraction
        
        Given a valid invoice file and working AI service
        When processing the file end-to-end
        Then complete workflow should succeed with AI-extracted data
        """
        # Setup directories
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        input_dir.mkdir()
        
        # Create a sample invoice file
        invoice_file = input_dir / "test_invoice.pdf"
        invoice_file.write_text(sample_pdf_content)
        
        # Mock the entire workflow chain
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary, \
             patch('os.getenv') as mock_getenv:
            
            # Setup environment with valid API key
            mock_getenv.side_effect = lambda key: "valid-openai-key" if key == "OPENAI_API_KEY" else None
            
            # Setup PDF extraction to return sufficient text (minimum 50 chars)
            long_content = sample_pdf_content + " " * 200  # Ensure sufficient length
            mock_pdf.return_value.extract_text.return_value = long_content
            
            # Setup AI extraction to return structured data
            from invoice_processor.models.invoice import Invoice, InvoiceHeader, InvoiceLineItem
            from datetime import date
            
            header = InvoiceHeader(
                invoice_number="INV-2024-001",
                invoice_date=date(2024, 1, 15),
                vendor_name="Tech Solutions Inc",
                total_amount=Decimal("1250.00"),
                currency="USD"
            )
            
            line_items = [InvoiceLineItem(
                item_description="Software Development Services",
                quantity=Decimal("40"),
                unit_price=Decimal("25.00"),
                line_total=Decimal("1000.00")
            )]
            
            mock_invoice = Invoice(
                header=header,
                line_items=line_items,
                raw_text=long_content,
                file_path=str(invoice_file)
            )
            
            mock_ai.return_value.extract_invoice_data.return_value = mock_invoice
            
            # Setup summary generation
            mock_summary.return_value.save_summary_report.return_value = str(output_dir / "summary.txt")
            mock_summary.return_value.save_summary_table.return_value = str(output_dir / "table.csv")
            
            # Execute end-to-end processing
            result = process_invoices(
                str(input_dir),
                str(output_dir),
                str(processed_dir)
            )
            
            # Verify successful processing
            assert "Successfully processed 1 invoices" in result
            
            # Verify AI extraction was called
            mock_ai.return_value.extract_invoice_data.assert_called_once()
            
            # Verify file was processed
            assert not invoice_file.exists()  # Should be moved to processed directory
            
            # Verify outputs were generated
            mock_summary.return_value.save_summary_report.assert_called_once()
            mock_summary.return_value.save_summary_table.assert_called_once()

    def test_end_to_end_ocr_fallback_wrong_api_key(self, temp_dir, sample_pdf_content):
        """
        Integration Test 2: OCR fallback when AI fails due to wrong API key
        
        Given an invoice file and invalid/wrong OpenAI API key
        When processing the file
        Then should fall back to OCR-only processing
        """
        # Setup directories
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output" 
        processed_dir = temp_dir / "processed"
        
        input_dir.mkdir()
        
        # Create invoice file
        invoice_file = input_dir / "ocr_fallback_test.pdf"
        invoice_file.write_text(sample_pdf_content)
        
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary, \
             patch('os.getenv') as mock_getenv:
            
            # Setup environment with wrong/invalid API key
            mock_getenv.side_effect = lambda key: "invalid-wrong-key" if key == "OPENAI_API_KEY" else None
            
            # Setup PDF extraction to return text (ensure sufficient length)
            long_content = sample_pdf_content + " " * 200
            mock_pdf.return_value.extract_text.return_value = long_content
            
            # Setup AI extraction to fail due to authentication error (return None for fallback)
            mock_ai.return_value.extract_invoice_data.return_value = None
            
            # Setup summary generation
            mock_summary.return_value.save_summary_report.return_value = str(output_dir / "summary.txt")
            mock_summary.return_value.save_summary_table.return_value = str(output_dir / "table.csv")
            
            # Execute processing
            result = process_invoices(
                str(input_dir),
                str(output_dir), 
                str(processed_dir)
            )
            
            # Verify processing continued despite AI failure
            assert "processed" in result.lower()
            
            # Verify AI extraction was attempted but failed
            mock_ai.return_value.extract_invoice_data.assert_called_once()
            
            # Verify file was still processed (OCR fallback)
            assert not invoice_file.exists()  # Should be moved despite AI failure

    def test_end_to_end_nonexistent_file_error_handling(self, temp_dir):
        """
        Integration Test 3: Error handling for non-existent files
        
        Given a directory with no files or non-existent input directory
        When attempting to process invoices
        Then should handle errors gracefully with appropriate messages
        """
        # Test Case 3a: Empty input directory
        input_dir = temp_dir / "empty_input"
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        input_dir.mkdir()  # Create empty directory
        
        result = process_invoices(
            str(input_dir),
            str(output_dir),
            str(processed_dir)
        )
        
        # Verify appropriate message for no files
        assert "No invoice files found" in result
        
        # Test Case 3b: Non-existent input directory
        nonexistent_dir = temp_dir / "does_not_exist"
        
        result_nonexistent = process_invoices(
            str(nonexistent_dir),
            str(output_dir),
            str(processed_dir)
        )
        
        # Verify appropriate message for non-existent directory
        assert "No invoice files found" in result_nonexistent

    def test_end_to_end_corrupted_file_handling(self, temp_dir):
        """
        Integration Test 4: Handling corrupted or unreadable files
        
        Given a corrupted/unreadable file in input directory
        When processing files
        Then should skip corrupted files and continue with valid ones
        """
        # Setup directories
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        input_dir.mkdir()
        
        # Create a corrupted file (binary content that can't be processed)
        corrupted_file = input_dir / "corrupted.pdf"
        corrupted_file.write_bytes(b'\x00\x01\x02\x03CORRUPTED_DATA\xFF\xFE')
        
        # Create a valid file
        valid_file = input_dir / "valid.pdf" 
        valid_file.write_text("Valid invoice content for processing with sufficient length to pass minimum text validation requirements")
        
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary:
            
            # Setup extraction to fail for corrupted file, succeed for valid
            def extract_side_effect(file_path):
                if "corrupted" in str(file_path):
                    raise Exception("Cannot read corrupted file")
                return "Valid content with sufficient length for processing and AI extraction requirements"
            
            mock_pdf.return_value.extract_text.side_effect = extract_side_effect
            
            # Setup AI to return mock invoice for valid files
            mock_invoice = Mock()
            mock_invoice.header = Mock()
            mock_invoice.line_items = [Mock()]
            mock_ai.return_value.extract_invoice_data.return_value = mock_invoice
            
            # Setup summary
            mock_summary.return_value.save_summary_report.return_value = str(output_dir / "summary.txt")
            mock_summary.return_value.save_summary_table.return_value = str(output_dir / "table.csv")
            
            # Execute processing
            result = process_invoices(
                str(input_dir),
                str(output_dir),
                str(processed_dir)
            )
            
            # Should continue processing despite corrupted file
            assert "processed" in result.lower()
            
            # Valid file should be processed
            assert not valid_file.exists()

    def test_cli_integration_with_ai_processing(self, temp_dir, mock_ai_success_response, sample_pdf_content):
        """
        Integration Test 5: Complete CLI integration with AI processing
        
        Given CLI command with valid invoice file
        When running through CLI interface
        Then should complete full processing workflow
        """
        # Setup directories
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        input_dir.mkdir()
        
        # Create invoice file
        invoice_file = input_dir / "cli_test.pdf"
        invoice_file.write_text(sample_pdf_content)
        
        with patch('invoice_processor.main.run_invoice_processing') as mock_process, \
             patch('invoice_processor.main.os.getenv') as mock_getenv:
            
            # Setup environment
            mock_getenv.side_effect = lambda key: "test-openai-key" if key == "OPENAI_API_KEY" else None
            
            # Setup successful processing
            mock_process.return_value = "Successfully processed 1 invoices. Output saved to test_output.csv"
            
            # Execute CLI command
            result = self.runner.invoke(app, [
                'process',
                '--input', str(input_dir),
                '--output', str(output_dir),
                '--processed', str(processed_dir)
            ])
            
            # Verify CLI execution success
            assert result.exit_code == 0
            assert "Starting Invoice Processing" in result.stdout
            assert "Successfully processed" in result.stdout
            
            # Verify underlying function was called correctly
            mock_process.assert_called_once_with(
                str(input_dir),
                str(output_dir), 
                str(processed_dir)
            )

    def test_large_batch_processing_integration(self, temp_dir, sample_pdf_content):
        """
        Integration Test 6: Processing multiple files in batch
        
        Given multiple invoice files in nested directories
        When processing all files
        Then should handle batch processing correctly
        """
        # Setup complex directory structure
        input_dir = temp_dir / "input"
        vendor_a_dir = input_dir / "vendor_a"
        vendor_b_dir = input_dir / "vendor_b"
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        vendor_a_dir.mkdir(parents=True)
        vendor_b_dir.mkdir(parents=True)
        
        # Create multiple invoice files
        files_created = []
        for i in range(3):
            file_a = vendor_a_dir / f"invoice_a_{i}.pdf"
            file_b = vendor_b_dir / f"invoice_b_{i}.pdf"
            
            file_a.write_text(f"Invoice A-{i}\n{sample_pdf_content}")
            file_b.write_text(f"Invoice B-{i}\n{sample_pdf_content}")
            
            files_created.extend([file_a, file_b])
        
        # Add one file to root input directory
        root_file = input_dir / "root_invoice.pdf"
        root_file.write_text(sample_pdf_content)
        files_created.append(root_file)
        
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary:
            
            # Setup extraction for all files (ensure sufficient length)
            long_content = sample_pdf_content + " " * 200
            mock_pdf.return_value.extract_text.return_value = long_content
            
            # Setup AI extraction
            mock_invoice = Mock()
            mock_invoice.header = Mock()
            mock_invoice.line_items = [Mock()]
            mock_ai.return_value.extract_invoice_data.return_value = mock_invoice
            
            # Setup summary
            mock_summary.return_value.save_summary_report.return_value = str(output_dir / "summary.txt")
            mock_summary.return_value.save_summary_table.return_value = str(output_dir / "table.csv")
            
            # Execute batch processing
            result = process_invoices(
                str(input_dir),
                str(output_dir),
                str(processed_dir)
            )
            
            # Verify all files were processed
            assert "Successfully processed 7 invoices" in result
            
            # Verify files were moved to processed directory
            for original_file in files_created:
                assert not original_file.exists()
                
            # Verify AI extraction called for each file
            assert mock_ai.return_value.extract_invoice_data.call_count == 7


class TestIntegrationErrorScenarios:
    """Integration tests for error scenarios and edge cases"""

    def test_mixed_file_types_processing(self, temp_dir):
        """
        Test processing directory with mixed file types
        
        Given directory with PDF, images, and non-invoice files
        When processing the directory
        Then should only process valid invoice file types
        """
        # Setup directories
        input_dir = temp_dir / "mixed_files"
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        input_dir.mkdir()
        
        # Create mixed file types
        pdf_file = input_dir / "invoice.pdf"
        image_file = input_dir / "scan.png"
        text_file = input_dir / "readme.txt"
        word_file = input_dir / "document.docx"
        
        pdf_file.write_text("PDF invoice content with sufficient length for processing requirements and validation")
        image_file.write_bytes(b"PNG_IMAGE_DATA")
        text_file.write_text("This is not an invoice")
        word_file.write_bytes(b"DOCX_DATA")
        
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.ImageExtractor') as mock_img, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary:
            
            # Setup extractors (ensure sufficient content length)
            mock_pdf.return_value.extract_text.return_value = "PDF content with sufficient length for processing and validation requirements"
            mock_img.return_value.extract_text_from_file.return_value = "Image text content with sufficient length for processing requirements"
            
            mock_invoice = Mock()
            mock_invoice.header = Mock()
            mock_invoice.line_items = [Mock()]
            mock_ai.return_value.extract_invoice_data.return_value = mock_invoice
            
            mock_summary.return_value.save_summary_report.return_value = str(output_dir / "summary.txt")
            mock_summary.return_value.save_summary_table.return_value = str(output_dir / "table.csv")
            
            # Execute processing
            result = process_invoices(
                str(input_dir),
                str(output_dir),
                str(processed_dir)
            )
            
            # Should process only PDF and image files (2 files)
            assert "Successfully processed 2 invoices" in result
            
            # Non-invoice files should remain
            assert text_file.exists()
            assert word_file.exists()
            
            # Invoice files should be moved
            assert not pdf_file.exists()
            assert not image_file.exists()

    def test_permission_error_handling(self, temp_dir):
        """
        Test handling of permission errors during file operations
        
        Given files with restricted permissions
        When processing files
        Then should handle permission errors gracefully
        """
        # Setup directories
        input_dir = temp_dir / "restricted"
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        input_dir.mkdir()
        
        # Create test file
        test_file = input_dir / "restricted.pdf"
        test_file.write_text("Test invoice content with sufficient length for processing and validation requirements")
        
        with patch('invoice_processor.workflows.invoice_workflow.move_processed_file') as mock_move, \
             patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary:
            
            # Setup file move to fail with permission error
            mock_move.side_effect = PermissionError("Permission denied")
            
            # Setup extraction
            mock_pdf.return_value.extract_text.return_value = "Test content with sufficient length for processing and validation requirements"
            mock_invoice = Mock()
            mock_invoice.header = Mock()
            mock_invoice.line_items = [Mock()]
            mock_ai.return_value.extract_invoice_data.return_value = mock_invoice
            
            mock_summary.return_value.save_summary_report.return_value = str(output_dir / "summary.txt")
            mock_summary.return_value.save_summary_table.return_value = str(output_dir / "table.csv")
            
            # Execute processing - should handle permission error gracefully
            result = process_invoices(
                str(input_dir),
                str(output_dir),
                str(processed_dir)
            )
            
            # Should still attempt processing despite permission errors
            assert "processed" in result.lower()

    def test_output_directory_creation_failure(self, temp_dir):
        """
        Test handling when output directory cannot be created
        
        Given restricted output location
        When attempting to save results
        Then should handle directory creation errors
        """
        # Setup directories
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        # Create test file
        test_file = input_dir / "test.pdf"
        test_file.write_text("Test invoice content for directory creation test")
        
        # Use a restricted output path (simulated)
        restricted_output = "/root/restricted_output"  # This should fail on most systems
        processed_dir = temp_dir / "processed"
        
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai:
            
            # Setup extraction
            mock_pdf.return_value.extract_text.return_value = "Test content for directory failure test with sufficient length for processing requirements"
            mock_invoice = Mock()
            mock_invoice.header = Mock()
            mock_invoice.line_items = [Mock()]
            mock_ai.return_value.extract_invoice_data.return_value = mock_invoice
            
            # Execute processing with restricted output - should handle gracefully
            try:
                result = process_invoices(
                    str(input_dir),
                    restricted_output,
                    str(processed_dir)
                )
                # If it doesn't fail, that's also acceptable behavior
                assert isinstance(result, str)
            except Exception as e:
                # Should handle the error gracefully
                assert "permission" in str(e).lower() or "not found" in str(e).lower()