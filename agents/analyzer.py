"""
Code Analyzer Agent (The Archaeologist)

Analyzes legacy code and produces comprehensive analysis reports.
This is Agent 1 in the modernization pipeline.
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

from loguru import logger

# Make IBM watsonx imports optional
try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    WATSONX_AVAILABLE = True
except ImportError:
    logger.warning("IBM watsonx AI library not installed. AI insights will be disabled.")
    WATSONX_AVAILABLE = False
    APIClient = None
    Credentials = None
    ModelInference = None

from utils.file_handler import walk_directory, read_file_safe, ensure_directory, get_file_stats
from utils.validators import (
    validate_directory, 
    validate_language, 
    get_language_extensions,
    detect_language_from_extension,
    validate_output_path
)
from utils.parsers import get_parser


class CodeAnalyzer:
    """
    Code Analyzer Agent that analyzes legacy code and produces detailed reports.
    
    This agent:
    - Detects programming language
    - Parses code structure (AST)
    - Extracts functions and their metadata
    - Analyzes dependencies
    - Detects technical debt
    - Uses IBM Granite for semantic insights
    """
    
    def __init__(self, config: dict):
        """
        Initialize the Code Analyzer.
        
        Args:
            config: Agent configuration from agent_configs.yaml
        """
        self.config = config
        self.name = config.get('name', 'Code Analyzer')
        self.model_id = config.get('model', 'ibm/granite-13b-instruct-v2')
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.1)
        self.timeout = config.get('timeout', 120)
        
        # Initialize IBM watsonx client
        self.watsonx_client = None
        self._init_watsonx_client()
        
        logger.info(f"Initialized {self.name} with model {self.model_id}")
    
    def _init_watsonx_client(self):
        """Initialize IBM watsonx AI client."""
        if not WATSONX_AVAILABLE:
            logger.warning("IBM watsonx AI library not available. AI insights will be disabled.")
            self.watsonx_client = None
            return
        
        try:
            api_key = os.getenv('WATSONX_API_KEY')
            project_id = os.getenv('WATSONX_PROJECT_ID')
            region = os.getenv('WATSONX_REGION', 'us-south')
            
            if not api_key or not project_id:
                logger.warning("IBM watsonx credentials not found. AI insights will be disabled.")
                return
            
            # Create credentials
            credentials = Credentials(
                api_key=api_key,
                url=f"https://{region}.ml.cloud.ibm.com"
            )
            
            # Create API client
            self.watsonx_client = APIClient(credentials)
            self.watsonx_client.set.default_project(project_id)
            
            logger.info("IBM watsonx client initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize IBM watsonx client: {e}")
            self.watsonx_client = None
    
    def analyze_directory(self, directory_path: str) -> Dict:
        """
        Main entry point for code analysis.
        
        Args:
            directory_path: Path to directory containing legacy code
        
        Returns:
            Complete analysis report as dictionary
        """
        logger.info(f"Starting analysis of directory: {directory_path}")
        
        # Validate directory
        if not validate_directory(directory_path):
            raise ValueError(f"Invalid directory: {directory_path}")
        
        # Detect language
        language = self._detect_language(directory_path)
        logger.info(f"Detected language: {language}")
        
        # Parse files
        parsed_files = self._parse_files(directory_path, language)
        logger.info(f"Parsed {len(parsed_files)} files")
        
        # Extract functions
        functions = self._extract_functions(parsed_files)
        logger.info(f"Extracted {len(functions)} functions/procedures")
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies(parsed_files)
        logger.info(f"Analyzed dependencies: {len(dependencies.get('modules', []))} modules")
        
        # Detect technical debt
        warnings = self._detect_technical_debt(parsed_files, functions)
        logger.info(f"Detected {len(warnings)} warnings")
        
        # Calculate metadata
        total_lines = sum(f.get('line_count', 0) for f in parsed_files)
        
        # Build analysis report
        report = {
            'metadata': {
                'analyzed_at': datetime.utcnow().isoformat() + 'Z',
                'language': language,
                'total_files': len(parsed_files),
                'total_lines': total_lines,
                'analyzer_version': '1.0.0',
                'directory': directory_path
            },
            'dependencies': dependencies,
            'functions': functions,
            'warnings': warnings,
            'files': [
                {
                    'path': f.get('path'),
                    'lines': f.get('line_count', 0),
                    'language': f.get('language')
                }
                for f in parsed_files
            ]
        }
        
        logger.info("Analysis complete")
        return report
    
    def _detect_language(self, directory_path: str) -> str:
        """
        Detect primary programming language from file extensions.
        
        Args:
            directory_path: Directory to analyze
        
        Returns:
            Language identifier ('cobol', 'vb', 'java', or 'unknown')
        """
        language_counts = defaultdict(int)
        
        # Walk directory and count file extensions
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                language = detect_language_from_extension(file_path)
                if language != 'unknown':
                    language_counts[language] += 1
        
        if not language_counts:
            logger.warning(f"No supported language files found in {directory_path}")
            return 'unknown'
        
        # Return most common language
        primary_language = max(language_counts.items(), key=lambda x: x[1])[0]
        logger.info(f"Language detection: {dict(language_counts)}, primary: {primary_language}")
        
        return primary_language
    
    def _parse_files(self, directory_path: str, language: str) -> List[Dict]:
        """
        Parse all files in directory for the detected language.
        
        Args:
            directory_path: Directory containing source files
            language: Detected language
        
        Returns:
            List of parsed file objects
        """
        if not validate_language(language):
            logger.error(f"Cannot parse unsupported language: {language}")
            return []
        
        # Get file extensions for language
        extensions = get_language_extensions(language)
        
        # Find all matching files
        file_paths = walk_directory(directory_path, extensions)
        
        if not file_paths:
            logger.warning(f"No {language} files found in {directory_path}")
            return []
        
        # Parse each file
        parsed_files = []
        parser = get_parser(language)
        
        if not parser:
            logger.error(f"No parser available for language: {language}")
            return []
        
        for file_path in file_paths:
            try:
                content = read_file_safe(file_path)
                if not content:
                    logger.warning(f"Could not read file: {file_path}")
                    continue
                
                # Parse file
                parsed = parser.parse(content)
                parsed['path'] = file_path
                parsed['content'] = content
                
                # Build AST
                ast_data = self._build_ast(content, language, parsed)
                parsed['ast'] = ast_data
                
                parsed_files.append(parsed)
                logger.debug(f"Successfully parsed: {file_path}")
            
            except Exception as e:
                logger.error(f"Error parsing file {file_path}: {e}")
                continue
        
        return parsed_files
    
    def _build_ast(self, file_content: str, language: str, parsed_data: Dict) -> Dict:
        """
        Build Abstract Syntax Tree representation.
        
        Args:
            file_content: Source code content
            language: Programming language
            parsed_data: Already parsed data from language parser
        
        Returns:
            AST representation as dictionary
        """
        ast = {
            'type': 'Program',
            'language': language,
            'body': []
        }
        
        if language == 'cobol':
            # COBOL AST structure
            ast['body'] = [
                {
                    'type': 'Division',
                    'name': div_name,
                    'content': div_data.get('content', [])
                }
                for div_name, div_data in parsed_data.get('divisions', {}).items()
            ]
            
            # Add paragraphs as callable units
            ast['procedures'] = parsed_data.get('paragraphs', [])
        
        elif language == 'vb':
            # VB AST structure
            ast['body'] = [
                {'type': 'Sub', **sub}
                for sub in parsed_data.get('subs', [])
            ] + [
                {'type': 'Function', **func}
                for func in parsed_data.get('functions', [])
            ]
        
        elif language == 'java':
            # Java AST structure
            ast['package'] = parsed_data.get('package')
            ast['imports'] = parsed_data.get('imports', [])
            ast['body'] = [
                {'type': 'Class', **cls}
                for cls in parsed_data.get('classes', [])
            ]
            ast['methods'] = parsed_data.get('methods', [])
        
        return ast
    
    def _extract_functions(self, parsed_files: List[Dict]) -> List[Dict]:
        """
        Extract all function/procedure definitions with metadata.
        
        Args:
            parsed_files: List of parsed file objects
        
        Returns:
            List of function metadata dictionaries
        """
        functions = []
        
        for file_data in parsed_files:
            language = file_data.get('language')
            file_path = file_data.get('path')
            
            if language == 'cobol':
                # Extract COBOL paragraphs as functions
                for para in file_data.get('paragraphs', []):
                    func_data = {
                        'name': para['name'],
                        'parameters': [],  # COBOL paragraphs don't have explicit parameters
                        'return_type': 'void',
                        'line_start': para['line_start'],
                        'line_end': para['line_end'],
                        'file': file_path,
                        'language': 'cobol'
                    }
                    
                    # Calculate complexity and LOC
                    loc = para['line_end'] - para['line_start'] + 1
                    func_data['loc'] = loc
                    func_data['complexity'] = self._calculate_complexity_from_lines(
                        file_data.get('content', '').split('\n')[para['line_start']-1:para['line_end']]
                    )
                    
                    functions.append(func_data)
            
            elif language == 'vb':
                # Extract VB Subs
                for sub in file_data.get('subs', []):
                    func_data = {
                        'name': sub['name'],
                        'parameters': sub.get('parameters', '').split(',') if sub.get('parameters') else [],
                        'return_type': 'void',
                        'line_start': sub['line_start'],
                        'line_end': sub.get('line_end', sub['line_start'] + 10),
                        'file': file_path,
                        'language': 'vb',
                        'visibility': sub.get('visibility', 'Public')
                    }
                    
                    loc = func_data['line_end'] - func_data['line_start'] + 1
                    func_data['loc'] = loc
                    func_data['complexity'] = self._calculate_complexity_from_lines(
                        file_data.get('content', '').split('\n')[func_data['line_start']-1:func_data['line_end']]
                    )
                    
                    functions.append(func_data)
                
                # Extract VB Functions
                for func in file_data.get('functions', []):
                    func_data = {
                        'name': func['name'],
                        'parameters': func.get('parameters', '').split(',') if func.get('parameters') else [],
                        'return_type': func.get('return_type', 'Variant'),
                        'line_start': func['line_start'],
                        'line_end': func.get('line_end', func['line_start'] + 10),
                        'file': file_path,
                        'language': 'vb',
                        'visibility': func.get('visibility', 'Public')
                    }
                    
                    loc = func_data['line_end'] - func_data['line_start'] + 1
                    func_data['loc'] = loc
                    func_data['complexity'] = self._calculate_complexity_from_lines(
                        file_data.get('content', '').split('\n')[func_data['line_start']-1:func_data['line_end']]
                    )
                    
                    functions.append(func_data)
            
            elif language == 'java':
                # Extract Java methods
                for method in file_data.get('methods', []):
                    func_data = {
                        'name': method['name'],
                        'parameters': method.get('parameters', '').split(',') if method.get('parameters') else [],
                        'return_type': method.get('return_type', 'void'),
                        'line_start': method['line_start'],
                        'line_end': method.get('line_end', method['line_start'] + 10),
                        'file': file_path,
                        'language': 'java',
                        'visibility': method.get('visibility', 'default'),
                        'static': method.get('static', False)
                    }
                    
                    loc = func_data['line_end'] - func_data['line_start'] + 1
                    func_data['loc'] = loc
                    func_data['complexity'] = self._calculate_complexity_from_lines(
                        file_data.get('content', '').split('\n')[func_data['line_start']-1:func_data['line_end']]
                    )
                    
                    functions.append(func_data)
        
        return functions
    
    def _calculate_complexity_from_lines(self, lines: List[str]) -> int:
        """
        Calculate cyclomatic complexity from code lines.
        
        Args:
            lines: List of code lines
        
        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity
        
        # Decision point keywords by language
        decision_keywords = [
            'IF', 'ELSE', 'ELIF', 'ELSEIF',
            'WHILE', 'FOR', 'FOREACH',
            'CASE', 'WHEN', 'SWITCH',
            'PERFORM', 'EVALUATE',
            'AND', 'OR', '&&', '||',
            'CATCH', 'EXCEPT'
        ]
        
        for line in lines:
            line_upper = line.upper()
            for keyword in decision_keywords:
                if keyword in line_upper:
                    complexity += 1
        
        return complexity
    
    def _analyze_dependencies(self, parsed_files: List[Dict]) -> Dict:
        """
        Build dependency graph between modules.
        
        Args:
            parsed_files: List of parsed file objects
        
        Returns:
            Dependency graph structure
        """
        dependencies = {
            'graph': {
                'nodes': [],
                'edges': []
            },
            'modules': []
        }
        
        # Build nodes (modules/files)
        for file_data in parsed_files:
            file_path = file_data.get('path')
            module_name = Path(file_path).stem
            
            dependencies['modules'].append({
                'name': module_name,
                'path': file_path,
                'language': file_data.get('language')
            })
            
            dependencies['graph']['nodes'].append({
                'id': module_name,
                'label': module_name,
                'path': file_path
            })
        
        # Build edges (dependencies)
        for file_data in parsed_files:
            source_module = Path(file_data.get('path')).stem
            language = file_data.get('language')
            
            if language == 'cobol':
                # COBOL PERFORM statements indicate dependencies
                for call in file_data.get('calls', []):
                    target = call.get('target')
                    if target:
                        dependencies['graph']['edges'].append({
                            'source': source_module,
                            'target': target,
                            'type': call.get('type', 'PERFORM')
                        })
            
            elif language == 'java':
                # Java imports indicate dependencies
                for import_stmt in file_data.get('imports', []):
                    dependencies['graph']['edges'].append({
                        'source': source_module,
                        'target': import_stmt,
                        'type': 'import'
                    })
        
        return dependencies
    
    def _detect_technical_debt(self, parsed_files: List[Dict], functions: List[Dict]) -> List[Dict]:
        """
        Detect code smells and technical debt.
        
        Args:
            parsed_files: List of parsed file objects
            functions: List of extracted functions
        
        Returns:
            List of warning dictionaries
        """
        warnings = []
        
        # Check for long functions
        for func in functions:
            loc = func.get('loc', 0)
            if loc > 50:
                warnings.append({
                    'type': 'long_function',
                    'severity': 'high' if loc > 100 else 'medium',
                    'message': f"Function '{func['name']}' is too long ({loc} lines)",
                    'location': f"{func['file']}:{func['line_start']}"
                })
        
        # Check for high complexity
        for func in functions:
            complexity = func.get('complexity', 0)
            if complexity > 10:
                warnings.append({
                    'type': 'high_complexity',
                    'severity': 'high' if complexity > 20 else 'medium',
                    'message': f"Function '{func['name']}' has high complexity ({complexity})",
                    'location': f"{func['file']}:{func['line_start']}"
                })
        
        # Check for global state (COBOL WORKING-STORAGE)
        for file_data in parsed_files:
            if file_data.get('language') == 'cobol':
                variables = file_data.get('variables', [])
                if len(variables) > 20:
                    warnings.append({
                        'type': 'global_state',
                        'severity': 'medium',
                        'message': f"File has many global variables ({len(variables)})",
                        'location': file_data.get('path')
                    })
        
        # Check for deeply nested code
        for file_data in parsed_files:
            content = file_data.get('content', '')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Count leading spaces/indentation
                indent_level = len(line) - len(line.lstrip())
                if indent_level > 32:  # More than 4 levels (assuming 8 spaces per level)
                    warnings.append({
                        'type': 'deep_nesting',
                        'severity': 'low',
                        'message': f"Deeply nested code detected (indent level {indent_level // 8})",
                        'location': f"{file_data.get('path')}:{line_num}"
                    })
        
        return warnings
    
    def _use_granite_for_insights(self, code: str, language: str) -> Dict:
        """
        Use IBM Granite model to extract semantic insights.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            AI-generated insights
        """
        if not self.watsonx_client:
            logger.warning("IBM watsonx client not available, skipping AI insights")
            return {'insights': 'AI insights unavailable - client not initialized'}
        
        try:
            prompt = f"""Analyze this {language} code and identify:
1. Purpose and main functionality
2. Key functions and their roles
3. Potential issues or bugs
4. Modernization opportunities

Code:
```{language}
{code[:2000]}  # Limit code length
```

Provide a concise analysis."""
            
            response = self._call_granite_model(prompt, self.max_tokens)
            
            return {
                'insights': response,
                'model': self.model_id,
                'generated_at': datetime.utcnow().isoformat() + 'Z'
            }
        
        except Exception as e:
            logger.error(f"Error getting AI insights: {e}")
            return {'insights': f'Error: {str(e)}'}
    
    def _call_granite_model(self, prompt: str, max_tokens: int) -> str:
        """
        Call IBM Granite model via watsonx.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
        
        Returns:
            Model response text
        """
        try:
            model = ModelInference(
                model_id=self.model_id,
                api_client=self.watsonx_client,
                params={
                    'max_new_tokens': max_tokens,
                    'temperature': self.temperature,
                    'top_p': 0.9,
                    'top_k': 50
                }
            )
            
            response = model.generate_text(prompt=prompt)
            return response
        
        except Exception as e:
            logger.error(f"Error calling Granite model: {e}")
            raise
    
    def analyze(self, code_path: str, language: str, output_dir: str) -> Dict:
        """
        Analyze a single legacy code file.

        This is the primary entry point used by the UI pipeline.
        Wraps analyze_directory() to support single-file analysis.

        Args:
            code_path: Path to the source code file
            language: Source language (cobol, vb, java)
            output_dir: Directory to save the analysis report

        Returns:
            Analysis report dictionary
        """
        import tempfile
        import shutil

        code_path = str(code_path)
        output_dir = str(output_dir)

        # Create a temporary directory with just this file so analyze_directory works
        tmp_dir = tempfile.mkdtemp()
        try:
            dest = os.path.join(tmp_dir, os.path.basename(code_path))
            shutil.copy2(code_path, dest)

            report = self.analyze_directory(tmp_dir)

            # Save report to output_dir
            ensure_directory(output_dir)
            report_path = os.path.join(output_dir, 'analysis_report.json')
            self.save_report(report, report_path)

            return report
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def save_report(self, report: Dict, output_path: str) -> bool:
        """
        Save analysis report to JSON file.
        
        Args:
            report: Analysis report dictionary
            output_path: Path to save the report
        
        Returns:
            True if saved successfully
        """
        try:
            # Validate output path
            if not validate_output_path(output_path):
                logger.error(f"Invalid output path: {output_path}")
                return False
            
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            ensure_directory(str(output_dir))
            
            # Write report
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Analysis report saved to: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving report to {output_path}: {e}")
            return False

