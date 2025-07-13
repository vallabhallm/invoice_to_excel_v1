Feature: Invoice Data Processing and Flattening
  As a data analyst
  I want to process and flatten invoice data
  So that I can analyze it in tabular format

  Scenario: Flatten invoice with multiple line items
    Given I have an invoice with 2 line items
    And the invoice has complete header information
    When I flatten the invoice data
    Then I should get 2 flat records
    And each record should contain the header information
    And each record should contain different line item data
    And the processing timestamp should be added

  Scenario: Flatten invoice with no line items
    Given I have an invoice with no line items
    And the invoice has header information
    When I flatten the invoice data
    Then I should get 1 flat record
    And the record should contain header information
    And the item description should be "No line items found"
    And line item fields should be null

  Scenario: Save flat records to CSV file
    Given I have multiple flat invoice records
    When I save the records to CSV
    Then a CSV file should be created
    And the file should contain all records
    And the file should have proper headers
    And the data should be properly formatted

  Scenario: Handle empty record list gracefully
    Given I have an empty list of invoice records
    When I try to save records to CSV
    Then appropriate warning should be logged
    And no CSV file should be created
    And the operation should complete without error

  Scenario: Process multiple invoices in batch
    Given I have multiple invoice files
    When I process all invoices in batch
    Then each invoice should be processed independently
    And successful extractions should be aggregated
    And failed extractions should be logged but not stop processing
    And a summary should be provided at the end

  Scenario: Maintain data integrity during processing
    Given I have invoices with various currencies
    And some invoices have missing optional fields
    When I process and flatten the data
    Then currency information should be preserved
    And missing fields should be handled as null
    And no data corruption should occur
    And all valid data should be retained