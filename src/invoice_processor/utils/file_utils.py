import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}


def get_invoice_files(directory: Path, recursive: bool = True) -> List[Path]:
    """Get all supported invoice files from a directory and optionally its subdirectories"""
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        return []
    
    files = []
    
    if recursive:
        # Use rglob for recursive search
        for pattern in SUPPORTED_EXTENSIONS:
            pattern_files = list(directory.rglob(f"*{pattern}"))
            files.extend(pattern_files)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file_path in files:
            if file_path not in seen:
                seen.add(file_path)
                unique_files.append(file_path)
        files = unique_files
        
        logger.info(f"Found {len(files)} invoice files recursively in {directory}")
    else:
        # Original non-recursive behavior
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(file_path)
        
        logger.info(f"Found {len(files)} invoice files in {directory}")
    
    # Sort files by path for consistent processing order
    files.sort(key=str)
    
    # Log directory breakdown
    if recursive and files:
        directory_counts = {}
        for file_path in files:
            parent_dir = file_path.parent
            relative_dir = parent_dir.relative_to(directory)
            dir_name = str(relative_dir) if relative_dir != Path('.') else 'root'
            directory_counts[dir_name] = directory_counts.get(dir_name, 0) + 1
        
        logger.info("Files by directory:")
        for dir_name, count in sorted(directory_counts.items()):
            logger.info(f"  {dir_name}: {count} files")
    
    return files


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't"""
    path.mkdir(parents=True, exist_ok=True)


def move_processed_file(source: Path, processed_dir: Path, input_base_dir: Path = None) -> Path:
    """Move processed file to processed directory, preserving subdirectory structure"""
    ensure_directory(processed_dir)
    
    # If we have the base input directory, preserve the relative path structure
    if input_base_dir and input_base_dir in source.parents:
        # Get relative path from input base to source file
        relative_path = source.relative_to(input_base_dir)
        destination = processed_dir / relative_path
        
        # Ensure the subdirectory exists
        ensure_directory(destination.parent)
    else:
        # Fallback to simple file name in processed root
        destination = processed_dir / source.name
    
    # Handle file name conflicts
    counter = 1
    original_destination = destination
    while destination.exists():
        stem = original_destination.stem
        suffix = original_destination.suffix
        destination = original_destination.parent / f"{stem}_{counter}{suffix}"
        counter += 1
    
    source.rename(destination)
    logger.info(f"Moved processed file: {source} -> {destination}")
    return destination
