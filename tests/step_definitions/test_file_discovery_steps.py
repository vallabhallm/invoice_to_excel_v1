"""
Step definitions for file discovery feature tests
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from pathlib import Path

from invoice_processor.utils.file_utils import get_invoice_files, move_processed_file

# Load scenarios from feature file
scenarios('../features/file_discovery.feature')


@pytest.fixture
def context():
    """Test context to store state between steps"""
    return {}


@given('I have an input directory structure with nested folders')
def input_directory_structure(context, input_directory_structure):
    """Set up the input directory structure"""
    context['input_dir'] = input_directory_structure


@given('the input directory contains 1 file in the root')
def create_root_file(context, input_directory_structure):
    """Ensure there's exactly one file in root"""
    context['input_dir'] = input_directory_structure
    # The fixture already creates this


@given('the input directory contains files in subdirectories')
def files_in_subdirectories(context, input_directory_structure):
    """Files exist in subdirectories"""
    context['input_dir'] = input_directory_structure


@given(parsers.parse('vendor_a subdirectory contains {count:d} PDF files'))
def vendor_a_files(context, count):
    """Verify vendor_a has expected number of files"""
    vendor_a_path = context['input_dir'] / 'vendor_a'
    pdf_files = list(vendor_a_path.glob('*.pdf'))
    assert len(pdf_files) == count
    context['vendor_a_files'] = pdf_files


@given(parsers.parse('vendor_b subdirectory contains {count:d} PDF files'))
def vendor_b_files(context, count):
    """Verify vendor_b has expected number of files"""
    vendor_b_path = context['input_dir'] / 'vendor_b'
    pdf_files = list(vendor_b_path.glob('*.pdf'))
    assert len(pdf_files) == count
    context['vendor_b_files'] = pdf_files


@given('the input directory is empty')
def empty_input_directory(context, temp_dir):
    """Create empty input directory"""
    empty_dir = temp_dir / 'empty_input'
    empty_dir.mkdir()
    context['input_dir'] = empty_dir


@given('the input directory contains mixed file types')
def mixed_file_types(context, temp_dir):
    """Create directory with mixed file types"""
    input_dir = temp_dir / 'mixed_input'
    input_dir.mkdir()
    
    # Create different file types
    (input_dir / 'invoice1.pdf').write_text('PDF content')
    (input_dir / 'invoice2.png').write_text('PNG content')
    (input_dir / 'readme.txt').write_text('TXT content')
    (input_dir / 'data.xlsx').write_text('Excel content')
    
    context['input_dir'] = input_dir


@given('there are PDF files')
def pdf_files_exist(context):
    """Verify PDF files exist"""
    pdf_files = list(context['input_dir'].glob('*.pdf'))
    assert len(pdf_files) > 0
    context['pdf_files'] = pdf_files


@given('there are PNG files')
def png_files_exist(context):
    """Verify PNG files exist"""
    png_files = list(context['input_dir'].glob('*.png'))
    assert len(png_files) > 0
    context['png_files'] = png_files


@given('there are TXT files')
def txt_files_exist(context):
    """Verify TXT files exist"""
    txt_files = list(context['input_dir'].glob('*.txt'))
    assert len(txt_files) > 0
    context['txt_files'] = txt_files


@given('I have processed invoice files in nested directories')
def processed_files_setup(context, temp_dir):
    """Set up files for moving"""
    input_dir = temp_dir / 'input'
    processed_dir = temp_dir / 'processed'
    
    input_dir.mkdir()
    processed_dir.mkdir()
    
    # Create nested structure
    vendor_dir = input_dir / 'vendor_x'
    vendor_dir.mkdir()
    
    test_file = vendor_dir / 'test_invoice.pdf'
    test_file.write_text('Test invoice content')
    
    context['input_dir'] = input_dir
    context['processed_dir'] = processed_dir
    context['test_file'] = test_file


@given('a file with the same name already exists in processed directory')
def existing_file_conflict(context, temp_dir):
    """Create file conflict scenario"""
    processed_dir = temp_dir / 'processed'
    processed_dir.mkdir()
    
    # Create vendor subdirectory in processed
    vendor_processed = processed_dir / 'vendor_x'
    vendor_processed.mkdir()
    
    # Create existing file
    existing_file = vendor_processed / 'test_invoice.pdf'
    existing_file.write_text('Existing file content')
    
    context['processed_dir'] = processed_dir
    context['existing_file'] = existing_file


