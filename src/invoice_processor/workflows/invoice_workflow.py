import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from prefect import flow, task

from invoice_processor.extractors.ai_extractor import AIExtractor
from invoice_processor.extractors.image_extractor import ImageExtractor
from invoice_processor.extractors.pdf_extractor import PDFExtractor
from invoice_processor.models.invoice import FlatInvoiceRecord, Invoice
from invoice_processor.utils.file_utils import get_invoice_files, move_processed_file
from invoice_processor.utils.summary_generator import InvoiceSummaryGenerator

logger = logging.getLogger(__name__)


@task(retries=2, log_prints=True)
def extract_text_from_file(file_path: Path) -> Optional[str]:
    """Extract text from PDF or image file"""
    file_extension = file_path.suffix.lower()
    
    try:
        if file_extension == '.pdf':
            pdf_extractor = PDFExtractor()
            
            # Try direct text extraction first
            text = pdf_extractor.extract_text(file_path)
            
            if not text or len(text.strip()) < 50:  # If no text or very little text
                logger.info(f"Direct PDF text extraction failed for {file_path}, trying OCR")
                images = pdf_extractor.convert_to_images(file_path)
                
                if images:
                    image_extractor = ImageExtractor()
                    ocr_text = ""
                    for i, image in enumerate(images):
                        page_text = image_extractor.extract_text_from_image(image)
                        if page_text:
                            ocr_text += f"Page {i+1}:\n{page_text}\n\n"
                    text = ocr_text if ocr_text.strip() else text
            
            return text
            
        else:  # Image files
            image_extractor = ImageExtractor()
            return image_extractor.extract_text_from_file(file_path)
            
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return None


@task(retries=1, log_prints=True)
def extract_invoice_structure(text: str, file_path: str) -> Optional[Invoice]:
    """Extract structured invoice data using AI or create basic structure if AI fails"""
    if not text or len(text.strip()) < 20:
        logger.warning(f"Insufficient text for AI extraction: {file_path}")
        return None
    
    ai_extractor = AIExtractor()
    invoice = ai_extractor.extract_invoice_data(text, file_path)
    
    # If AI extraction fails, create a basic invoice with the raw text
    if not invoice:
        logger.info(f"AI extraction failed for {file_path}, creating basic invoice structure")
        from ..models.invoice import Invoice, InvoiceHeader, InvoiceLineItem
        
        # Create basic header with filename and extracted text
        filename = Path(file_path).stem
        header = InvoiceHeader(
            invoice_number=filename,
            vendor_name="Unknown (OCR only)",
            total_amount=None
        )
        
        # Create a single line item with the raw text for manual review
        line_item = InvoiceLineItem(
            item_description=f"OCR Text (AI extraction failed): {text[:500]}..."
        )
        
        invoice = Invoice(
            header=header,
            line_items=[line_item],
            raw_text=text,
            file_path=file_path
        )
        
        logger.info(f"Created basic invoice structure for {file_path}")
    
    return invoice


