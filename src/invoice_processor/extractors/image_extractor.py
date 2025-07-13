import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class ImageExtractor:
    """Extract text from image files using OCR"""
    
    def __init__(self):
        # Configure Tesseract for better invoice processing
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/:-$€£¥₹ '
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy"""
        try:
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive thresholding
            threshold = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(threshold)
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"Error preprocessing image: {e}. Using original image.")
            return image
    
    def extract_text_from_image(self, image: Image.Image) -> Optional[str]:
        """Extract text from image using Tesseract OCR"""
        try:
            # Preprocess the image
            processed_image = self.preprocess_image(image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)
            
            if text.strip():
                logger.info("Successfully extracted text from image using OCR")
                return text.strip()
            else:
                logger.warning("No text found in image")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return None
    
    def extract_text_from_file(self, file_path: Path) -> Optional[str]:
        """Extract text from image file"""
        try:
            image = Image.open(file_path)
            return self.extract_text_from_image(image)
        except Exception as e:
            logger.error(f"Error opening image file {file_path}: {e}")
            return None
