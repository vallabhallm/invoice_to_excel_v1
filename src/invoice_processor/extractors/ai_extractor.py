import json
import logging
import os
from typing import Optional

import openai
from anthropic import Anthropic

from invoice_processor.models.invoice import Invoice, InvoiceHeader, InvoiceLineItem

logger = logging.getLogger(__name__)


class AIExtractor:
    """Extract structured invoice data using AI models"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI if API key is available
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = openai.OpenAI()
        
        # Initialize Anthropic if API key is available
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
            try:
                self.anthropic_client = Anthropic(api_key=anthropic_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
                self.anthropic_client = None
    
    def create_extraction_prompt(self, text: str) -> str:
        """Create a prompt for AI-based invoice data extraction"""
        return f"""
Extract structured invoice information from the following text. Return a JSON object with this exact structure:

{{
    "header": {{
        "invoice_number": "string or null",
        "invoice_date": "YYYY-MM-DD format or null",
        "due_date": "YYYY-MM-DD format or null",
        "vendor_name": "string or null",
        "vendor_address": "string or null",
        "vendor_tax_id": "string or null",
        "customer_name": "string or null",
        "customer_address": "string or null",
        "total_amount": "decimal number or null",
        "tax_amount": "decimal number or null",
        "subtotal": "decimal number or null",
        "currency": "string (USD, EUR, etc.) or null"
    }},
    "line_items": [
        {{
            "item_description": "string",
            "quantity": "decimal number or null",
            "unit_price": "decimal number or null",
            "line_total": "decimal number or null",
            "item_code": "string or null"
        }}
    ]
}}

Rules:
- Extract all line items with their descriptions, quantities, prices, and totals
- Be precise with numerical values (remove currency symbols, keep only numbers and decimals)
- Convert dates to YYYY-MM-DD format
- If information is not found, use null
- Return only valid JSON, no additional text

Invoice text:
{text}
"""
    
    def extract_with_openai(self, text: str) -> Optional[dict]:
        """Extract invoice data using OpenAI GPT models"""
        if not self.openai_client:
            logger.warning("OpenAI client not initialized")
            return None
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # More cost-effective than gpt-4
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured data from invoices. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": self.create_extraction_prompt(text)
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error extracting with OpenAI: {e}")
            return None
    
    def extract_with_anthropic(self, text: str) -> Optional[dict]:
        """Extract invoice data using Anthropic Claude"""
        if not self.anthropic_client:
            logger.warning("Anthropic client not initialized")
            return None
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cost-effective
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": self.create_extraction_prompt(text)
                    }
                ]
            )
            
            content = response.content[0].text
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error extracting with Anthropic: {e}")
            return None
    
    def extract_invoice_data(self, text: str, file_path: str) -> Optional[Invoice]:
        """Extract structured invoice data from text using available AI models"""
        
        # Try OpenAI first, then Anthropic as fallback
        extracted_data = None
        
        if self.openai_client:
            extracted_data = self.extract_with_openai(text)
        
        if not extracted_data and self.anthropic_client:
            logger.info("Falling back to Anthropic for extraction")
            extracted_data = self.extract_with_anthropic(text)
        
        if not extracted_data:
            logger.error("Failed to extract data with any AI model")
            return None
        
        try:
            # Parse the extracted data into our Pydantic models
            header_data = extracted_data.get("header", {})
            line_items_data = extracted_data.get("line_items", [])
            
            header = InvoiceHeader(**header_data)
            line_items = [InvoiceLineItem(**item) for item in line_items_data]
            
            invoice = Invoice(
                header=header,
                line_items=line_items,
                raw_text=text,
                file_path=file_path
            )
            
            logger.info(f"Successfully extracted invoice data with {len(line_items)} line items")
            return invoice
            
        except Exception as e:
            logger.error(f"Error parsing extracted data: {e}")
            return None
