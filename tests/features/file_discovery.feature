Feature: File Discovery and Organization
  As a system administrator
  I want to discover invoice files in nested directories
  So that all invoices are processed regardless of their location

  Background:
    Given I have an input directory structure with nested folders

  Scenario: Discover files in main directory only
    Given the input directory contains 1 file in the root
    When I search for files with recursive mode disabled
    Then I should find 1 file
    And the file should be from the root directory

  Scenario: Discover files recursively in nested directories
    Given the input directory contains files in subdirectories
    And vendor_a subdirectory contains 2 PDF files
    And vendor_b subdirectory contains 1 PDF file
    When I search for files with recursive mode enabled
    Then I should find 4 files total
    And I should see files from vendor_a directory
    And I should see files from vendor_b directory
    And I should see files from root directory

  Scenario: Handle empty directories gracefully
    Given the input directory is empty
    When I search for files with recursive mode enabled
    Then I should find 0 files
    And no error should occur

  Scenario: Filter files by supported extensions
    Given the input directory contains mixed file types
    And there are PDF files
    And there are PNG files
    And there are TXT files
    When I search for invoice files
    Then I should only find PDF and PNG files
    And TXT files should be ignored

  Scenario: Preserve directory structure when moving files
    Given I have processed invoice files in nested directories
    When I move files to the processed directory
    Then the original directory structure should be preserved
    And files should be in their respective vendor subdirectories

  Scenario: Handle file name conflicts during move
    Given a file with the same name already exists in processed directory
    When I try to move a newly processed file
    Then the file should be renamed with a counter suffix
    And both files should exist in the processed directory