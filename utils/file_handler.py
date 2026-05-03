"""
File Handler Utilities

Provides safe file operations for the Code Analyzer agent.
"""

import os
from pathlib import Path
from typing import List, Optional
import chardet
from loguru import logger


def walk_directory(path: str, extensions: List[str]) -> List[str]:
    """
    Recursively find all files with specified extensions in a directory.
    
    Args:
        path: Directory path to search
        extensions: List of file extensions to match (e.g., ['.cob', '.cbl'])
    
    Returns:
        List of file paths matching the extensions
    """
    matched_files = []
    path_obj = Path(path)
    
    if not path_obj.exists():
        logger.error(f"Directory does not exist: {path}")
        return matched_files
    
    if not path_obj.is_dir():
        logger.error(f"Path is not a directory: {path}")
        return matched_files
    
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in [ext.lower() for ext in extensions]:
                    matched_files.append(str(file_path))
                    logger.debug(f"Found file: {file_path}")
        
        logger.info(f"Found {len(matched_files)} files with extensions {extensions} in {path}")
        return matched_files
    
    except Exception as e:
        logger.error(f"Error walking directory {path}: {e}")
        return matched_files


def read_file_safe(path: str) -> Optional[str]:
    """
    Safely read a file with automatic encoding detection.
    
    Args:
        path: File path to read
    
    Returns:
        File content as string, or None if reading fails
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        logger.error(f"File does not exist: {path}")
        return None
    
    if not path_obj.is_file():
        logger.error(f"Path is not a file: {path}")
        return None
    
    try:
        # First, try to detect encoding
        with open(path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        # Read with detected encoding
        with open(path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
            logger.debug(f"Successfully read file {path} with encoding {encoding}")
            return content
    
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        # Fallback to UTF-8 with error replacement
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                logger.warning(f"Read file {path} with UTF-8 fallback")
                return content
        except Exception as e2:
            logger.error(f"Failed to read file {path} even with fallback: {e2}")
            return None


def get_file_stats(path: str) -> dict:
    """
    Get statistics about a file.
    
    Args:
        path: File path
    
    Returns:
        Dictionary with file statistics
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        return {}
    
    try:
        stat = path_obj.stat()
        content = read_file_safe(path)
        lines = content.split('\n') if content else []
        
        return {
            'path': str(path_obj),
            'name': path_obj.name,
            'size_bytes': stat.st_size,
            'modified': stat.st_mtime,
            'lines': len(lines),
            'extension': path_obj.suffix
        }
    except Exception as e:
        logger.error(f"Error getting file stats for {path}: {e}")
        return {}


def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
    
    Returns:
        True if directory exists or was created successfully
    """
    path_obj = Path(path)
    
    try:
        path_obj.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path}")
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Get relative path from base path.
    
    Args:
        file_path: Full file path
        base_path: Base directory path
    
    Returns:
        Relative path string
    """
    try:
        return str(Path(file_path).relative_to(Path(base_path)))
    except ValueError:
        return str(Path(file_path))

