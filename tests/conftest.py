"""
Test configuration and fixtures for invoice processor tests
"""
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from PIL import Image
import json

from invoice_processor.models.invoice import (
    Invoice, InvoiceHeader, InvoiceLineItem, FlatInvoiceRecord
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_invoice_header():
    """Sample invoice header for testing"""
    return InvoiceHeader(
        invoice_number="INV-001",
        invoice_date=datetime(2024, 1, 15).date(),
        due_date=datetime(2024, 2, 15).date(),
        vendor_name="Test Vendor Ltd",
        vendor_address="123 Test Street, Test City",
        vendor_tax_id="VAT123456",
        customer_name="Test Customer Inc",
        customer_address="456 Customer Ave, Customer City",
        total_amount=1000.00,
        tax_amount=200.00,
        subtotal=800.00,
        currency="EUR"
    )


@pytest.fixture
def sample_line_items():
    """Sample line items for testing"""
    return [
        InvoiceLineItem(
            item_description="Product A",
            quantity=2,
            unit_price=200.00,
            line_total=400.00,
            item_code="PA001"
        ),
        InvoiceLineItem(
            item_description="Product B",
            quantity=1,
            unit_price=400.00,
            line_total=400.00,
            item_code="PB001"
        )
    ]


@pytest.fixture
def sample_invoice(sample_invoice_header, sample_line_items):
    """Complete sample invoice for testing"""
    return Invoice(
        header=sample_invoice_header,
        line_items=sample_line_items,
        raw_text="Sample invoice text content",
        file_path="test_invoice.pdf"
    )


@pytest.fixture
def empty_line_items_invoice(sample_invoice_header):
    """Invoice with no line items"""
    return Invoice(
        header=sample_invoice_header,
        line_items=[],
        raw_text="Invoice with no line items",
        file_path="empty_invoice.pdf"
    )


@pytest.fixture
def sample_pdf_file(temp_dir):
    """Create a sample PDF file for testing"""
    pdf_path = temp_dir / "sample.pdf"
    # Create a minimal PDF content
    pdf_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
179
%%EOF"""
    
    pdf_path.write_text(pdf_content)
    return pdf_path


@pytest.fixture
def sample_image_file(temp_dir):
    """Create a sample image file for testing"""
    image_path = temp_dir / "sample.png"
    # Create a simple test image
    img = Image.new('RGB', (100, 50), color='white')
    img.save(image_path)
    return image_path


@pytest.fixture
def input_directory_structure(temp_dir):
    """Create a test directory structure with nested folders"""
    input_dir = temp_dir / "input"
    
    # Create main input directory
    input_dir.mkdir()
    
    # Create subdirectories
    (input_dir / "vendor_a").mkdir()
    (input_dir / "vendor_b").mkdir()
    
    # Create test files in main directory
    (input_dir / "main_invoice.pdf").write_text("Main invoice content")
    
    # Create test files in subdirectories
    (input_dir / "vendor_a" / "invoice_a1.pdf").write_text("Vendor A invoice 1")
    (input_dir / "vendor_a" / "invoice_a2.pdf").write_text("Vendor A invoice 2")
    (input_dir / "vendor_b" / "invoice_b1.pdf").write_text("Vendor B invoice 1")
    
    return input_dir


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "header": {
            "invoice_number": "AI-001",
            "invoice_date": "2024-01-15",
            "vendor_name": "AI Vendor",
            "total_amount": 500.00,
            "currency": "USD"
        },
        "line_items": [
            {
                "item_description": "AI Product",
                "quantity": 1,
                "unit_price": 500.00,
                "line_total": 500.00
            }
        ]
    }


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response"""
    return {
        "header": {
            "invoice_number": "ANT-001",
            "invoice_date": "2024-01-15",
            "vendor_name": "Anthropic Vendor",
            "total_amount": 750.00,
            "currency": "EUR"
        },
        "line_items": [
            {
                "item_description": "Anthropic Product",
                "quantity": 2,
                "unit_price": 375.00,
                "line_total": 750.00
            }
        ]
    }


@pytest.fixture
def sample_flat_records():
    """Sample flat invoice records for testing"""
    timestamp = datetime.now().isoformat()
    return [
        FlatInvoiceRecord(
            invoice_number="INV-001",
            invoice_date=datetime(2024, 1, 15).date(),
            vendor_name="Vendor A",
            total_amount=500.00,
            currency="EUR",
            item_description="Product 1",
            quantity=2,
            unit_price=250.00,
            line_total=500.00,
            file_path="vendor_a/invoice1.pdf",
            processing_timestamp=timestamp
        ),
        FlatInvoiceRecord(
            invoice_number="INV-002",
            invoice_date=datetime(2024, 1, 16).date(),
            vendor_name="Vendor B",
            total_amount=300.00,
            currency="USD",
            item_description="Product 2",
            quantity=1,
            unit_price=300.00,
            line_total=300.00,
            file_path="vendor_b/invoice2.pdf",
            processing_timestamp=timestamp
        )
    ]


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("LOG_LEVEL", "INFO")


@pytest.fixture
def sample_ocr_text():
    """Sample OCR extracted text"""
    return """
    INVOICE
    
    Invoice Number: OCR-001
    Date: 2024-01-15
    
    Vendor: OCR Test Vendor
    Address: 123 OCR Street
    
    Customer: OCR Customer
    
    Item                Qty    Price    Total
    OCR Product A       2      100.00   200.00
    OCR Product B       1      150.00   150.00
    
    Subtotal: 350.00
    Tax: 70.00
    Total: 420.00
    """


@pytest.fixture
def error_scenarios():
    """Various error scenarios for testing"""
    return {
        "empty_file": "",
        "invalid_pdf": "Not a valid PDF file",
        "corrupted_json": '{"invalid": json}',
        "missing_required_fields": '{"header": {}}',
        "network_error": "Connection timeout",
        "api_quota_exceeded": "API quota exceeded"
    }