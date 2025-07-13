import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from ..models.invoice import FlatInvoiceRecord

logger = logging.getLogger(__name__)


class InvoiceSummaryGenerator:
    """Generate comprehensive summaries and reports from processed invoices"""
    
    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_processing_results(self, records: List[FlatInvoiceRecord]) -> Dict[str, Any]:
        """Analyze processing results and generate statistics"""
        if not records:
            return {
                "total_files": 0,
                "successful_extractions": 0,
                "ocr_only": 0,
                "failed_extractions": 0,
                "success_rate": 0.0
            }
        
        # Group records by file
        files_data = {}
        for record in records:
            file_path = record.file_path
            if file_path not in files_data:
                files_data[file_path] = []
            files_data[file_path].append(record)
        
        total_files = len(files_data)
        successful_extractions = 0
        ocr_only = 0
        failed_extractions = 0
        
        for file_path, file_records in files_data.items():
            first_record = file_records[0]
            
            if first_record.vendor_name == "Unknown (OCR only)":
                ocr_only += 1
            elif first_record.item_description == "No line items found":
                failed_extractions += 1
            else:
                successful_extractions += 1
        
        success_rate = (successful_extractions / total_files * 100) if total_files > 0 else 0
        
        return {
            "total_files": total_files,
            "successful_extractions": successful_extractions,
            "ocr_only": ocr_only,
            "failed_extractions": failed_extractions,
            "success_rate": success_rate,
            "total_line_items": len(records)
        }
    
    def generate_invoice_summary_table(self, records: List[FlatInvoiceRecord]) -> pd.DataFrame:
        """Generate a summary table with one row per invoice"""
        if not records:
            return pd.DataFrame()
        
        # Group records by file to get invoice-level summaries
        invoice_summaries = []
        
        files_data = {}
        for record in records:
            file_path = record.file_path
            if file_path not in files_data:
                files_data[file_path] = []
            files_data[file_path].append(record)
        
        for file_path, file_records in files_data.items():
            first_record = file_records[0]
            
            # Determine processing status
            if first_record.vendor_name == "Unknown (OCR only)":
                status = "OCR Only"
                extraction_quality = "Poor"
            elif first_record.item_description == "No line items found":
                status = "Failed"
                extraction_quality = "None"
            else:
                status = "AI Extracted"
                extraction_quality = "Good"
            
            # Calculate financial summary
            total_amount = first_record.total_amount if first_record.total_amount else 0
            line_item_count = len(file_records)
            
            # Get unique products
            products = []
            for record in file_records:
                if record.item_description and record.item_description not in ["No line items found"]:
                    if not record.item_description.startswith("OCR Text"):
                        products.append(record.item_description)
            
            # Use relative path for better readability if it's in a subdirectory
            file_display = str(Path(file_path))
            if "data/input/" in file_display:
                file_display = file_display.replace("data/input/", "")
            else:
                file_display = Path(file_path).name
            
            invoice_summary = {
                "File": file_display,
                "Invoice Number": first_record.invoice_number or "N/A",
                "Date": first_record.invoice_date or "N/A",
                "Vendor": first_record.vendor_name or "N/A",
                "Customer": first_record.customer_name or "N/A",
                "Total Amount": f"{first_record.currency or ''} {total_amount:.2f}" if total_amount else "N/A",
                "Line Items": line_item_count,
                "Products": "; ".join(products[:2]) + ("..." if len(products) > 2 else "") if products else "N/A",
                "Processing Status": status,
                "Extraction Quality": extraction_quality
            }
            
            invoice_summaries.append(invoice_summary)
        
        return pd.DataFrame(invoice_summaries)
    
    def generate_financial_summary(self, records: List[FlatInvoiceRecord]) -> Dict[str, Any]:
        """Generate financial summary statistics"""
        if not records:
            return {}
        
        # Filter out failed/OCR-only records for financial analysis
        valid_records = [
            r for r in records 
            if r.total_amount and r.vendor_name != "Unknown (OCR only)" 
            and r.item_description != "No line items found"
        ]
        
        if not valid_records:
            return {"message": "No valid financial data extracted"}
        
        # Group by file to get unique invoices
        invoice_totals = {}
        currencies = set()
        
        for record in valid_records:
            file_path = record.file_path
            if file_path not in invoice_totals:
                invoice_totals[file_path] = record.total_amount
                if record.currency:
                    currencies.add(record.currency)
        
        totals = list(invoice_totals.values())
        
        return {
            "total_invoices_with_amounts": len(totals),
            "total_value": sum(totals),
            "average_invoice_value": sum(totals) / len(totals),
            "min_invoice": min(totals),
            "max_invoice": max(totals),
            "currencies": list(currencies)
        }
    
    def generate_detailed_summary_report(self, records: List[FlatInvoiceRecord], 
                                       processing_stats: Dict[str, Any],
                                       csv_file_path: str) -> str:
        """Generate a comprehensive text summary report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get analysis data
        summary_table = self.generate_invoice_summary_table(records)
        financial_summary = self.generate_financial_summary(records)
        
        report_lines = [
            "=" * 80,
            "INVOICE PROCESSING SUMMARY REPORT",
            "=" * 80,
            f"Generated: {timestamp}",
            f"CSV Output: {csv_file_path}",
            "",
            "PROCESSING OVERVIEW",
            "-" * 40,
            f"Total Files Processed: {processing_stats['total_files']}",
            f"Successfully Extracted (AI): {processing_stats['successful_extractions']}",
            f"OCR Fallback Only: {processing_stats['ocr_only']}",
            f"Failed Extractions: {processing_stats['failed_extractions']}",
            f"Overall Success Rate: {processing_stats['success_rate']:.1f}%",
            f"Total Line Items: {processing_stats['total_line_items']}",
            ""
        ]
        
        # Add financial summary if available
        if "total_value" in financial_summary:
            currencies_str = ", ".join(financial_summary["currencies"]) if financial_summary["currencies"] else "Mixed"
            report_lines.extend([
                "FINANCIAL SUMMARY",
                "-" * 40,
                f"Invoices with Valid Amounts: {financial_summary['total_invoices_with_amounts']}",
                f"Total Value: {financial_summary['total_value']:.2f} ({currencies_str})",
                f"Average Invoice Value: {financial_summary['average_invoice_value']:.2f}",
                f"Smallest Invoice: {financial_summary['min_invoice']:.2f}",
                f"Largest Invoice: {financial_summary['max_invoice']:.2f}",
                ""
            ])
        
        # Add detailed invoice table
        if not summary_table.empty:
            report_lines.extend([
                "DETAILED INVOICE SUMMARY",
                "-" * 40,
                ""
            ])
            
            # Convert table to string with proper formatting
            table_str = summary_table.to_string(index=False, max_cols=None, max_colwidth=30)
            report_lines.append(table_str)
            report_lines.append("")
        
        # Add processing status breakdown
        report_lines.extend([
            "PROCESSING STATUS BREAKDOWN",
            "-" * 40,
            ""
        ])
        
        if not summary_table.empty:
            status_counts = summary_table["Processing Status"].value_counts()
            for status, count in status_counts.items():
                report_lines.append(f"{status}: {count} files")
            
            report_lines.append("")
            
            quality_counts = summary_table["Extraction Quality"].value_counts()
            report_lines.append("Extraction Quality:")
            for quality, count in quality_counts.items():
                report_lines.append(f"  {quality}: {count} files")
        
        report_lines.extend([
            "",
            "=" * 80,
            "End of Report",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def save_summary_report(self, records: List[FlatInvoiceRecord], 
                          csv_file_path: str) -> str:
        """Save comprehensive summary report to file"""
        
        # Generate analysis
        processing_stats = self.analyze_processing_results(records)
        
        # Generate detailed report
        report_content = self.generate_detailed_summary_report(
            records, processing_stats, csv_file_path
        )
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.output_dir / f"invoice_processing_summary_{timestamp}.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Summary report saved to: {summary_file}")
        return str(summary_file)
    
    def save_summary_table(self, records: List[FlatInvoiceRecord]) -> str:
        """Save summary table as separate CSV"""
        
        summary_table = self.generate_invoice_summary_table(records)
        
        if summary_table.empty:
            logger.warning("No data to generate summary table")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_file = self.output_dir / f"invoice_summary_table_{timestamp}.csv"
        
        summary_table.to_csv(table_file, index=False)
        
        logger.info(f"Summary table saved to: {table_file}")
        return str(table_file)