"""
Unit tests for file utilities
"""
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from invoice_processor.utils.file_utils import (
    get_invoice_files, move_processed_file, ensure_directory, SUPPORTED_EXTENSIONS
)


class TestGetInvoiceFiles:
    """Test file discovery functionality"""
    
    def test_get_files_from_directory_non_recursive(self, temp_dir):
        """
        Given a directory with invoice files
        When searching with recursive=False
        Then only root level files should be found
        """
        # Create test files
        (temp_dir / "invoice1.pdf").write_text("content")
        (temp_dir / "invoice2.png").write_text("content")
        (temp_dir / "readme.txt").write_text("content")
        
        # Create subdirectory with files (should be ignored)
        sub_dir = temp_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "sub_invoice.pdf").write_text("content")
        
        files = get_invoice_files(temp_dir, recursive=False)
        
        assert len(files) == 2  # Only PDF and PNG from root
        file_names = [f.name for f in files]
        assert "invoice1.pdf" in file_names
        assert "invoice2.png" in file_names
        assert "sub_invoice.pdf" not in file_names
    
    def test_get_files_recursive(self, input_directory_structure):
        """
        Given a directory structure with nested files
        When searching with recursive=True
        Then all invoice files should be found
        """
        files = get_invoice_files(input_directory_structure, recursive=True)
        
        assert len(files) == 4  # 1 root + 2 vendor_a + 1 vendor_b
        
        # Check files from different directories are included
        file_paths = [str(f) for f in files]
        assert any("main_invoice.pdf" in path for path in file_paths)
        assert any("vendor_a" in path for path in file_paths)
        assert any("vendor_b" in path for path in file_paths)
    
    def test_get_files_with_supported_extensions_only(self, temp_dir):
        """
        Given files with various extensions
        When searching for invoice files
        Then only supported extensions should be returned
        """
        # Create files with different extensions
        for ext in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.txt', '.doc']:
            (temp_dir / f"file{ext}").write_text("content")
        
        files = get_invoice_files(temp_dir)
        
        found_extensions = {f.suffix.lower() for f in files}
        assert found_extensions.issubset(SUPPORTED_EXTENSIONS)
        assert '.txt' not in found_extensions
        assert '.doc' not in found_extensions
    
    def test_get_files_from_nonexistent_directory(self, temp_dir):
        """
        Given a non-existent directory
        When searching for files
        Then empty list should be returned and error logged
        """
        non_existent = temp_dir / "does_not_exist"
        
        files = get_invoice_files(non_existent)
        
        assert len(files) == 0
        assert isinstance(files, list)
    
    def test_get_files_case_insensitive_extensions(self, temp_dir):
        """
        Given files with mixed case extensions
        When searching for files
        Then files should be found regardless of case
        """
        (temp_dir / "file.PDF").write_text("content")
        (temp_dir / "file.Png").write_text("content")
        (temp_dir / "file.JPEG").write_text("content")
        
        files = get_invoice_files(temp_dir)
        
        assert len(files) == 3
    
    def test_get_files_sorted_by_path(self, temp_dir):
        """
        Given multiple files
        When searching for files
        Then files should be sorted by path for consistent ordering
        """
        # Create files in different order
        (temp_dir / "z_file.pdf").write_text("content")
        (temp_dir / "a_file.pdf").write_text("content")
        (temp_dir / "m_file.pdf").write_text("content")
        
        files = get_invoice_files(temp_dir)
        
        # Check if sorted
        file_names = [f.name for f in files]
        assert file_names == sorted(file_names)
    
    def test_get_files_removes_duplicates(self, temp_dir):
        """
        Given potential for duplicate file discovery
        When searching recursively
        Then duplicates should be removed
        """
        (temp_dir / "test.pdf").write_text("content")
        
        # This test verifies the deduplication logic works
        files = get_invoice_files(temp_dir, recursive=True)
        
        # Should not have duplicates
        file_paths = [str(f) for f in files]
        assert len(file_paths) == len(set(file_paths))


