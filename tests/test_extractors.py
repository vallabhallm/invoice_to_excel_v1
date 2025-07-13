"""
Unit tests for extractors
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path

from invoice_processor.extractors.ai_extractor import AIExtractor
from invoice_processor.extractors.pdf_extractor import PDFExtractor
from invoice_processor.extractors.image_extractor import ImageExtractor


class TestAIExtractor:
    """Test AI extraction functionality"""
    
    def test_init_with_env_vars(self, mock_env_vars):
        """
        Given environment variables are set
        When initializing AIExtractor
        Then both clients should be initialized
        """
        with patch('invoice_processor.extractors.ai_extractor.openai.OpenAI') as mock_openai, \
             patch('invoice_processor.extractors.ai_extractor.Anthropic') as mock_anthropic:
            
            extractor = AIExtractor()
            
            mock_openai.assert_called_once()
            mock_anthropic.assert_called_once_with(api_key="test-anthropic-key")
    
    def test_init_without_env_vars(self, monkeypatch):
        """
        Given no environment variables
        When initializing AIExtractor
        Then clients should be None
        """
        # Remove env vars
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        with patch('invoice_processor.extractors.ai_extractor.openai.OpenAI') as mock_openai, \
             patch('invoice_processor.extractors.ai_extractor.Anthropic') as mock_anthropic:
            
            extractor = AIExtractor()
            
            assert extractor.openai_client is None
            assert extractor.anthropic_client is None
    
    def test_create_extraction_prompt(self, mock_env_vars):
        """
        Given text content
        When creating extraction prompt
        Then prompt should contain text and proper structure
        """
        extractor = AIExtractor()
        text = "Sample invoice text"
        
        prompt = extractor.create_extraction_prompt(text)
        
        assert "Sample invoice text" in prompt
        assert "JSON" in prompt
        assert "header" in prompt
        assert "line_items" in prompt
    
    def test_extract_with_openai_success(self, mock_env_vars, mock_openai_response):
        """
        Given valid OpenAI response
        When extracting with OpenAI
        Then structured data should be returned
        """
        with patch('invoice_processor.extractors.ai_extractor.openai.OpenAI') as mock_openai:
            # Setup mock response
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = json.dumps(mock_openai_response)
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            
            extractor = AIExtractor()
            result = extractor.extract_with_openai("test text")
            
            assert result is not None
            assert "header" in result
            assert "line_items" in result
    
    def test_extract_with_openai_failure(self, mock_env_vars):
        """
        Given OpenAI API error
        When extracting with OpenAI
        Then None should be returned and error logged
        """
        with patch('invoice_processor.extractors.ai_extractor.openai.OpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
            
            extractor = AIExtractor()
            result = extractor.extract_with_openai("test text")
            
            assert result is None
    
    def test_extract_with_anthropic_success(self, mock_env_vars, mock_anthropic_response):
        """
        Given valid Anthropic response
        When extracting with Anthropic
        Then structured data should be returned
        """
        with patch('invoice_processor.extractors.ai_extractor.Anthropic') as mock_anthropic:
            mock_response = Mock()
            mock_content = Mock()
            mock_content.text = json.dumps(mock_anthropic_response)
            mock_response.content = [mock_content]
            mock_anthropic.return_value.messages.create.return_value = mock_response
            
            extractor = AIExtractor()
            result = extractor.extract_with_anthropic("test text")
            
            assert result is not None
            assert "header" in result
            assert "line_items" in result
    
    def test_extract_invoice_data_openai_success(self, mock_env_vars, mock_openai_response):
        """
        Given valid text and working OpenAI
        When extracting invoice data
        Then OpenAI should be used and invoice returned
        """
        with patch('invoice_processor.extractors.ai_extractor.openai.OpenAI') as mock_openai, \
             patch('invoice_processor.extractors.ai_extractor.Anthropic'):
            
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = json.dumps(mock_openai_response)
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            
            extractor = AIExtractor()
            result = extractor.extract_invoice_data("test text", "test.pdf")
            
            assert result is not None
            assert result.header.invoice_number == "AI-001"
            assert len(result.line_items) == 1
    
    def test_extract_invoice_data_fallback_to_anthropic(self, mock_env_vars, mock_anthropic_response):
        """
        Given OpenAI fails and Anthropic succeeds
        When extracting invoice data
        Then Anthropic should be used as fallback
        """
        with patch('invoice_processor.extractors.ai_extractor.openai.OpenAI') as mock_openai, \
             patch('invoice_processor.extractors.ai_extractor.Anthropic') as mock_anthropic:
            
            # OpenAI fails
            mock_openai.return_value.chat.completions.create.side_effect = Exception("OpenAI Error")
            
            # Anthropic succeeds
            mock_response = Mock()
            mock_content = Mock()
            mock_content.text = json.dumps(mock_anthropic_response)
            mock_response.content = [mock_content]
            mock_anthropic.return_value.messages.create.return_value = mock_response
            
            extractor = AIExtractor()
            result = extractor.extract_invoice_data("test text", "test.pdf")
            
            assert result is not None
            assert result.header.vendor_name == "Anthropic Vendor"
    
    def test_extract_invoice_data_both_fail(self, mock_env_vars):
        """
        Given both AI services fail
        When extracting invoice data
        Then None should be returned
        """
        with patch('invoice_processor.extractors.ai_extractor.openai.OpenAI') as mock_openai, \
             patch('invoice_processor.extractors.ai_extractor.Anthropic') as mock_anthropic:
            
            mock_openai.return_value.chat.completions.create.side_effect = Exception("OpenAI Error")
            mock_anthropic.return_value.messages.create.side_effect = Exception("Anthropic Error")
            
            extractor = AIExtractor()
            result = extractor.extract_invoice_data("test text", "test.pdf")
            
            assert result is None


class TestPDFExtractor:
    """Test PDF extraction functionality"""
    
    def test_extract_text_success(self, sample_pdf_file):
        """
        Given a valid PDF file
        When extracting text
        Then text content should be returned
        """
        extractor = PDFExtractor()
        
        # Mock PyPDF2 to return some text
        with patch('invoice_processor.extractors.pdf_extractor.PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "Sample PDF text content"
            mock_reader.return_value.pages = [mock_page]
            
            result = extractor.extract_text(sample_pdf_file)
            
            assert result == "Sample PDF text content"
    
    def test_extract_text_no_content(self, sample_pdf_file):
        """
        Given a PDF with no extractable text
        When extracting text
        Then None should be returned
        """
        extractor = PDFExtractor()
        
        with patch('invoice_processor.extractors.pdf_extractor.PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = ""
            mock_reader.return_value.pages = [mock_page]
            
            result = extractor.extract_text(sample_pdf_file)
            
            assert result is None
    
    def test_extract_text_file_error(self, temp_dir):
        """
        Given an invalid PDF file
        When extracting text
        Then None should be returned and error logged
        """
        extractor = PDFExtractor()
        invalid_file = temp_dir / "invalid.pdf"
        invalid_file.write_text("Not a valid PDF")
        
        result = extractor.extract_text(invalid_file)
        
        assert result is None
    
    def test_convert_to_images_success(self, sample_pdf_file):
        """
        Given a valid PDF file
        When converting to images
        Then list of images should be returned
        """
        extractor = PDFExtractor()
        
        with patch('invoice_processor.extractors.pdf_extractor.convert_from_path') as mock_convert:
            mock_image = Mock()
            mock_convert.return_value = [mock_image, mock_image]
            
            result = extractor.convert_to_images(sample_pdf_file)
            
            assert len(result) == 2
            assert all(img == mock_image for img in result)
    
    def test_convert_to_images_error(self, sample_pdf_file):
        """
        Given PDF conversion error
        When converting to images
        Then empty list should be returned
        """
        extractor = PDFExtractor()
        
        with patch('invoice_processor.extractors.pdf_extractor.convert_from_path') as mock_convert:
            mock_convert.side_effect = Exception("Conversion error")
            
            result = extractor.convert_to_images(sample_pdf_file)
            
            assert result == []


class TestImageExtractor:
    """Test image extraction functionality"""
    
    def test_init_sets_tesseract_config(self):
        """
        Given ImageExtractor initialization
        When creating instance
        Then tesseract config should be set
        """
        extractor = ImageExtractor()
        
        assert hasattr(extractor, 'tesseract_config')
        assert '--oem' in extractor.tesseract_config
        assert '--psm' in extractor.tesseract_config
    
    def test_preprocess_image_success(self, sample_image_file):
        """
        Given an image file
        When preprocessing
        Then processed image should be returned
        """
        extractor = ImageExtractor()
        
        with patch('invoice_processor.extractors.image_extractor.Image.open') as mock_open, \
             patch('invoice_processor.extractors.image_extractor.cv2') as mock_cv2, \
             patch('invoice_processor.extractors.image_extractor.np') as mock_np:
            
            mock_image = Mock()
            mock_open.return_value = mock_image
            
            # Mock OpenCV operations
            mock_cv2.cvtColor.return_value = mock_np.array([])
            mock_cv2.GaussianBlur.return_value = mock_np.array([])
            mock_cv2.adaptiveThreshold.return_value = mock_np.array([])
            
            # Mock PIL Image.fromarray
            mock_processed = Mock()
            with patch('invoice_processor.extractors.image_extractor.Image.fromarray', return_value=mock_processed):
                result = extractor.preprocess_image(mock_image)
                
                assert result == mock_processed
    
    def test_preprocess_image_error_fallback(self, sample_image_file):
        """
        Given image preprocessing error
        When preprocessing
        Then original image should be returned
        """
        extractor = ImageExtractor()
        
        mock_image = Mock()
        
        with patch('invoice_processor.extractors.image_extractor.cv2') as mock_cv2:
            mock_cv2.cvtColor.side_effect = Exception("CV2 Error")
            
            result = extractor.preprocess_image(mock_image)
            
            assert result == mock_image
    
    def test_extract_text_from_image_success(self, sample_image_file):
        """
        Given an image with text
        When extracting text using OCR
        Then text should be returned
        """
        extractor = ImageExtractor()
        
        mock_image = Mock()
        
        with patch('invoice_processor.extractors.image_extractor.pytesseract.image_to_string') as mock_tesseract:
            mock_tesseract.return_value = "Extracted text from image"
            
            with patch.object(extractor, 'preprocess_image', return_value=mock_image):
                result = extractor.extract_text_from_image(mock_image)
                
                assert result == "Extracted text from image"
    
    def test_extract_text_from_image_no_text(self, sample_image_file):
        """
        Given an image with no readable text
        When extracting text using OCR
        Then None should be returned
        """
        extractor = ImageExtractor()
        
        mock_image = Mock()
        
        with patch('invoice_processor.extractors.image_extractor.pytesseract.image_to_string') as mock_tesseract:
            mock_tesseract.return_value = ""
            
            with patch.object(extractor, 'preprocess_image', return_value=mock_image):
                result = extractor.extract_text_from_image(mock_image)
                
                assert result is None
    
    def test_extract_text_from_image_error(self, sample_image_file):
        """
        Given OCR error
        When extracting text from image
        Then None should be returned and error logged
        """
        extractor = ImageExtractor()
        
        mock_image = Mock()
        
        with patch('invoice_processor.extractors.image_extractor.pytesseract.image_to_string') as mock_tesseract:
            mock_tesseract.side_effect = Exception("OCR Error")
            
            with patch.object(extractor, 'preprocess_image', return_value=mock_image):
                result = extractor.extract_text_from_image(mock_image)
                
                assert result is None
    
    def test_extract_text_from_file_success(self, sample_image_file):
        """
        Given an image file path
        When extracting text from file
        Then text should be returned
        """
        extractor = ImageExtractor()
        
        with patch('invoice_processor.extractors.image_extractor.Image.open') as mock_open:
            mock_image = Mock()
            mock_open.return_value = mock_image
            
            with patch.object(extractor, 'extract_text_from_image', return_value="File text"):
                result = extractor.extract_text_from_file(sample_image_file)
                
                assert result == "File text"
    
    def test_extract_text_from_file_error(self, temp_dir):
        """
        Given invalid image file
        When extracting text from file
        Then None should be returned
        """
        extractor = ImageExtractor()
        
        invalid_file = temp_dir / "invalid.png"
        invalid_file.write_text("Not an image")
        
        result = extractor.extract_text_from_file(invalid_file)
        
        assert result is None


class TestExtractorsIntegration:
    """Integration tests for extractors working together"""
    
    def test_pdf_with_ocr_fallback_workflow(self, sample_pdf_file):
        """
        Given PDF extraction fails and OCR is needed
        When processing through complete workflow
        Then OCR should be applied successfully
        """
        pdf_extractor = PDFExtractor()
        image_extractor = ImageExtractor()
        
        # Mock PDF extraction to fail
        with patch.object(pdf_extractor, 'extract_text', return_value=None), \
             patch.object(pdf_extractor, 'convert_to_images') as mock_convert, \
             patch.object(image_extractor, 'extract_text_from_image', return_value="OCR text"):
            
            mock_image = Mock()
            mock_convert.return_value = [mock_image]
            
            # Simulate workflow
            pdf_text = pdf_extractor.extract_text(sample_pdf_file)
            assert pdf_text is None
            
            images = pdf_extractor.convert_to_images(sample_pdf_file)
            assert len(images) == 1
            
            ocr_text = image_extractor.extract_text_from_image(images[0])
            assert ocr_text == "OCR text"
    
    def test_ai_extractor_with_different_providers(self, mock_env_vars):
        """
        Given different AI provider configurations
        When extracting with AI
        Then appropriate provider should be used
        """
        # Test with only OpenAI
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}, clear=True):
            with patch('invoice_processor.extractors.ai_extractor.openai.OpenAI') as mock_openai:
                extractor = AIExtractor()
                assert extractor.openai_client is not None
                assert extractor.anthropic_client is None
        
        # Test with only Anthropic
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}, clear=True):
            with patch('invoice_processor.extractors.ai_extractor.Anthropic') as mock_anthropic:
                extractor = AIExtractor()
                assert extractor.openai_client is None
                assert extractor.anthropic_client is not None