"""
Legacy Code Parsers

Provides parsing utilities for COBOL, Visual Basic, and Java legacy code.
"""

import re
from typing import Dict, List, Optional, Tuple
from loguru import logger


class CobolParser:
    """Parser for COBOL code"""
    
    def __init__(self):
        self.divisions = ['IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE']
        self.sections = []
        self.paragraphs = []
        self.variables = []
        self.procedures = []
    
    def parse(self, content: str) -> Dict:
        """
        Parse COBOL source code.
        
        Args:
            content: COBOL source code as string
        
        Returns:
            Dictionary containing parsed structure
        """
        lines = content.split('\n')
        result = {
            'language': 'cobol',
            'divisions': {},
            'variables': [],
            'procedures': [],
            'paragraphs': [],
            'calls': [],
            'line_count': len(lines)
        }
        
        current_division = None
        current_section = None
        in_working_storage = False
        
        for line_num, line in enumerate(lines, 1):
            # Remove comments (lines starting with * in column 7)
            if len(line) > 6 and line[6] == '*':
                continue
            
            # Clean line
            clean_line = line.strip().upper()
            
            # Detect divisions
            for division in self.divisions:
                if f'{division} DIVISION' in clean_line:
                    current_division = division
                    result['divisions'][division] = {'start_line': line_num, 'content': []}
                    logger.debug(f"Found {division} DIVISION at line {line_num}")
                    break
            
            # Detect WORKING-STORAGE SECTION
            if 'WORKING-STORAGE SECTION' in clean_line:
                in_working_storage = True
                current_section = 'WORKING-STORAGE'
                logger.debug(f"Entered WORKING-STORAGE SECTION at line {line_num}")
            
            # Parse variables in WORKING-STORAGE
            if in_working_storage and current_division == 'DATA':
                var_match = re.match(r'\s*(\d+)\s+([A-Z0-9\-]+)\s+PIC\s+([X9\(\)]+)', clean_line)
                if var_match:
                    level, name, pic = var_match.groups()
                    result['variables'].append({
                        'name': name,
                        'level': level,
                        'picture': pic,
                        'line': line_num
                    })
                    logger.debug(f"Found variable {name} at line {line_num}")
            
            # Detect PROCEDURE DIVISION
            if 'PROCEDURE DIVISION' in clean_line:
                in_working_storage = False
                current_division = 'PROCEDURE'
            
            # Parse paragraphs (procedure names)
            if current_division == 'PROCEDURE':
                # Paragraph names typically start at column 8 and end with a period
                para_match = re.match(r'\s*([A-Z][A-Z0-9\-]+)\.\s*$', clean_line)
                if para_match:
                    para_name = para_match.group(1)
                    result['paragraphs'].append({
                        'name': para_name,
                        'line_start': line_num,
                        'line_end': line_num  # Will be updated
                    })
                    logger.debug(f"Found paragraph {para_name} at line {line_num}")
            
            # Detect PERFORM statements (procedure calls)
            if 'PERFORM' in clean_line:
                perform_match = re.search(r'PERFORM\s+([A-Z][A-Z0-9\-]+)', clean_line)
                if perform_match:
                    called_para = perform_match.group(1)
                    result['calls'].append({
                        'type': 'PERFORM',
                        'target': called_para,
                        'line': line_num
                    })
                    logger.debug(f"Found PERFORM {called_para} at line {line_num}")
            
            # Add line to current division
            if current_division and current_division in result['divisions']:
                result['divisions'][current_division]['content'].append(line)
        
        # Update paragraph end lines
        for i, para in enumerate(result['paragraphs']):
            if i < len(result['paragraphs']) - 1:
                para['line_end'] = result['paragraphs'][i + 1]['line_start'] - 1
            else:
                para['line_end'] = len(lines)
        
        return result