class TestMoveProcessedFile:
    """Test file moving functionality"""
    
    def test_move_file_simple(self, temp_dir):
        """
        Given a source file and destination directory
        When moving the file
        Then file should be moved to destination
        """
        source_file = temp_dir / "source.pdf"
        source_file.write_text("content")
        
        dest_dir = temp_dir / "destination"
        
        result = move_processed_file(source_file, dest_dir)
        
        assert not source_file.exists()
        assert result.exists()
        assert result.parent == dest_dir
        assert result.name == "source.pdf"
    
    def test_move_file_preserve_structure(self, temp_dir):
        """
        Given a source file in nested structure
        When moving with input_base_dir specified
        Then directory structure should be preserved
        """
        # Create nested structure
        input_base = temp_dir / "input"
        vendor_dir = input_base / "vendor_a"
        vendor_dir.mkdir(parents=True)
        
        source_file = vendor_dir / "invoice.pdf"
        source_file.write_text("content")
        
        processed_dir = temp_dir / "processed"
        
        result = move_processed_file(source_file, processed_dir, input_base)
        
        # Should preserve vendor_a subdirectory
        expected_path = processed_dir / "vendor_a" / "invoice.pdf"
        assert result == expected_path
        assert result.exists()
        assert not source_file.exists()
    
    def test_move_file_handle_name_conflict(self, temp_dir):
        """
        Given a destination file that already exists
        When moving a new file with same name
        Then new file should be renamed with counter
        """
        source_file = temp_dir / "source.pdf"
        source_file.write_text("new content")
        
        dest_dir = temp_dir / "destination"
        dest_dir.mkdir()
        
        # Create existing file
        existing_file = dest_dir / "source.pdf"
        existing_file.write_text("existing content")
        
        result = move_processed_file(source_file, dest_dir)
        
        # Should be renamed with counter
        assert "_1" in result.name
        assert result.exists()
        assert existing_file.exists()  # Original should still exist
        assert result.read_text() == "new content"
    
    def test_move_file_multiple_conflicts(self, temp_dir):
        """
        Given multiple files with same name already exist
        When moving files with conflicts
        Then counter should increment properly
        """
        dest_dir = temp_dir / "destination"
        dest_dir.mkdir()
        
        # Create existing files
        (dest_dir / "test.pdf").write_text("original")
        (dest_dir / "test_1.pdf").write_text("first conflict")
        
        # Move new file
        source_file = temp_dir / "test.pdf"
        source_file.write_text("new file")
        
        result = move_processed_file(source_file, dest_dir)
        
        assert "test_2.pdf" in result.name
        assert result.exists()
    
    def test_move_file_without_base_dir_fallback(self, temp_dir):
        """
        Given no input_base_dir or invalid base_dir
        When moving file
        Then should fallback to simple filename in root
        """
        source_file = temp_dir / "fallback.pdf"
        source_file.write_text("content")
        
        dest_dir = temp_dir / "destination"
        invalid_base = temp_dir / "invalid"
        
        result = move_processed_file(source_file, dest_dir, invalid_base)
        
        # Should be in root of destination
        assert result.parent == dest_dir
        assert result.name == "fallback.pdf"


class TestEnsureDirectory:
    """Test directory creation functionality"""
    
    def test_ensure_directory_creates_new(self, temp_dir):
        """
        Given a non-existent directory path
        When ensuring directory exists
        Then directory should be created
        """
        new_dir = temp_dir / "new" / "nested" / "directory"
        
        ensure_directory(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_ensure_directory_existing_no_error(self, temp_dir):
        """
        Given an existing directory
        When ensuring directory exists
        Then no error should occur
        """
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()
        
        # Should not raise exception
        ensure_directory(existing_dir)
        
        assert existing_dir.exists()
    
    def test_ensure_directory_with_file_conflict(self, temp_dir):
        """
        Given a path where a file already exists
        When ensuring directory exists
        Then appropriate error should be handled
        """
        file_path = temp_dir / "conflicting_file.txt"
        file_path.write_text("content")
        
        # This should raise an exception in real scenario
        with pytest.raises(Exception):
            ensure_directory(file_path)


class TestSupportedExtensions:
    """Test supported file extensions configuration"""
    
    def test_supported_extensions_constant(self):
        """
        Given the SUPPORTED_EXTENSIONS constant
        When checking its contents
        Then it should contain expected file types
        """
        expected_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        
        assert SUPPORTED_EXTENSIONS == expected_extensions
        assert '.txt' not in SUPPORTED_EXTENSIONS
        assert '.doc' not in SUPPORTED_EXTENSIONS
    
    def test_extensions_are_lowercase(self):
        """
        Given SUPPORTED_EXTENSIONS
        When checking extension format
        Then all extensions should be lowercase
        """
        for ext in SUPPORTED_EXTENSIONS:
            assert ext == ext.lower()
            assert ext.startswith('.')


class TestFileUtilsIntegration:
    """Integration tests for file utilities"""
    
    def test_full_workflow_file_discovery_and_move(self, temp_dir):
        """
        Given a complete directory structure
        When discovering and moving files
        Then the complete workflow should work correctly
        """
        # Set up input structure
        input_dir = temp_dir / "input"
        vendor_a = input_dir / "vendor_a"
        vendor_b = input_dir / "vendor_b"
        
        vendor_a.mkdir(parents=True)
        vendor_b.mkdir(parents=True)
        
        # Create files
        (input_dir / "root_invoice.pdf").write_text("root")
        (vendor_a / "va_invoice1.pdf").write_text("va1")
        (vendor_a / "va_invoice2.png").write_text("va2")
        (vendor_b / "vb_invoice1.pdf").write_text("vb1")
        
        processed_dir = temp_dir / "processed"
        
        # Discover files
        files = get_invoice_files(input_dir, recursive=True)
        assert len(files) == 4
        
        # Move all files
        moved_files = []
        for file_path in files:
            moved_file = move_processed_file(file_path, processed_dir, input_dir)
            moved_files.append(moved_file)
        
        # Verify all moved correctly
        assert len(moved_files) == 4
        assert all(f.exists() for f in moved_files)
        
        # Verify structure preserved
        assert (processed_dir / "vendor_a" / "va_invoice1.pdf").exists()
        assert (processed_dir / "vendor_b" / "vb_invoice1.pdf").exists()
        assert (processed_dir / "root_invoice.pdf").exists()
        
        # Verify original files are gone
        remaining_files = get_invoice_files(input_dir, recursive=True)
        assert len(remaining_files) == 0