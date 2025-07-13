"""Invoice Processing Application with Prefect and GenAI"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .models.invoice import Invoice, InvoiceHeader, InvoiceLineItem, FlatInvoiceRecord
from .workflows.invoice_workflow import process_invoices, run_invoice_processing

__all__ = [
    "Invoice",
    "InvoiceHeader", 
    "InvoiceLineItem",
    "FlatInvoiceRecord",
    "process_invoices",
    "run_invoice_processing"
]
