Feature: Summary Report Generation
  As a business manager
  I want to generate comprehensive summary reports
  So that I can understand processing results and financial insights

  Scenario: Generate processing overview statistics
    Given I have processed multiple invoices with various outcomes
    And some invoices were successfully extracted by AI
    And some invoices used OCR fallback
    And some invoices failed completely
    When I generate a processing summary
    Then the summary should show total files processed
    And it should show success rate percentage
    And it should categorize processing outcomes
    And it should show total line items extracted

  Scenario: Generate financial summary for valid invoices
    Given I have processed invoices with financial data
    And the invoices have different currencies
    And the invoices have various total amounts
    When I generate a financial summary
    Then the summary should show total invoice value
    And it should show average invoice value
    And it should show minimum and maximum amounts
    And it should list currencies used

  Scenario: Create tabular invoice summary
    Given I have processed invoices from different directories
    When I generate a tabular summary
    Then each invoice should have one summary row
    And the table should show file paths relative to input directory
    And it should show processing status for each invoice
    And it should show extraction quality ratings
    And vendor and customer information should be included

  Scenario: Handle invoices with missing financial data
    Given I have some invoices without total amounts
    And some invoices with only OCR data
    When I generate a financial summary
    Then invoices without amounts should be excluded from financial calculations
    And a note should indicate excluded invoices
    And calculations should be based only on valid financial data

  Scenario: Save summary to text file with proper formatting
    Given I have processing results and statistics
    When I save the summary report
    Then a text file should be created with timestamp
    And the file should have proper section headers
    And tables should be formatted for readability
    And all relevant information should be included

  Scenario: Generate summary table as separate CSV
    Given I have invoice processing results
    When I generate a summary table
    Then a separate CSV file should be created
    And it should contain one row per invoice
    And columns should include all relevant summary fields
    And the data should be suitable for spreadsheet analysis