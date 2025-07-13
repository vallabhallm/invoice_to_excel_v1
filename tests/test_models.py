"""
Unit tests for data models
"""
import pytest
from datetime import datetime, date
from decimal import Decimal

from invoice_processor.models.invoice import (
    InvoiceHeader, InvoiceLineItem, Invoice, FlatInvoiceRecord
)


class TestInvoiceHeader:
    """Test InvoiceHeader model"""
    
    def test_create_invoice_header_with_all_fields(self):
        """
        Given all required and optional fields
        When creating an InvoiceHeader
        Then all fields should be set correctly
        """
        header = InvoiceHeader(
            invoice_number="INV-001",
            invoice_date=date(2024, 1, 15),
            due_date=date(2024, 2, 15),
            vendor_name="Test Vendor",
            vendor_address="123 Test St",
            vendor_tax_id="VAT123",
            customer_name="Test Customer",
            customer_address="456 Customer Ave",
            total_amount=Decimal("1000.00"),
            tax_amount=Decimal("200.00"),
            subtotal=Decimal("800.00"),
            currency="EUR"
        )
        
        assert header.invoice_number == "INV-001"
        assert header.invoice_date == date(2024, 1, 15)
        assert header.vendor_name == "Test Vendor"
        assert header.total_amount == Decimal("1000.00")
        assert header.currency == "EUR"
    
    def test_create_invoice_header_with_minimal_fields(self):
        """
        Given only optional fields (all fields are optional)
        When creating an InvoiceHeader
        Then the header should be created with None values
        """
        header = InvoiceHeader()
        
        assert header.invoice_number is None
        assert header.vendor_name is None
        assert header.total_amount is None
    
    def test_invoice_header_date_validation(self):
        """
        Given invalid date strings
        When creating an InvoiceHeader
        Then validation should handle date conversion
        """
        # This would test Pydantic's date validation
        header = InvoiceHeader(invoice_date="2024-01-15")
        assert isinstance(header.invoice_date, date)
    
    def test_invoice_header_decimal_conversion(self):
        """
        Given numeric values as strings or floats
        When creating an InvoiceHeader
        Then they should be converted to appropriate types
        """
        header = InvoiceHeader(
            total_amount="1000.50",
            tax_amount=200.0
        )
        
        assert isinstance(header.total_amount, (float, Decimal))
        assert isinstance(header.tax_amount, (float, Decimal))


