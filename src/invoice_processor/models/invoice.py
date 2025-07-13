from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class InvoiceLineItem(BaseModel):
    """Individual line item in an invoice"""
    item_description: str = Field(..., description="Description of the item/service")
    quantity: Optional[Decimal] = Field(None, description="Quantity of items")
    unit_price: Optional[Decimal] = Field(None, description="Price per unit")
    line_total: Optional[Decimal] = Field(None, description="Total for this line item")
    item_code: Optional[str] = Field(None, description="Product/service code")


class InvoiceHeader(BaseModel):
    """Invoice header information"""
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    invoice_date: Optional[date] = Field(None, description="Invoice date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    vendor_name: Optional[str] = Field(None, description="Vendor/supplier name")
    vendor_address: Optional[str] = Field(None, description="Vendor address")
    vendor_tax_id: Optional[str] = Field(None, description="Vendor tax ID")
    customer_name: Optional[str] = Field(None, description="Customer/buyer name")
    customer_address: Optional[str] = Field(None, description="Customer address")
    total_amount: Optional[Decimal] = Field(None, description="Total invoice amount")
    tax_amount: Optional[Decimal] = Field(None, description="Total tax amount")
    subtotal: Optional[Decimal] = Field(None, description="Subtotal before tax")
    currency: Optional[str] = Field("USD", description="Currency code")


class Invoice(BaseModel):
    """Complete invoice structure"""
    header: InvoiceHeader
    line_items: List[InvoiceLineItem] = Field(default_factory=list)
    raw_text: Optional[str] = Field(None, description="Raw extracted text")
    file_path: str = Field(..., description="Source file path")
    processing_timestamp: Optional[str] = Field(None, description="When this was processed")


class FlatInvoiceRecord(BaseModel):
    """Flattened invoice record with header repeated for each line item"""
    # Header fields
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    total_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    currency: Optional[str] = "USD"
    
    # Line item fields
    item_description: str
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    line_total: Optional[Decimal] = None
    item_code: Optional[str] = None
    
    # Metadata
    file_path: str
    processing_timestamp: Optional[str] = None
