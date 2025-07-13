#!/usr/bin/env python3
"""
Generate summary for existing processed invoice data
"""

import pandas as pd
from pathlib import Path
import sys
import os

# Add src to path to import modules
sys.path.append(str(Path(__file__).parent / "src"))

from invoice_processor.models.invoice import FlatInvoiceRecord
from invoice_processor.utils.summary_generator import InvoiceSummaryGenerator

def main():
    # Read the current CSV output
    csv_file = "data/output/processed_invoices_20250713_084012.csv"
    
    if not Path(csv_file).exists():
        print(f"CSV file not found: {csv_file}")
        return
    
    # Load data
    df = pd.read_csv(csv_file)
    
    # Convert to FlatInvoiceRecord objects
    records = []
    for _, row in df.iterrows():
        record_dict = row.to_dict()
        # Handle NaN values
        for key, value in record_dict.items():
            if pd.isna(value):
                record_dict[key] = None
        
        record = FlatInvoiceRecord(**record_dict)
        records.append(record)
    
    # Generate summary
    summary_generator = InvoiceSummaryGenerator("data/output")
    
    # Save comprehensive summary report
    summary_file = summary_generator.save_summary_report(records, csv_file)
    table_file = summary_generator.save_summary_table(records)
    
    print(f"✅ Summary report generated: {summary_file}")
    print(f"✅ Summary table generated: {table_file}")
    
    # Also create the specifically requested file name
    timestamp_free_summary = "data/output/invoice_processing_summary.txt"
    
    # Generate report content
    processing_stats = summary_generator.analyze_processing_results(records)
    report_content = summary_generator.generate_detailed_summary_report(
        records, processing_stats, csv_file
    )
    
    # Save with requested filename
    with open(timestamp_free_summary, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Custom summary file: {timestamp_free_summary}")

if __name__ == "__main__":
    main()