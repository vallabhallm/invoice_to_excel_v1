import pytest
from pathlib import Path
from invoice_processor.models.invoice import Invoice, InvoiceHeader, InvoiceLineItem
from invoice_processor.workflows.invoice_workflow import flatten_invoice_data


def test_flatten_invoice_data():
    """Test invoice data flattening"""
    # Create test invoice
    header = InvoiceHeader(
        invoice_number="INV-001",
        vendor_name="Test Vendor",
        total_amount=100.00
    )
    
    line_items = [
        InvoiceLineItem(item_description="Item 1", quantity=2, unit_price=25.00, line_total=50.00),
        InvoiceLineItem(item_description="Item 2", quantity=1, unit_price=50.00, line_total=50.00)
    ]
    
    invoice = Invoice(
        header=header,
        line_items=line_items,
        file_path="test.pdf"
    )
    
    # Test flattening
    flat_records = flatten_invoice_data(invoice)
    
    assert len(flat_records) == 2
    assert all(record.invoice_number == "INV-001" for record in flat_records)
    assert all(record.vendor_name == "Test Vendor" for record in flat_records)
    assert flat_records[0].item_description == "Item 1"
    assert flat_records[1].item_description == "Item 2"


def test_flatten_invoice_data_no_line_items():
    """Test flattening invoice with no line items"""
    header = InvoiceHeader(
        invoice_number="INV-002",
        vendor_name="Test Vendor 2"
    )
    
    invoice = Invoice(
        header=header,
        line_items=[],
        file_path="test2.pdf"
    )
    
    flat_records = flatten_invoice_data(invoice)
    
    assert len(flat_records) == 1
    assert flat_records[0].invoice_number == "INV-002"
    assert flat_records[0].item_description == "No line items found"


if __name__ == "__main__":
    pytest.main([__file__])