class VBParser:
    """Parser for Visual Basic code"""
    
    def parse(self, content: str) -> Dict:
        """
        Parse Visual Basic source code.
        
        Args:
            content: VB source code as string
        
        Returns:
            Dictionary containing parsed structure
        """
        lines = content.split('\n')
        result = {
            'language': 'vb',
            'modules': [],
            'classes': [],
            'functions': [],
            'subs': [],
            'variables': [],
            'line_count': len(lines)
        }
        
        for line_num, line in enumerate(lines, 1):
            clean_line = line.strip()
            
            # Skip comments
            if clean_line.startswith("'"):
                continue
            
            # Parse Sub declarations
            sub_match = re.match(r'(Public|Private|Friend)?\s*Sub\s+(\w+)\s*\((.*?)\)', clean_line, re.IGNORECASE)
            if sub_match:
                visibility, name, params = sub_match.groups()
                result['subs'].append({
                    'name': name,
                    'visibility': visibility or 'Public',
                    'parameters': params,
                    'line_start': line_num
                })
                logger.debug(f"Found Sub {name} at line {line_num}")
            
            # Parse Function declarations
            func_match = re.match(r'(Public|Private|Friend)?\s*Function\s+(\w+)\s*\((.*?)\)\s*As\s+(\w+)', clean_line, re.IGNORECASE)
            if func_match:
                visibility, name, params, return_type = func_match.groups()
                result['functions'].append({
                    'name': name,
                    'visibility': visibility or 'Public',
                    'parameters': params,
                    'return_type': return_type,
                    'line_start': line_num
                })
                logger.debug(f"Found Function {name} at line {line_num}")
            
            # Parse variable declarations
            var_match = re.match(r'Dim\s+(\w+)\s+As\s+(\w+)', clean_line, re.IGNORECASE)
            if var_match:
                name, var_type = var_match.groups()
                result['variables'].append({
                    'name': name,
                    'type': var_type,
                    'line': line_num
                })
        
        return result


class JavaParser:
    """Parser for Java code"""
    
    def parse(self, content: str) -> Dict:
        """
        Parse Java source code.
        
        Args:
            content: Java source code as string
        
        Returns:
            Dictionary containing parsed structure
        """
        lines = content.split('\n')
        result = {
            'language': 'java',
            'package': None,
            'imports': [],
            'classes': [],
            'methods': [],
            'fields': [],
            'line_count': len(lines)
        }
        
        in_multiline_comment = False
        
        for line_num, line in enumerate(lines, 1):
            clean_line = line.strip()
            
            # Handle multi-line comments
            if '/*' in clean_line:
                in_multiline_comment = True
            if '*/' in clean_line:
                in_multiline_comment = False
                continue
            if in_multiline_comment:
                continue
            
            # Skip single-line comments
            if clean_line.startswith('//'):
                continue
            
            # Parse package declaration
            package_match = re.match(r'package\s+([\w.]+);', clean_line)
            if package_match:
                result['package'] = package_match.group(1)
            
            # Parse imports
            import_match = re.match(r'import\s+([\w.*]+);', clean_line)
            if import_match:
                result['imports'].append(import_match.group(1))
            
            # Parse class declarations
            class_match = re.match(r'(public|private|protected)?\s*(abstract|final)?\s*class\s+(\w+)', clean_line)
            if class_match:
                visibility, modifier, name = class_match.groups()
                result['classes'].append({
                    'name': name,
                    'visibility': visibility or 'default',
                    'modifier': modifier,
                    'line_start': line_num
                })
                logger.debug(f"Found class {name} at line {line_num}")
            
            # Parse method declarations
            method_match = re.match(r'(public|private|protected)?\s*(static)?\s*([\w<>]+)\s+(\w+)\s*\((.*?)\)', clean_line)
            if method_match and not clean_line.startswith('class'):
                visibility, static, return_type, name, params = method_match.groups()
                result['methods'].append({
                    'name': name,
                    'visibility': visibility or 'default',
                    'static': static is not None,
                    'return_type': return_type,
                    'parameters': params,
                    'line_start': line_num
                })
                logger.debug(f"Found method {name} at line {line_num}")
            
            # Parse field declarations
            field_match = re.match(r'(public|private|protected)?\s*(static|final)?\s*([\w<>]+)\s+(\w+)\s*[;=]', clean_line)
            if field_match and '{' not in clean_line and '(' not in clean_line:
                visibility, modifier, field_type, name = field_match.groups()
                result['fields'].append({
                    'name': name,
                    'type': field_type,
                    'visibility': visibility or 'default',
                    'modifier': modifier,
                    'line': line_num
                })
        
        return result


def get_parser(language: str):
    """
    Get appropriate parser for a language.
    
    Args:
        language: Language identifier ('cobol', 'vb', 'java')
    
    Returns:
        Parser instance
    """
    parsers = {
        'cobol': CobolParser(),
        'vb': VBParser(),
        'java': JavaParser()
    }
    
    return parsers.get(language.lower())

