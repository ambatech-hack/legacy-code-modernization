"""
Validation Utilities

Provides validation functions for the Code Analyzer agent.
"""

import os
from pathlib import Path
from typing import List
from loguru import logger


# Supported languages and their file extensions
SUPPORTED_LANGUAGES = {
    'cobol': ['.cob', '.cbl', '.cpy'],
    'vb': ['.vb', '.bas', '.frm', '.cls'],
    'java': ['.java']
}


def validate_directory(path: str) -> bool:
    """
    Validate that a directory exists and is readable.
    
    Args:
        path: Directory path to validate
    
    Returns:
        True if directory is valid and readable
    """
    if not path:
        logger.error("Directory path is empty")
        return False
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        logger.error(f"Directory does not exist: {path}")
        return False
    
    if not path_obj.is_dir():
        logger.error(f"Path is not a directory: {path}")
        return False
    
    if not os.access(path, os.R_OK):
        logger.error(f"Directory is not readable: {path}")
        return False
    
    logger.debug(f"Directory validated: {path}")
    return True


def validate_language(language: str) -> bool:
    """
    Validate that a language is supported.
    
    Args:
        language: Language identifier (e.g., 'cobol', 'vb', 'java')
    
    Returns:
        True if language is supported
    """
    if not language:
        logger.error("Language is empty")
        return False
    
    language_lower = language.lower()
    
    if language_lower not in SUPPORTED_LANGUAGES:
        logger.error(f"Unsupported language: {language}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")
        return False
    
    logger.debug(f"Language validated: {language}")
    return True


def validate_file(path: str) -> bool:
    """
    Validate that a file exists and is readable.
    
    Args:
        path: File path to validate
    
    Returns:
        True if file is valid and readable
    """
    if not path:
        logger.error("File path is empty")
        return False
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        logger.error(f"File does not exist: {path}")
        return False
    
    if not path_obj.is_file():
        logger.error(f"Path is not a file: {path}")
        return False
    
    if not os.access(path, os.R_OK):
        logger.error(f"File is not readable: {path}")
        return False
    
    logger.debug(f"File validated: {path}")
    return True


def get_language_extensions(language: str) -> List[str]:
    """
    Get file extensions for a language.
    
    Args:
        language: Language identifier
    
    Returns:
        List of file extensions for the language
    """
    language_lower = language.lower()
    return SUPPORTED_LANGUAGES.get(language_lower, [])


def detect_language_from_extension(file_path: str) -> str:
    """
    Detect language from file extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Language identifier or 'unknown'
    """
    path_obj = Path(file_path)
    extension = path_obj.suffix.lower()
    
    for language, extensions in SUPPORTED_LANGUAGES.items():
        if extension in extensions:
            return language
    
    return 'unknown'


def validate_output_path(path: str) -> bool:
    """
    Validate that an output path can be written to.
    
    Args:
        path: Output file path
    
    Returns:
        True if path can be written to
    """
    if not path:
        logger.error("Output path is empty")
        return False
    
    path_obj = Path(path)
    parent_dir = path_obj.parent
    
    # Check if parent directory exists or can be created
    if not parent_dir.exists():
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created output directory: {parent_dir}")
        except Exception as e:
            logger.error(f"Cannot create output directory {parent_dir}: {e}")
            return False
    
    # Check if parent directory is writable
    if not os.access(parent_dir, os.W_OK):
        logger.error(f"Output directory is not writable: {parent_dir}")
        return False
    
    logger.debug(f"Output path validated: {path}")
    return True