@when('I search for files with recursive mode disabled')
def search_non_recursive(context):
    """Search files without recursion"""
    found_files = get_invoice_files(context['input_dir'], recursive=False)
    context['found_files'] = found_files


@when('I search for files with recursive mode enabled')
def search_recursive(context):
    """Search files with recursion"""
    found_files = get_invoice_files(context['input_dir'], recursive=True)
    context['found_files'] = found_files


@when('I search for invoice files')
def search_invoice_files(context):
    """Search for invoice files (default behavior)"""
    found_files = get_invoice_files(context['input_dir'])
    context['found_files'] = found_files


@when('I move files to the processed directory')
def move_files_to_processed(context):
    """Move files preserving structure"""
    moved_file = move_processed_file(
        context['test_file'], 
        context['processed_dir'], 
        context['input_dir']
    )
    context['moved_file'] = moved_file


@when('I try to move a newly processed file')
def move_file_with_conflict(context):
    """Try to move file that will conflict"""
    # Create a new file to move
    input_file = context['input_dir'] / 'vendor_x' / 'test_invoice.pdf'
    
    moved_file = move_processed_file(
        input_file,
        context['processed_dir'],
        context['input_dir']
    )
    context['moved_file'] = moved_file


@then(parsers.parse('I should find {count:d} file'))
@then(parsers.parse('I should find {count:d} files'))
@then(parsers.parse('I should find {count:d} files total'))
def verify_file_count(context, count):
    """Verify the number of files found"""
    assert len(context['found_files']) == count


@then('the file should be from the root directory')
def verify_root_file(context):
    """Verify file is from root directory"""
    found_file = context['found_files'][0]
    assert found_file.parent == context['input_dir']


@then('I should see files from vendor_a directory')
def verify_vendor_a_files(context):
    """Verify vendor_a files are found"""
    vendor_a_files = [f for f in context['found_files'] if 'vendor_a' in str(f)]
    assert len(vendor_a_files) == 2


@then('I should see files from vendor_b directory')
def verify_vendor_b_files(context):
    """Verify vendor_b files are found"""
    vendor_b_files = [f for f in context['found_files'] if 'vendor_b' in str(f)]
    assert len(vendor_b_files) == 1


@then('I should see files from root directory')
def verify_root_files(context):
    """Verify root files are found"""
    root_files = [f for f in context['found_files'] if f.parent == context['input_dir']]
    assert len(root_files) == 1


@then('no error should occur')
def verify_no_error(context):
    """Verify no errors occurred"""
    # If we reach this point, no exception was raised
    assert True


@then('I should only find PDF and PNG files')
def verify_pdf_png_only(context):
    """Verify only supported file types are found"""
    found_extensions = {f.suffix.lower() for f in context['found_files']}
    expected_extensions = {'.pdf', '.png'}
    assert found_extensions.issubset(expected_extensions)


@then('TXT files should be ignored')
def verify_txt_ignored(context):
    """Verify TXT files are not included"""
    txt_files = [f for f in context['found_files'] if f.suffix.lower() == '.txt']
    assert len(txt_files) == 0


@then('the original directory structure should be preserved')
def verify_structure_preserved(context):
    """Verify directory structure is maintained"""
    moved_file = context['moved_file']
    # Should be in processed/vendor_x/test_invoice.pdf
    assert 'vendor_x' in str(moved_file)
    assert moved_file.parent.name == 'vendor_x'


@then('files should be in their respective vendor subdirectories')
def verify_vendor_subdirectories(context):
    """Verify files are in correct vendor subdirectories"""
    moved_file = context['moved_file']
    assert moved_file.parent.parent == context['processed_dir']


@then('the file should be renamed with a counter suffix')
def verify_file_renamed(context):
    """Verify file was renamed to avoid conflict"""
    moved_file = context['moved_file']
    # Should have _1 or similar suffix
    assert '_1' in moved_file.stem


@then('both files should exist in the processed directory')
def verify_both_files_exist(context):
    """Verify both original and new files exist"""
    processed_files = list(context['processed_dir'].rglob('*.pdf'))
    assert len(processed_files) >= 2