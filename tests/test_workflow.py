"""
Unit tests for workflow functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from invoice_processor.workflows.invoice_workflow import (
    extract_text_from_file, extract_invoice_structure, flatten_invoice_data,
    save_results_to_csv, process_invoices
)
from invoice_processor.models.invoice import Invoice, InvoiceHeader, InvoiceLineItem


class TestExtractTextFromFile:
    """Test text extraction workflow function"""
    
    def test_extract_text_from_pdf_success(self, sample_pdf_file):
        """
        Given a PDF file with extractable text
        When extracting text from file
        Then text should be returned
        """
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf:
            mock_pdf.return_value.extract_text.return_value = "PDF text content"
            
            result = extract_text_from_file(sample_pdf_file)
            
            assert result == "PDF text content"
    
    def test_extract_text_from_pdf_with_ocr_fallback(self, sample_pdf_file):
        """
        Given a PDF with no extractable text
        When extracting text from file
        Then OCR should be used as fallback
        """
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.ImageExtractor') as mock_image:
            
            # PDF extraction returns insufficient text
            mock_pdf.return_value.extract_text.return_value = "x"  # Less than 50 chars
            mock_pdf.return_value.convert_to_images.return_value = [Mock(), Mock()]
            mock_image.return_value.extract_text_from_image.return_value = "OCR page text"
            
            result = extract_text_from_file(sample_pdf_file)
            
            assert "Page 1:" in result
            assert "OCR page text" in result
    
    def test_extract_text_from_image_file(self, sample_image_file):
        """
        Given an image file
        When extracting text from file
        Then image extractor should be used
        """
        with patch('invoice_processor.workflows.invoice_workflow.ImageExtractor') as mock_image:
            mock_image.return_value.extract_text_from_file.return_value = "Image text"
            
            result = extract_text_from_file(sample_image_file)
            
            assert result == "Image text"
    
    def test_extract_text_from_file_error(self, sample_pdf_file):
        """
        Given extraction error
        When extracting text from file
        Then None should be returned
        """
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf:
            mock_pdf.return_value.extract_text.side_effect = Exception("Extraction error")
            
            result = extract_text_from_file(sample_pdf_file)
            
            assert result is None


class TestExtractInvoiceStructure:
    """Test invoice structure extraction"""
    
    def test_extract_structure_ai_success(self, sample_invoice):
        """
        Given valid text and working AI
        When extracting invoice structure
        Then structured invoice should be returned
        """
        with patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai:
            mock_ai.return_value.extract_invoice_data.return_value = sample_invoice
            
            result = extract_invoice_structure("Valid invoice text content for AI extraction testing with sufficient length", "test.pdf")
            
            assert result == sample_invoice
    
    def test_extract_structure_ai_failure_fallback(self):
        """
        Given AI extraction fails
        When extracting invoice structure
        Then basic structure should be created
        """
        with patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.Path') as mock_path:
            
            mock_ai.return_value.extract_invoice_data.return_value = None
            mock_path.return_value.stem = "test_file"
            
            result = extract_invoice_structure("Some text content with sufficient length for processing", "test_file.pdf")
            
            assert result is not None
            assert result.header.invoice_number == "test_file"
            assert result.header.vendor_name == "Unknown (OCR only)"
            assert len(result.line_items) == 1
            assert "AI extraction failed" in result.line_items[0].item_description
    
    def test_extract_structure_insufficient_text(self):
        """
        Given insufficient text content
        When extracting invoice structure
        Then None should be returned
        """
        result = extract_invoice_structure("x", "test.pdf")  # Too short
        
        assert result is None
    
    def test_extract_structure_no_text(self):
        """
        Given no text content
        When extracting invoice structure
        Then None should be returned
        """
        result = extract_invoice_structure(None, "test.pdf")
        
        assert result is None


class TestFlattenInvoiceData:
    """Test invoice data flattening"""
    
    def test_flatten_with_multiple_line_items(self, sample_invoice):
        """
        Given invoice with multiple line items
        When flattening data
        Then multiple flat records should be created
        """
        result = flatten_invoice_data(sample_invoice)
        
        assert len(result) == 2  # Two line items
        
        # Check that header data is repeated
        for record in result:
            assert record.invoice_number == sample_invoice.header.invoice_number
            assert record.vendor_name == sample_invoice.header.vendor_name
            assert record.total_amount == sample_invoice.header.total_amount
        
        # Check line item data is different
        assert result[0].item_description != result[1].item_description
    
    def test_flatten_with_no_line_items(self, empty_line_items_invoice):
        """
        Given invoice with no line items
        When flattening data
        Then single record with "No line items found" should be created
        """
        result = flatten_invoice_data(empty_line_items_invoice)
        
        assert len(result) == 1
        assert result[0].item_description == "No line items found"
        assert result[0].quantity is None
        assert result[0].unit_price is None
    
    def test_flatten_adds_processing_timestamp(self, sample_invoice):
        """
        Given any invoice
        When flattening data
        Then processing timestamp should be added
        """
        with patch('invoice_processor.workflows.invoice_workflow.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
            
            result = flatten_invoice_data(sample_invoice)
            
            assert all(record.processing_timestamp == "2024-01-01T12:00:00" for record in result)


class TestSaveResultsToCSV:
    """Test CSV saving functionality"""
    
    def test_save_results_success(self, sample_flat_records, temp_dir):
        """
        Given flat records and output file path
        When saving to CSV
        Then CSV file should be created with correct data
        """
        output_file = temp_dir / "test_output.csv"
        
        with patch('invoice_processor.workflows.invoice_workflow.pd.DataFrame') as mock_df:
            mock_df.return_value.to_csv = Mock()
            
            result = save_results_to_csv(sample_flat_records, output_file)
            
            assert "Successfully saved" in result
            assert str(len(sample_flat_records)) in result
    
    def test_save_results_empty_records(self, temp_dir):
        """
        Given empty records list
        When saving to CSV
        Then appropriate message should be returned
        """
        output_file = temp_dir / "empty_output.csv"
        
        result = save_results_to_csv([], output_file)
        
        assert result == "No records processed"
    
    def test_save_results_creates_directory(self, temp_dir):
        """
        Given output file in non-existent directory
        When saving to CSV
        Then directory should be created
        """
        output_file = temp_dir / "new_dir" / "output.csv"
        
        with patch('invoice_processor.workflows.invoice_workflow.pd.DataFrame') as mock_df:
            mock_df.return_value.to_csv = Mock()
            
            save_results_to_csv([Mock()], output_file)
            
            assert output_file.parent.exists()


class TestProcessInvoices:
    """Test main processing workflow"""
    
    def test_process_invoices_success_flow(self, input_directory_structure, temp_dir):
        """
        Given input directory with files
        When processing invoices
        Then complete workflow should execute successfully
        """
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        with patch('invoice_processor.workflows.invoice_workflow.extract_text_from_file') as mock_extract, \
             patch('invoice_processor.workflows.invoice_workflow.extract_invoice_structure') as mock_structure, \
             patch('invoice_processor.workflows.invoice_workflow.flatten_invoice_data') as mock_flatten, \
             patch('invoice_processor.workflows.invoice_workflow.save_results_to_csv') as mock_save, \
             patch('invoice_processor.workflows.invoice_workflow.move_processed_file') as mock_move, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary:
            
            # Setup mocks
            mock_extract.return_value = "Extracted text"
            mock_structure.return_value = Mock()
            mock_flatten.return_value = [Mock()]
            mock_save.return_value = "CSV saved"
            mock_move.return_value = Mock()
            mock_summary.return_value.save_summary_report.return_value = "summary.txt"
            mock_summary.return_value.save_summary_table.return_value = "table.csv"
            
            result = process_invoices(
                str(input_directory_structure),
                str(output_dir),
                str(processed_dir)
            )
            
            assert "Successfully processed" in result
            assert "invoices" in result
    
    def test_process_invoices_no_files(self, temp_dir):
        """
        Given empty input directory
        When processing invoices
        Then appropriate message should be returned
        """
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        result = process_invoices(str(empty_dir), str(temp_dir), str(temp_dir))
        
        assert "No invoice files found" in result
    
    def test_process_invoices_handles_individual_failures(self, input_directory_structure, temp_dir):
        """
        Given some files fail processing
        When processing invoices
        Then workflow should continue with successful files
        """
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        with patch('invoice_processor.workflows.invoice_workflow.extract_text_from_file') as mock_extract, \
             patch('invoice_processor.workflows.invoice_workflow.extract_invoice_structure') as mock_structure, \
             patch('invoice_processor.workflows.invoice_workflow.flatten_invoice_data') as mock_flatten, \
             patch('invoice_processor.workflows.invoice_workflow.save_results_to_csv') as mock_save, \
             patch('invoice_processor.workflows.invoice_workflow.move_processed_file') as mock_move, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary:
            
            # Make some extractions fail, some succeed
            mock_extract.side_effect = ["Text 1", None, "Text 3", Exception("Error")]
            mock_structure.return_value = Mock()
            mock_flatten.return_value = [Mock()]
            mock_save.return_value = "CSV saved"
            mock_move.return_value = Mock()
            mock_summary.return_value.save_summary_report.return_value = "summary.txt"
            mock_summary.return_value.save_summary_table.return_value = "table.csv"
            
            result = process_invoices(
                str(input_directory_structure),
                str(output_dir),
                str(processed_dir)
            )
            
            # Should process some files successfully despite failures
            assert "processed" in result.lower()
    
    def test_process_invoices_no_successful_extractions(self, input_directory_structure, temp_dir):
        """
        Given all files fail extraction
        When processing invoices
        Then appropriate failure message should be returned
        """
        with patch('invoice_processor.workflows.invoice_workflow.extract_text_from_file', return_value=None):
            
            result = process_invoices(
                str(input_directory_structure),
                str(temp_dir),
                str(temp_dir)
            )
            
            assert "No invoices were successfully processed" in result


class TestWorkflowIntegration:
    """Integration tests for workflow components"""
    
    def test_end_to_end_processing_simulation(self, temp_dir):
        """
        Given complete workflow setup
        When processing through all stages
        Then data should flow correctly through pipeline
        """
        # Create test input
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        test_file = input_dir / "test.pdf"
        test_file.write_text("Test content")
        
        output_dir = temp_dir / "output"
        processed_dir = temp_dir / "processed"
        
        # Mock the workflow stages
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary:
            
            # Setup extraction
            mock_pdf.return_value.extract_text.return_value = "Invoice text content"
            
            # Setup AI extraction
            mock_invoice = Mock()
            mock_invoice.header = Mock()
            mock_invoice.header.invoice_number = "TEST-001"
            mock_invoice.line_items = [Mock()]
            mock_ai.return_value.extract_invoice_data.return_value = mock_invoice
            
            # Setup summary
            mock_summary.return_value.save_summary_report.return_value = "summary.txt"
            mock_summary.return_value.save_summary_table.return_value = "table.csv"
            
            result = process_invoices(str(input_dir), str(output_dir), str(processed_dir))
            
            assert "Successfully processed" in result
    
    def test_workflow_with_different_file_types(self, temp_dir):
        """
        Given mixed file types in input
        When processing workflow
        Then appropriate extractors should be used for each type
        """
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        # Create different file types
        (input_dir / "invoice.pdf").write_text("PDF content")
        (input_dir / "scan.png").write_text("PNG content")
        
        with patch('invoice_processor.workflows.invoice_workflow.PDFExtractor') as mock_pdf, \
             patch('invoice_processor.workflows.invoice_workflow.ImageExtractor') as mock_img, \
             patch('invoice_processor.workflows.invoice_workflow.AIExtractor') as mock_ai, \
             patch('invoice_processor.workflows.invoice_workflow.InvoiceSummaryGenerator') as mock_summary:
            
            mock_pdf.return_value.extract_text.return_value = "PDF text"
            mock_img.return_value.extract_text_from_file.return_value = "Image text"
            mock_ai.return_value.extract_invoice_data.return_value = Mock()
            mock_summary.return_value.save_summary_report.return_value = "summary.txt"
            mock_summary.return_value.save_summary_table.return_value = "table.csv"
            
            process_invoices(str(input_dir), str(temp_dir), str(temp_dir))
            
            # Verify both extractors were used
            mock_pdf.assert_called()
            mock_img.assert_called()