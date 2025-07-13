import logging
from pathlib import Path
from typing import Optional

import PyPDF2
from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text and images from PDF files"""
    
    def extract_text(self, file_path: Path) -> Optional[str]:
        """Extract text directly from PDF using PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                if text.strip():
                    logger.info(f"Successfully extracted text from PDF: {file_path}")
                    return text.strip()
                else:
                    logger.warning(f"No text found in PDF: {file_path}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return None
    
    def convert_to_images(self, file_path: Path) -> list[Image.Image]:
        """Convert PDF pages to images for OCR processing"""
        try:
            images = convert_from_path(file_path, dpi=300)
            logger.info(f"Converted PDF {file_path} to {len(images)} images")
            return images
        except Exception as e:
            logger.error(f"Error converting PDF to images {file_path}: {e}")
            return []
