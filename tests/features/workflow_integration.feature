Feature: End-to-End Workflow Integration
  As a system operator
  I want to run the complete invoice processing workflow
  So that I can process invoices from input to final output automatically

  Background:
    Given the invoice processing system is set up
    And input, output, and processed directories exist

  Scenario: Process single invoice successfully
    Given I have one valid invoice file in the input directory
    And AI services are available
    When I run the invoice processing workflow
    Then the invoice should be processed successfully
    And structured data should be extracted
    And the file should be moved to processed directory
    And a CSV output should be generated
    And a summary report should be created

  Scenario: Process multiple invoices from nested directories
    Given I have invoice files in multiple subdirectories
    And the files have different formats (PDF and images)
    When I run the invoice processing workflow
    Then all files should be discovered recursively
    And each file should be processed independently
    And directory structure should be preserved in processed folder
    And all successful extractions should be in the CSV output
    And the summary should reflect all processing attempts

  Scenario: Handle mixed success and failure scenarios
    Given I have a mix of valid and invalid invoice files
    And some files will succeed AI extraction
    And some files will need OCR fallback
    And some files will fail completely
    When I run the invoice processing workflow
    Then successful files should be processed and moved
    And failed files should be logged but not stop processing
    And the CSV should contain all successful extractions
    And the summary should show accurate success rates

  Scenario: Continue processing when individual files fail
    Given I have multiple invoice files
    And one file is corrupted and will cause an error
    When I run the invoice processing workflow
    Then the corrupted file error should be logged
    And processing should continue with remaining files
    And other files should be processed successfully
    And the final result should include all successful extractions

  Scenario: Generate comprehensive outputs for all scenarios
    Given I have processed invoices with various outcomes
    When the workflow completes
    Then a timestamped CSV file should be created with all data
    And a summary report should be generated
    And a tabular summary CSV should be created
    And all files should be moved to appropriate processed subdirectories
    And appropriate log messages should be generated throughout

  Scenario: Handle empty input directory gracefully
    Given the input directory is empty
    When I run the invoice processing workflow
    Then the workflow should complete without error
    And appropriate message should indicate no files found
    And no output files should be created
    And the system should be ready for future runs

  Scenario: Validate workflow with different AI provider configurations
    Given I have invoice files to process
    And only OpenAI is configured
    When I run the invoice processing workflow
    Then OpenAI should be used for extraction
    And no Anthropic fallback should be attempted
    And processing should complete successfully
    And the summary should indicate AI provider used