class TestInvoiceLineItem:
    """Test InvoiceLineItem model"""
    
    def test_create_line_item_with_all_fields(self):
        """
        Given all line item fields
        When creating an InvoiceLineItem
        Then all fields should be set correctly
        """
        line_item = InvoiceLineItem(
            item_description="Test Product",
            quantity=Decimal("2.5"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("250.00"),
            item_code="TP001"
        )
        
        assert line_item.item_description == "Test Product"
        assert line_item.quantity == Decimal("2.5")
        assert line_item.unit_price == Decimal("100.00")
        assert line_item.line_total == Decimal("250.00")
        assert line_item.item_code == "TP001"
    
    def test_create_line_item_with_minimal_fields(self):
        """
        Given only item description
        When creating an InvoiceLineItem
        Then other fields should be None
        """
        line_item = InvoiceLineItem(item_description="Minimal Item")
        
        assert line_item.item_description == "Minimal Item"
        assert line_item.quantity is None
        assert line_item.unit_price is None
    
    def test_line_item_numeric_conversion(self):
        """
        Given numeric values as strings
        When creating an InvoiceLineItem
        Then they should be converted properly
        """
        line_item = InvoiceLineItem(
            item_description="Numeric Test",
            quantity="3",
            unit_price="99.99"
        )
        
        assert isinstance(line_item.quantity, (int, float, Decimal))
        assert isinstance(line_item.unit_price, (float, Decimal))


class TestInvoice:
    """Test Invoice model"""
    
    def test_create_complete_invoice(self, sample_invoice_header, sample_line_items):
        """
        Given header and line items
        When creating an Invoice
        Then all components should be properly associated
        """
        invoice = Invoice(
            header=sample_invoice_header,
            line_items=sample_line_items,
            raw_text="Sample raw text",
            file_path="test.pdf"
        )
        
        assert invoice.header == sample_invoice_header
        assert invoice.line_items == sample_line_items
        assert invoice.raw_text == "Sample raw text"
        assert invoice.file_path == "test.pdf"
    
    def test_create_invoice_with_empty_line_items(self, sample_invoice_header):
        """
        Given header but no line items
        When creating an Invoice
        Then line_items should be empty list
        """
        invoice = Invoice(
            header=sample_invoice_header,
            line_items=[],
            file_path="empty.pdf"
        )
        
        assert invoice.header == sample_invoice_header
        assert invoice.line_items == []
        assert len(invoice.line_items) == 0
    
    def test_invoice_with_optional_fields(self, sample_invoice_header, sample_line_items):
        """
        Given minimal invoice data
        When creating an Invoice
        Then optional fields should be handled properly
        """
        invoice = Invoice(
            header=sample_invoice_header,
            line_items=sample_line_items,
            file_path="minimal.pdf"
        )
        
        assert invoice.raw_text is None
        assert invoice.file_path == "minimal.pdf"


class TestFlatInvoiceRecord:
    """Test FlatInvoiceRecord model"""
    
    def test_create_flat_record_with_all_fields(self):
        """
        Given all flat record fields
        When creating a FlatInvoiceRecord
        Then all fields should be set correctly
        """
        timestamp = datetime.now().isoformat()
        
        record = FlatInvoiceRecord(
            invoice_number="FLAT-001",
            invoice_date=date(2024, 1, 15),
            vendor_name="Flat Vendor",
            customer_name="Flat Customer",
            total_amount=Decimal("500.00"),
            currency="USD",
            item_description="Flat Item",
            quantity=Decimal("1"),
            unit_price=Decimal("500.00"),
            line_total=Decimal("500.00"),
            item_code="FI001",
            file_path="flat.pdf",
            processing_timestamp=timestamp
        )
        
        assert record.invoice_number == "FLAT-001"
        assert record.vendor_name == "Flat Vendor"
        assert record.item_description == "Flat Item"
        assert record.processing_timestamp == timestamp
    
    def test_flat_record_with_none_values(self):
        """
        Given flat record with None values
        When creating a FlatInvoiceRecord
        Then None values should be accepted
        """
        record = FlatInvoiceRecord(
            invoice_number=None,
            vendor_name=None,
            item_description="Test item",  # Required field
            file_path="none_test.pdf"
        )
        
        assert record.invoice_number is None
        assert record.vendor_name is None
        assert record.item_description == "Test item"
        assert record.file_path == "none_test.pdf"
    
    def test_flat_record_serialization(self):
        """
        Given a FlatInvoiceRecord
        When converting to dict
        Then all fields should be serializable
        """
        record = FlatInvoiceRecord(
            invoice_number="SER-001",
            invoice_date=date(2024, 1, 15),
            total_amount=Decimal("100.00"),
            item_description="Test item",  # Required field
            file_path="serialize.pdf"
        )
        
        record_dict = record.model_dump() if hasattr(record, 'model_dump') else record.dict()
        
        assert isinstance(record_dict, dict)
        assert record_dict['invoice_number'] == "SER-001"
        assert 'file_path' in record_dict


class TestModelValidation:
    """Test model validation edge cases"""
    
    def test_invoice_header_with_negative_amounts(self):
        """
        Given negative amounts
        When creating an InvoiceHeader
        Then negative values should be accepted (could be credits)
        """
        header = InvoiceHeader(
            total_amount=Decimal("-100.00"),
            tax_amount=Decimal("-20.00")
        )
        
        assert header.total_amount == Decimal("-100.00")
        assert header.tax_amount == Decimal("-20.00")
    
    def test_line_item_with_zero_quantities(self):
        """
        Given zero quantities
        When creating an InvoiceLineItem
        Then zero values should be accepted
        """
        line_item = InvoiceLineItem(
            item_description="Zero quantity item",
            quantity=0,
            unit_price=Decimal("100.00"),
            line_total=Decimal("0.00")
        )
        
        assert line_item.quantity == 0
        assert line_item.line_total == Decimal("0.00")
    
    def test_invoice_with_very_long_strings(self):
        """
        Given very long string values
        When creating invoice models
        Then long strings should be handled properly
        """
        long_description = "x" * 1000
        
        line_item = InvoiceLineItem(item_description=long_description)
        assert len(line_item.item_description) == 1000
        
        header = InvoiceHeader(vendor_name=long_description)
        assert len(header.vendor_name) == 1000
    
    def test_invoice_with_unicode_characters(self):
        """
        Given unicode characters in text fields
        When creating invoice models
        Then unicode should be preserved
        """
        unicode_vendor = "Tëst Vëndör GmbH 中文"
        unicode_product = "Prøduct Nåme €"
        
        header = InvoiceHeader(vendor_name=unicode_vendor)
        line_item = InvoiceLineItem(item_description=unicode_product)
        
        assert header.vendor_name == unicode_vendor
        assert line_item.item_description == unicode_product