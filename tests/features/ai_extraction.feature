Feature: AI-Powered Invoice Data Extraction
  As a business analyst
  I want to extract structured data from invoice text using AI
  So that I can automate invoice processing and analysis

  Background:
    Given AI services are configured and available

  Scenario: Successful extraction using OpenAI
    Given I have invoice text content
    And OpenAI API is available
    When I extract invoice data using AI
    Then OpenAI should be tried first
    And I should get structured invoice data
    And the data should include header information
    And the data should include line items
    And no fallback to Anthropic should occur

  Scenario: Fallback to Anthropic when OpenAI fails
    Given I have invoice text content
    And OpenAI API is unavailable or returns an error
    And Anthropic API is available
    When I extract invoice data using AI
    Then OpenAI should be tried first
    And OpenAI should fail
    And the system should fallback to Anthropic
    And Anthropic should return structured data
    And I should get valid invoice data

  Scenario: Handle AI extraction failure with OCR fallback
    Given I have invoice text content
    And both OpenAI and Anthropic APIs are unavailable
    When I extract invoice data using AI
    Then both AI services should fail
    And the system should create a basic invoice structure
    And the invoice should have the filename as invoice number
    And the vendor should be marked as "Unknown (OCR only)"
    And the raw text should be preserved in line items

  Scenario: Parse valid AI response into invoice models
    Given I have a valid AI JSON response
    When I parse the response into invoice models
    Then the invoice header should be created correctly
    And all line items should be parsed
    And the data should pass validation
    And the invoice object should be complete

  Scenario: Handle malformed AI responses gracefully
    Given I have a malformed AI JSON response
    When I try to parse the response
    Then JSON parsing should fail
    And appropriate error should be logged
    And no invoice object should be created
    And the system should fallback to basic structure

  Scenario: Validate extracted data meets business rules
    Given I have extracted invoice data
    When I validate the invoice data
    Then required fields should be present
    And numeric values should be valid
    And dates should be in correct format
    And line item totals should be consistent

  Scenario: Handle API quota exceeded errors
    Given I have invoice text content
    And the AI API quota is exceeded
    When I try to extract data using AI
    Then the API should return a quota error
    And the error should be logged appropriately
    And the system should fallback to basic structure
    And processing should continue for other files