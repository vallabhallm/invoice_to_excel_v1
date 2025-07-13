"""
Unit tests for summary generation functionality
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime
import pandas as pd

from invoice_processor.utils.summary_generator import InvoiceSummaryGenerator
from invoice_processor.models.invoice import FlatInvoiceRecord


class TestInvoiceSummaryGenerator:
    """Test summary generator functionality"""
    
    def test_init_creates_output_directory(self, temp_dir):
        """
        Given output directory path
        When initializing summary generator
        Then output directory should be created
        """
        output_dir = temp_dir / "summary_output"
        
        generator = InvoiceSummaryGenerator(str(output_dir))
        
        assert output_dir.exists()
        assert generator.output_dir == output_dir
    
    def test_analyze_processing_results_with_records(self, sample_flat_records):
        """
        Given flat invoice records
        When analyzing processing results
        Then correct statistics should be calculated
        """
        generator = InvoiceSummaryGenerator()
        
        results = generator.analyze_processing_results(sample_flat_records)
        
        assert results['total_files'] == 2
        assert results['successful_extractions'] == 2
        assert results['ocr_only'] == 0
        assert results['failed_extractions'] == 0
        assert results['success_rate'] == 100.0
        assert results['total_line_items'] == 2
    
    def test_analyze_processing_results_empty(self):
        """
        Given empty records list
        When analyzing processing results
        Then zero statistics should be returned
        """
        generator = InvoiceSummaryGenerator()
        
        results = generator.analyze_processing_results([])
        
        assert results['total_files'] == 0
        assert results['successful_extractions'] == 0
        assert results['success_rate'] == 0.0
    
    def test_analyze_processing_results_with_ocr_records(self):
        """
        Given records with OCR-only extractions
        When analyzing processing results
        Then OCR records should be counted separately
        """
        generator = InvoiceSummaryGenerator()
        
        # Create OCR-only record
        ocr_record = FlatInvoiceRecord(
            vendor_name="Unknown (OCR only)",
            item_description="OCR Text...",
            file_path="ocr_file.pdf"
        )
        
        results = generator.analyze_processing_results([ocr_record])
        
        assert results['total_files'] == 1
        assert results['ocr_only'] == 1
        assert results['successful_extractions'] == 0
    
    def test_analyze_processing_results_with_failed_records(self):
        """
        Given records with failed extractions
        When analyzing processing results
        Then failed records should be counted
        """
        generator = InvoiceSummaryGenerator()
        
        # Create failed record
        failed_record = FlatInvoiceRecord(
            vendor_name="Test Vendor",
            item_description="No line items found",
            file_path="failed_file.pdf"
        )
        
        results = generator.analyze_processing_results([failed_record])
        
        assert results['total_files'] == 1
        assert results['failed_extractions'] == 1
    
    def test_generate_invoice_summary_table(self, sample_flat_records):
        """
        Given flat invoice records
        When generating summary table
        Then DataFrame with correct structure should be returned
        """
        generator = InvoiceSummaryGenerator()
        
        table = generator.generate_invoice_summary_table(sample_flat_records)
        
        assert isinstance(table, pd.DataFrame)
        assert len(table) == 2  # Two unique files
        assert 'File' in table.columns
        assert 'Invoice Number' in table.columns
        assert 'Processing Status' in table.columns
        assert 'Extraction Quality' in table.columns
    
    def test_generate_invoice_summary_table_empty(self):
        """
        Given empty records
        When generating summary table
        Then empty DataFrame should be returned
        """
        generator = InvoiceSummaryGenerator()
        
        table = generator.generate_invoice_summary_table([])
        
        assert isinstance(table, pd.DataFrame)
        assert len(table) == 0
    
    def test_generate_financial_summary_with_valid_data(self):
        """
        Given records with valid financial data
        When generating financial summary
        Then correct calculations should be returned
        """
        generator = InvoiceSummaryGenerator()
        
        records = [
            FlatInvoiceRecord(
                vendor_name="Vendor A",
                total_amount=100.0,
                currency="EUR",
                item_description="Test item A",
                file_path="file1.pdf"
            ),
            FlatInvoiceRecord(
                vendor_name="Vendor B", 
                total_amount=200.0,
                currency="EUR",
                item_description="Test item B",
                file_path="file2.pdf"
            )
        ]
        
        summary = generator.generate_financial_summary(records)
        
        assert summary['total_invoices_with_amounts'] == 2
        assert summary['total_value'] == 300.0
        assert summary['average_invoice_value'] == 150.0
        assert summary['min_invoice'] == 100.0
        assert summary['max_invoice'] == 200.0
        assert 'EUR' in summary['currencies']
    
    def test_generate_financial_summary_no_valid_data(self):
        """
        Given records without valid financial data
        When generating financial summary
        Then appropriate message should be returned
        """
        generator = InvoiceSummaryGenerator()
        
        records = [
            FlatInvoiceRecord(
                vendor_name="Unknown (OCR only)",
                item_description="Test item C",
                file_path="ocr_file.pdf"
            )
        ]
        
        summary = generator.generate_financial_summary(records)
        
        assert 'message' in summary
        assert 'No valid financial data' in summary['message']
    
    def test_generate_detailed_summary_report(self, sample_flat_records):
        """
        Given processing results and statistics
        When generating detailed summary report
        Then formatted text report should be returned
        """
        generator = InvoiceSummaryGenerator()
        
        processing_stats = {
            'total_files': 2,
            'successful_extractions': 2,
            'success_rate': 100.0,
            'total_line_items': 2
        }
        
        report = generator.generate_detailed_summary_report(
            sample_flat_records, 
            processing_stats, 
            "test.csv"
        )
        
        assert isinstance(report, str)
        assert "INVOICE PROCESSING SUMMARY REPORT" in report
        assert "Total Files Processed: 2" in report
        assert "Success Rate: 100.0%" in report
    
    def test_save_summary_report(self, sample_flat_records, temp_dir):
        """
        Given records and output directory
        When saving summary report
        Then report file should be created
        """
        generator = InvoiceSummaryGenerator(str(temp_dir))
        
        with patch('builtins.open', mock_open()) as mock_file:
            result_path = generator.save_summary_report(sample_flat_records, "test.csv")
            
            assert result_path is not None
            assert "invoice_processing_summary_" in result_path
            mock_file.assert_called_once()
    
    def test_save_summary_table(self, sample_flat_records, temp_dir):
        """
        Given records and output directory  
        When saving summary table
        Then CSV table file should be created
        """
        generator = InvoiceSummaryGenerator(str(temp_dir))
        
        with patch('pandas.DataFrame.to_csv') as mock_to_csv:
            result_path = generator.save_summary_table(sample_flat_records)
            
            assert result_path is not None
            assert "invoice_summary_table_" in result_path
            mock_to_csv.assert_called_once()
    
    def test_save_summary_table_empty_data(self, temp_dir):
        """
        Given empty records
        When saving summary table
        Then empty string should be returned
        """
        generator = InvoiceSummaryGenerator(str(temp_dir))
        
        result_path = generator.save_summary_table([])
        
        assert result_path == ""


class TestSummaryGeneratorEdgeCases:
    """Test edge cases and error handling"""
    
    def test_file_path_display_formatting(self):
        """
        Given file paths with data/input prefix
        When generating summary table
        Then paths should be formatted for readability
        """
        generator = InvoiceSummaryGenerator()
        
        record = FlatInvoiceRecord(
            vendor_name="Test Vendor",
            item_description="Test item D",
            file_path="data/input/vendor_a/invoice.pdf"
        )
        
        table = generator.generate_invoice_summary_table([record])
        
        # Should remove data/input/ prefix
        assert table.iloc[0]['File'] == "vendor_a/invoice.pdf"
    
    def test_multiple_currencies_in_financial_summary(self):
        """
        Given records with different currencies
        When generating financial summary
        Then all currencies should be listed
        """
        generator = InvoiceSummaryGenerator()
        
        records = [
            FlatInvoiceRecord(
                vendor_name="Vendor A",
                total_amount=100.0,
                currency="EUR",
                item_description="Test item E",
                file_path="file1.pdf"
            ),
            FlatInvoiceRecord(
                vendor_name="Vendor B",
                total_amount=150.0, 
                currency="USD",
                item_description="Test item F",
                file_path="file2.pdf"
            )
        ]
        
        summary = generator.generate_financial_summary(records)
        
        assert len(summary['currencies']) == 2
        assert 'EUR' in summary['currencies']
        assert 'USD' in summary['currencies']
    
    def test_processing_status_classification(self):
        """
        Given different types of records
        When generating summary table
        Then processing status should be correctly classified
        """
        generator = InvoiceSummaryGenerator()
        
        records = [
            # Successful AI extraction
            FlatInvoiceRecord(
                vendor_name="AI Vendor",
                item_description="Product A",
                file_path="success.pdf"
            ),
            # OCR only
            FlatInvoiceRecord(
                vendor_name="Unknown (OCR only)",
                item_description="OCR Text...",
                file_path="ocr.pdf"
            ),
            # Failed extraction
            FlatInvoiceRecord(
                vendor_name="Some Vendor",
                item_description="No line items found",
                file_path="failed.pdf"
            )
        ]
        
        table = generator.generate_invoice_summary_table(records)
        
        statuses = table['Processing Status'].tolist()
        assert 'AI Extracted' in statuses
        assert 'OCR Only' in statuses
        assert 'Failed' in statuses
    
    def test_products_truncation_in_summary(self):
        """
        Given invoice with many products
        When generating summary table
        Then products should be truncated with ellipsis
        """
        generator = InvoiceSummaryGenerator()
        
        # Create records with many products for same file
        records = [
            FlatInvoiceRecord(
                vendor_name="Multi Product Vendor",
                item_description="Product 1",
                file_path="multi.pdf"
            ),
            FlatInvoiceRecord(
                vendor_name="Multi Product Vendor",
                item_description="Product 2", 
                file_path="multi.pdf"
            ),
            FlatInvoiceRecord(
                vendor_name="Multi Product Vendor",
                item_description="Product 3",
                file_path="multi.pdf"
            )
        ]
        
        table = generator.generate_invoice_summary_table(records)
        
        products_cell = table.iloc[0]['Products']
        assert "..." in products_cell  # Should be truncated
        assert "Product 1" in products_cell
        assert "Product 2" in products_cell


class TestSummaryGeneratorIntegration:
    """Integration tests for summary generator"""
    
    def test_complete_summary_generation_workflow(self, temp_dir):
        """
        Given mixed processing results
        When running complete summary generation
        Then all outputs should be created correctly
        """
        generator = InvoiceSummaryGenerator(str(temp_dir))
        
        # Create diverse set of records
        records = [
            FlatInvoiceRecord(
                invoice_number="SUC-001",
                vendor_name="Success Vendor", 
                total_amount=500.0,
                currency="EUR",
                item_description="Success Product",
                file_path="success.pdf"
            ),
            FlatInvoiceRecord(
                vendor_name="Unknown (OCR only)",
                item_description="OCR Text extraction failed",
                file_path="ocr_fallback.pdf"
            ),
            FlatInvoiceRecord(
                vendor_name="Failed Vendor",
                item_description="No line items found",
                file_path="failed.pdf"
            )
        ]
        
        # Generate all summary components
        processing_stats = generator.analyze_processing_results(records)
        financial_summary = generator.generate_financial_summary(records)
        summary_table = generator.generate_invoice_summary_table(records)
        
        # Verify comprehensive results
        assert processing_stats['total_files'] == 3
        assert processing_stats['successful_extractions'] == 1
        assert processing_stats['ocr_only'] == 1
        assert processing_stats['failed_extractions'] == 1
        
        assert financial_summary['total_invoices_with_amounts'] == 1
        assert financial_summary['total_value'] == 500.0
        
        assert len(summary_table) == 3
        assert set(summary_table['Processing Status']) == {'AI Extracted', 'OCR Only', 'Failed'}
    
    def test_summary_with_real_file_operations(self, temp_dir):
        """
        Given real file system operations
        When saving summary files
        Then actual files should be created
        """
        generator = InvoiceSummaryGenerator(str(temp_dir))
        
        records = [
            FlatInvoiceRecord(
                vendor_name="Real Test Vendor",
                item_description="Test item G",
                file_path="real_test.pdf"
            )
        ]
        
        # Save both summary types
        summary_file = generator.save_summary_report(records, "test_input.csv")
        table_file = generator.save_summary_table(records)
        
        # Verify files exist
        assert Path(summary_file).exists()
        assert Path(table_file).exists()
        
        # Verify file contents
        with open(summary_file, 'r') as f:
            content = f.read()
            assert "INVOICE PROCESSING SUMMARY REPORT" in content
        
        # Verify CSV structure
        df = pd.read_csv(table_file)
        assert 'File' in df.columns
        assert len(df) == 1