@task(log_prints=True)
def flatten_invoice_data(invoice: Invoice) -> List[FlatInvoiceRecord]:
    """Convert invoice to flat records (one per line item)"""
    flat_records = []
    processing_timestamp = datetime.now().isoformat()
    
    # If no line items, create one record with just header info
    if not invoice.line_items:
        flat_record = FlatInvoiceRecord(
            # Header fields
            invoice_number=invoice.header.invoice_number,
            invoice_date=invoice.header.invoice_date,
            due_date=invoice.header.due_date,
            vendor_name=invoice.header.vendor_name,
            vendor_address=invoice.header.vendor_address,
            vendor_tax_id=invoice.header.vendor_tax_id,
            customer_name=invoice.header.customer_name,
            customer_address=invoice.header.customer_address,
            total_amount=invoice.header.total_amount,
            tax_amount=invoice.header.tax_amount,
            subtotal=invoice.header.subtotal,
            currency=invoice.header.currency,
            
            # Empty line item fields
            item_description="No line items found",
            quantity=None,
            unit_price=None,
            line_total=None,
            item_code=None,
            
            # Metadata
            file_path=invoice.file_path,
            processing_timestamp=processing_timestamp
        )
        flat_records.append(flat_record)
    else:
        # Create one record per line item
        for line_item in invoice.line_items:
            flat_record = FlatInvoiceRecord(
                # Header fields (repeated for each line item)
                invoice_number=invoice.header.invoice_number,
                invoice_date=invoice.header.invoice_date,
                due_date=invoice.header.due_date,
                vendor_name=invoice.header.vendor_name,
                vendor_address=invoice.header.vendor_address,
                vendor_tax_id=invoice.header.vendor_tax_id,
                customer_name=invoice.header.customer_name,
                customer_address=invoice.header.customer_address,
                total_amount=invoice.header.total_amount,
                tax_amount=invoice.header.tax_amount,
                subtotal=invoice.header.subtotal,
                currency=invoice.header.currency,
                
                # Line item fields
                item_description=line_item.item_description,
                quantity=line_item.quantity,
                unit_price=line_item.unit_price,
                line_total=line_item.line_total,
                item_code=line_item.item_code,
                
                # Metadata
                file_path=invoice.file_path,
                processing_timestamp=processing_timestamp
            )
            flat_records.append(flat_record)
    
    logger.info(f"Created {len(flat_records)} flat records for invoice {invoice.header.invoice_number}")
    return flat_records


@task(log_prints=True)
def save_results_to_csv(all_records: List[FlatInvoiceRecord], output_file: Path) -> str:
    """Save all flat records to CSV file"""
    if not all_records:
        logger.warning("No records to save")
        return "No records processed"
    
    # Convert to DataFrame
    df = pd.DataFrame([record.model_dump() if hasattr(record, 'model_dump') else record.dict() for record in all_records])
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    logger.info(f"Saved {len(all_records)} records to {output_file}")
    return f"Successfully saved {len(all_records)} records to {output_file}"


@flow(name="Invoice Processing Workflow", log_prints=True)
def process_invoices(
    input_dir: str = "data/input",
    output_dir: str = "data/output", 
    processed_dir: str = "data/processed"
) -> str:
    """Main workflow to process all invoices in input directory"""
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    processed_path = Path(processed_dir)
    
    # Get all invoice files
    invoice_files = get_invoice_files(input_path)
    
    if not invoice_files:
        return f"No invoice files found in {input_dir}"
    
    logger.info(f"Starting processing of {len(invoice_files)} invoice files")
    
    all_flat_records = []
    processed_count = 0
    
    for file_path in invoice_files:
        logger.info(f"Processing file: {file_path}")
        
        try:
            # Extract text from file
            text = extract_text_from_file(file_path)
            
            if not text:
                logger.warning(f"No text extracted from {file_path}, skipping")
                continue
            
            # Extract structured invoice data
            invoice = extract_invoice_structure(text, str(file_path))
            
            if not invoice:
                logger.warning(f"Failed to extract invoice structure from {file_path}, skipping")
                continue
            
            # Convert to flat records
            flat_records = flatten_invoice_data(invoice)
            all_flat_records.extend(flat_records)
            
            # Move processed file, preserving directory structure
            move_processed_file(file_path, processed_path, input_path)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    # Save all results to CSV
    if all_flat_records:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"processed_invoices_{timestamp}.csv"
        save_results_to_csv(all_flat_records, output_file)
        
        # Generate summary reports
        summary_generator = InvoiceSummaryGenerator(str(output_path))
        summary_file = summary_generator.save_summary_report(all_flat_records, str(output_file))
        table_file = summary_generator.save_summary_table(all_flat_records)
        
        logger.info(f"Generated summary report: {summary_file}")
        logger.info(f"Generated summary table: {table_file}")
        
        return f"Successfully processed {processed_count} invoices with {len(all_flat_records)} total line items. Results saved to {output_file}. Summary: {summary_file}"
    else:
        return f"No invoices were successfully processed from {len(invoice_files)} files"


# Convenience function for running the workflow
def run_invoice_processing(input_dir: str = "data/input", 
                         output_dir: str = "data/output",
                         processed_dir: str = "data/processed") -> str:
    """Run the invoice processing workflow"""
    return process_invoices(input_dir, output_dir, processed_dir)
