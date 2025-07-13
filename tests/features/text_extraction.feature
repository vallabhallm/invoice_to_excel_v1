Feature: Text Extraction from Invoice Files
  As a data processor
  I want to extract text from various invoice file formats
  So that I can analyze the invoice content

  Scenario: Extract text from PDF with embedded text
    Given I have a PDF file with embedded text content
    When I extract text from the PDF
    Then I should get the text content successfully
    And the text should not be empty
    And no OCR should be used

  Scenario: Extract text from PDF without embedded text using OCR
    Given I have a PDF file without embedded text (scanned image)
    When I extract text from the PDF
    Then PDF text extraction should fail initially
    And the system should convert PDF to images
    And OCR should be applied to the images
    And I should get OCR-extracted text

  Scenario: Extract text from image file using OCR
    Given I have an image file containing invoice text
    When I extract text from the image
    Then OCR should be applied directly
    And I should get the extracted text
    And the text should contain recognizable invoice elements

  Scenario: Handle corrupted or unreadable files
    Given I have a corrupted PDF file
    When I try to extract text from the file
    Then the extraction should fail gracefully
    And an appropriate error should be logged
    And no text should be returned

  Scenario: Preprocess images for better OCR accuracy
    Given I have a noisy image file
    When I extract text using OCR
    Then the image should be preprocessed first
    And noise reduction should be applied
    And the OCR accuracy should be improved

  Scenario: Handle files with insufficient text content
    Given I have a file with very little text content
    When I extract text from the file
    Then the system should detect insufficient content
    And appropriate warnings should be logged
    And the file should be skipped for AI processing