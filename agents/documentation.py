"""
Documentation Agent (The Scribe)

Generates comprehensive documentation from analysis reports.
This is Agent 2 in the modernization pipeline.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from loguru import logger

# Make IBM watsonx imports optional
try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    WATSONX_AVAILABLE = True
except ImportError:
    logger.warning("IBM watsonx AI library not installed. Using template-based generation.")
    WATSONX_AVAILABLE = False
    APIClient = None
    Credentials = None
    ModelInference = None

from utils.file_handler import read_file_safe, ensure_directory


class DocumentationAgent:
    """
    Documentation Agent that generates comprehensive documentation from analysis reports.
    
    This agent:
    - Generates project README.md
    - Creates inline code comments
    - Generates architecture documentation
    - Creates data flow diagrams (ASCII)
    - Documents dependencies and technical debt
    """
    
    def __init__(self, config: dict):
        """
        Initialize the Documentation Agent.
        
        Args:
            config: Agent configuration from agent_configs.yaml
        """
        self.config = config
        self.name = config.get('name', 'Documentation Agent')
        self.model_id = config.get('model', 'ibm/granite-13b-instruct-v2')
        self.max_tokens = config.get('max_tokens', 8192)
        self.temperature = config.get('temperature', 0.3)
        self.timeout = config.get('timeout', 180)
        
        # Initialize IBM watsonx client
        self.watsonx_client = None
        self.model_inference = None
        self._init_watsonx_client()
        
        logger.info(f"Initialized {self.name} with model {self.model_id}")
    
    def _init_watsonx_client(self):
        """Initialize IBM watsonx AI client."""
        if not WATSONX_AVAILABLE:
            logger.warning("IBM watsonx AI library not available. Using template-based generation.")
            return
        
        try:
            api_key = os.getenv('WATSONX_API_KEY')
            project_id = os.getenv('WATSONX_PROJECT_ID')
            region = os.getenv('WATSONX_REGION', 'us-south')
            
            if not api_key or not project_id:
                logger.warning("IBM watsonx credentials not found. Using template-based generation.")
                return
            
            # Create credentials
            credentials = Credentials(
                api_key=api_key,
                url=f"https://{region}.ml.cloud.ibm.com"
            )
            
            # Create API client
            self.watsonx_client = APIClient(credentials)
            self.watsonx_client.set.default_project(project_id)
            
            # Create model inference
            self.model_inference = ModelInference(
                model_id=self.model_id,
                api_client=self.watsonx_client,
                project_id=project_id
            )
            
            logger.info("IBM watsonx client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize IBM watsonx client: {e}")
            self.watsonx_client = None
            self.model_inference = None
    
    def generate_documentation(self, analysis_report_path: str) -> dict:
        """
        Main entry point for documentation generation.
        
        Args:
            analysis_report_path: Path to analysis report JSON
            
        Returns:
            Dictionary with paths to generated documentation files
        """
        logger.info(f"Starting documentation generation from {analysis_report_path}")
        
        # Load and validate analysis report
        analysis = self._load_analysis_report(analysis_report_path)
        
        # Generate all documentation
        logger.info("Generating README.md...")
        readme_content = self._generate_readme(analysis)
        
        logger.info("Generating ARCHITECTURE.md...")
        architecture_content = self._generate_architecture_doc(analysis)
        
        logger.info("Generating inline comments...")
        inline_comments = self._generate_inline_comments(analysis)
        
        logger.info("Generating DEPENDENCIES.md...")
        dependencies_content = self._generate_dependency_doc(analysis)
        
        logger.info("Generating TECHNICAL_DEBT.md...")
        technical_debt_content = self._generate_technical_debt_report(analysis)
        
        # Prepare documentation dictionary
        docs = {
            'README.md': readme_content,
            'ARCHITECTURE.md': architecture_content,
            'inline_comments.json': json.dumps(inline_comments, indent=2),
            'DEPENDENCIES.md': dependencies_content,
            'TECHNICAL_DEBT.md': technical_debt_content
        }
        
        # Save documentation
        output_dir = Path(analysis_report_path).parent.parent / 'documentation'
        result = self.save_documentation(docs, str(output_dir))
        
        logger.info("Documentation generation complete")
        return result
    
    def _load_analysis_report(self, path: str) -> dict:
        """
        Load and validate analysis report.
        
        Args:
            path: Path to analysis report JSON
            
        Returns:
            Parsed analysis report dictionary
        """
        logger.info(f"Loading analysis report from {path}")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Analysis report not found: {path}")
        
        content = read_file_safe(path)
        if not content:
            raise ValueError(f"Failed to read analysis report: {path}")
        
        try:
            analysis = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in analysis report: {e}")
        
        # Validate required fields
        required_fields = ['metadata', 'dependencies', 'functions', 'files']
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Missing required field in analysis report: {field}")
        
        logger.info("Analysis report loaded and validated successfully")
        return analysis
    
    def _generate_readme(self, analysis: dict) -> str:
        """
        Generate comprehensive README.md content.
        
        Args:
            analysis: Analysis report dictionary
            
        Returns:
            README markdown content
        """
        metadata = analysis.get('metadata', {})
        language = metadata.get('language', 'Unknown').upper()
        total_files = metadata.get('total_files', 0)
        total_lines = metadata.get('total_lines', 0)
        functions = analysis.get('functions', [])
        
        # Get project name from directory
        directory = metadata.get('directory', '')
        project_name = Path(directory).name if directory else "Legacy Code Project"
        
        # Use AI to generate project overview if available
        overview = self._use_granite_for_descriptions(
            context=f"Language: {language}, Files: {total_files}, Lines: {total_lines}, Functions: {len(functions)}",
            doc_type="overview"
        )
        
        # Build README content
        template = self._get_readme_template()
        
        # Extract features from functions
        features = []
        for func in functions[:10]:  # Top 10 functions
            func_name = func.get('name', 'Unknown')
            features.append(f"- **{func_name}**: Core functionality component")
        
        features_text = "\n".join(features) if features else "- Core business logic implementation"
        
        # Generate installation instructions based on language
        install_instructions = self._get_installation_instructions(language)
        
        # Generate usage examples
        usage_examples = self._get_usage_examples(language, functions)
        
        # Fill template
        readme = template.format(
            project_name=project_name,
            language=language,
            overview=overview,
            features=features_text,
            total_files=total_files,
            total_lines=total_lines,
            function_count=len(functions),
            installation=install_instructions,
            usage=usage_examples
        )
        
        return readme
    
    def _generate_architecture_doc(self, analysis: dict) -> str:
        """
        Generate ARCHITECTURE.md content.
        
        Args:
            analysis: Analysis report dictionary
            
        Returns:
            Architecture markdown content
        """
        metadata = analysis.get('metadata', {})
        dependencies = analysis.get('dependencies', {})
        functions = analysis.get('functions', [])
        
        language = metadata.get('language', 'Unknown').upper()
        
        # Use AI to generate system overview
        system_overview = self._use_granite_for_descriptions(
            context=f"System with {len(functions)} functions in {language}",
            doc_type="architecture"
        )
        
        # Generate component descriptions
        components_text = self._generate_component_descriptions(functions)
        
        # Generate data flow diagram
        data_flow = self._create_flow_diagram(dependencies.get('graph', {}))
        
        # Generate dependency tree
        dependency_tree = self._create_dependency_tree(dependencies.get('graph', {}))
        
        # Get template and fill
        template = self._get_architecture_template()
        
        architecture = template.format(
            language=language,
            system_overview=system_overview,
            components=components_text,
            data_flow=data_flow,
            dependency_tree=dependency_tree,
            function_count=len(functions)
        )
        
        return architecture
    
    def _generate_inline_comments(self, analysis: dict) -> dict:
        """
        Generate structured inline comments for each function.
        
        Args:
            analysis: Analysis report dictionary
            
        Returns:
            Dictionary with structured comments
        """
        functions = analysis.get('functions', [])
        comments = []
        
        for func in functions:
            func_name = func.get('name', 'Unknown')
            file_path = func.get('file', '')
            line_start = func.get('line_start', 0)
            complexity = func.get('complexity', 0)
            parameters = func.get('parameters', [])
            return_type = func.get('return_type', 'void')
            
            # Generate comment using AI or template
            comment_text = self._use_granite_for_descriptions(
                context=f"Function: {func_name}, Complexity: {complexity}, Parameters: {len(parameters)}, Returns: {return_type}",
                doc_type="function"
            )
            
            # Create structured comment
            comment = {
                "file": file_path,
                "line": line_start,
                "function": func_name,
                "comment": comment_text,
                "parameters": parameters,
                "return_type": return_type,
                "complexity": complexity
            }
            
            comments.append(comment)
        
        return {"comments": comments, "total": len(comments)}
    
    def _generate_dependency_doc(self, analysis: dict) -> str:
        """
        Generate DEPENDENCIES.md content.
        
        Args:
            analysis: Analysis report dictionary
            
        Returns:
            Dependency markdown content
        """
        dependencies = analysis.get('dependencies', {})
        modules = dependencies.get('modules', [])
        graph = dependencies.get('graph', {})
        
        # Create dependency tree
        dep_tree = self._create_dependency_tree(graph)
        
        # Document modules
        modules_text = "## Modules\n\n"
        for module in modules:
            name = module.get('name', 'Unknown')
            path = module.get('path', '')
            language = module.get('language', 'Unknown')
            modules_text += f"### {name}\n"
            modules_text += f"- **Path**: `{path}`\n"
            modules_text += f"- **Language**: {language}\n\n"
        
        # Explain relationships
        relationships = self._explain_relationships(graph)
        
        content = f"""# Dependencies Documentation

## Overview

This document describes the module dependencies and relationships in the codebase.

{modules_text}

## Dependency Tree

```
{dep_tree}
```

## Relationships

{relationships}

## Analysis

- **Total Modules**: {len(modules)}
- **Total Dependencies**: {len(graph.get('edges', []))}

---
*Generated by Documentation Agent*
"""
        
        return content
    
    def _generate_technical_debt_report(self, analysis: dict) -> str:
        """
        Generate TECHNICAL_DEBT.md content.
        
        Args:
            analysis: Analysis report dictionary
            
        Returns:
            Technical debt markdown content
        """
        warnings = analysis.get('warnings', [])
        functions = analysis.get('functions', [])
        
        # Categorize warnings by severity
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for warning in warnings:
            severity = warning.get('severity', 'medium')
            if severity == 'high':
                high_priority.append(warning)
            elif severity == 'medium':
                medium_priority.append(warning)
            else:
                low_priority.append(warning)
        
        # Analyze complexity
        high_complexity_funcs = [f for f in functions if f.get('complexity', 0) > 10]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(warnings, high_complexity_funcs)
        
        # Get template and fill
        template = self._get_technical_debt_template()
        
        high_text = self._format_warnings(high_priority) if high_priority else "No high priority issues found."
        medium_text = self._format_warnings(medium_priority) if medium_priority else "No medium priority issues found."
        low_text = self._format_warnings(low_priority) if low_priority else "No low priority issues found."
        
        complexity_text = ""
        if high_complexity_funcs:
            complexity_text = "### High Complexity Functions\n\n"
            for func in high_complexity_funcs[:5]:
                complexity_text += f"- **{func.get('name')}**: Complexity {func.get('complexity')} (Line {func.get('line_start')})\n"
        
        debt = template.format(
            total_warnings=len(warnings),
            high_count=len(high_priority),
            medium_count=len(medium_priority),
            low_count=len(low_priority),
            high_priority=high_text,
            medium_priority=medium_text,
            low_priority=low_text,
            complexity_issues=complexity_text,
            recommendations=recommendations
        )
        
        return debt
    
    def _create_ascii_diagram(self, graph: dict) -> str:
        """
        Convert dependency graph to ASCII art diagram.
        
        Args:
            graph: Dependency graph dictionary
            
        Returns:
            ASCII diagram string
        """
        return self._create_flow_diagram(graph)
    
    def _create_dependency_tree(self, graph: dict) -> str:
        """
        Create tree-style ASCII representation of dependencies.
        
        Args:
            graph: Dependency graph dictionary
            
        Returns:
            ASCII tree string
        """
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        
        if not nodes:
            return "No dependencies found"
        
        # Build tree structure
        tree = []
        root_nodes = [n for n in nodes if not any(e.get('target') == n.get('id') for e in edges)]
        
        if not root_nodes:
            root_nodes = nodes[:1]  # Use first node as root if no clear root
        
        for root in root_nodes:
            tree.append(f"📦 {root.get('label', root.get('id', 'Unknown'))}")
            self._add_children_to_tree(root.get('id'), edges, nodes, tree, "  ")
        
        return "\n".join(tree)
    
    def _add_children_to_tree(self, parent_id: str, edges: list, nodes: list, tree: list, indent: str):
        """Helper to recursively add children to tree."""
        children = [e for e in edges if e.get('source') == parent_id]
        
        for i, edge in enumerate(children):
            target_id = edge.get('target')
            edge_type = edge.get('type', 'depends on')
            is_last = i == len(children) - 1
            
            # Find target node
            target_node = next((n for n in nodes if n.get('id') == target_id), None)
            target_label = target_node.get('label', target_id) if target_node else target_id
            
            prefix = "└── " if is_last else "├── "
            tree.append(f"{indent}{prefix}{target_label} ({edge_type})")
            
            # Recurse for children
            new_indent = indent + ("    " if is_last else "│   ")
            self._add_children_to_tree(target_id, edges, nodes, tree, new_indent)
    
    def _create_flow_diagram(self, graph: dict) -> str:
        """
        Create flow-style ASCII representation.
        
        Args:
            graph: Dependency graph dictionary
            
        Returns:
            ASCII flow diagram string
        """
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        
        if not nodes:
            return "No data flow to display"
        
        diagram = []
        diagram.append("┌─────────────────────────────────────┐")
        diagram.append("│         Data Flow Diagram           │")
        diagram.append("└─────────────────────────────────────┘")
        diagram.append("")
        
        for node in nodes:
            node_id = node.get('id', 'Unknown')
            node_label = node.get('label', node_id)
            
            diagram.append(f"  ┌─────────────────┐")
            diagram.append(f"  │  {node_label:^15}  │")
            diagram.append(f"  └─────────────────┘")
            
            # Show outgoing edges
            outgoing = [e for e in edges if e.get('source') == node_id]
            for edge in outgoing:
                target = edge.get('target', 'Unknown')
                edge_type = edge.get('type', 'calls')
                diagram.append(f"         │")
                diagram.append(f"         ↓ {edge_type}")
                diagram.append(f"  ┌─────────────────┐")
                diagram.append(f"  │  {target:^15}  │")
                diagram.append(f"  └─────────────────┘")
            
            diagram.append("")
        
        return "\n".join(diagram)
    
    def _use_granite_for_descriptions(self, context: str, doc_type: str) -> str:
        """
        Use IBM Granite model to generate natural language descriptions.
        
        Args:
            context: Context information for generation
            doc_type: Type of documentation (overview, function, architecture, recommendation)
            
        Returns:
            Generated description
        """
        # Define prompts for different types
        prompts = {
            "overview": f"""Based on this code analysis, generate a concise project overview (2-3 sentences):
{context}

Write a professional description of what this project does.""",
            
            "function": f"""Generate a clear, concise inline comment for this function:
{context}

Write a single-line comment explaining what this function does.""",
            
            "architecture": f"""Generate a technical architecture overview (2-3 sentences):
{context}

Explain the system architecture and design.""",
            
            "recommendation": f"""Generate a technical recommendation for this issue:
{context}

Provide a specific, actionable recommendation."""
        }
        
        prompt = prompts.get(doc_type, context)
        
        # Try to use AI model
        if self.model_inference:
            try:
                response = self._call_granite_model(prompt, max_tokens=512, temperature=self.temperature)
                return response.strip()
            except Exception as e:
                logger.warning(f"Failed to use Granite model: {e}. Using template.")
        
        # Fallback to template-based generation
        return self._get_template_description(context, doc_type)
    
    def _call_granite_model(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """
        Call IBM Granite model via watsonx.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Model response text
        """
        if not self.model_inference:
            raise RuntimeError("Model inference not initialized")
        
        params = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 50
        }
        
        response = self.model_inference.generate_text(prompt=prompt, params=params)
        return response
    
    def _get_template_description(self, context: str, doc_type: str) -> str:
        """Fallback template-based descriptions."""
        templates = {
            "overview": "This is a legacy codebase that requires modernization. The project contains business logic and data processing components.",
            "function": "This function performs a core operation in the system.",
            "architecture": "The system follows a modular architecture with clear separation of concerns.",
            "recommendation": "Consider refactoring this component to improve maintainability and reduce complexity."
        }
        return templates.get(doc_type, "Documentation generated from code analysis.")
    
    def _generate_component_descriptions(self, functions: list) -> str:
        """Generate descriptions for components."""
        if not functions:
            return "No components found."
        
        text = ""
        for func in functions[:10]:  # Top 10 functions
            name = func.get('name', 'Unknown')
            complexity = func.get('complexity', 0)
            loc = func.get('loc', 0)
            
            text += f"### {name}\n\n"
            text += f"- **Lines of Code**: {loc}\n"
            text += f"- **Complexity**: {complexity}\n"
            text += f"- **Type**: {'Complex' if complexity > 10 else 'Simple'} component\n\n"
        
        return text
    
    def _explain_relationships(self, graph: dict) -> str:
        """Explain module relationships."""
        edges = graph.get('edges', [])
        
        if not edges:
            return "No inter-module dependencies found."
        
        text = ""
        for edge in edges:
            source = edge.get('source', 'Unknown')
            target = edge.get('target', 'Unknown')
            edge_type = edge.get('type', 'depends on')
            
            text += f"- **{source}** {edge_type.lower()} **{target}**\n"
        
        return text
    
    def _generate_recommendations(self, warnings: list, high_complexity: list) -> str:
        """Generate recommendations for technical debt."""
        recommendations = []
        
        if warnings:
            recommendations.append("### Code Quality Issues")
            recommendations.append(f"- Address {len(warnings)} identified warnings")
            recommendations.append("- Implement code review process")
        
        if high_complexity:
            recommendations.append("\n### Complexity Reduction")
            recommendations.append(f"- Refactor {len(high_complexity)} high-complexity functions")
            recommendations.append("- Break down large functions into smaller units")
            recommendations.append("- Apply SOLID principles")
        
        if not recommendations:
            recommendations.append("No major technical debt identified. Continue with regular code maintenance.")
        
        return "\n".join(recommendations)
    
    def _format_warnings(self, warnings: list) -> str:
        """Format warnings for display."""
        if not warnings:
            return "None"
        
        text = ""
        for warning in warnings[:10]:  # Top 10
            message = warning.get('message', 'Unknown issue')
            file = warning.get('file', 'Unknown file')
            line = warning.get('line', 0)
            
            text += f"- **{message}** (File: `{Path(file).name}`, Line: {line})\n"
        
        return text
    
    def _get_installation_instructions(self, language: str) -> str:
        """Get installation instructions based on language."""
        instructions = {
            "COBOL": """```bash
# Install GnuCOBOL compiler
sudo apt-get install gnucobol

# Compile the program
cobc -x -free program.cbl

# Run the program
./program
```""",
            "JAVA": """```bash
# Ensure Java JDK is installed
java -version

# Compile the program
javac Program.java

# Run the program
java Program
```""",
            "VB": """```bash
# Install Mono (for Linux/Mac) or use Visual Studio (Windows)
mono Program.exe
```"""
        }
        
        return instructions.get(language, "Installation instructions not available for this language.")
    
    def _get_usage_examples(self, language: str, functions: list) -> str:
        """Generate usage examples."""
        if not functions:
            return "No usage examples available."
        
        examples = f"""```{language.lower()}
# Example usage of main functions

"""
        
        for func in functions[:3]:  # Top 3 functions
            name = func.get('name', 'Unknown')
            examples += f"# Call {name}\n"
            examples += f"{name}()\n\n"
        
        examples += "```"
        return examples
    
    def _get_readme_template(self) -> str:
        """Return README.md template."""
        return """# {project_name}

## Overview

{overview}

**Language**: {language}  
**Total Files**: {total_files}  
**Total Lines**: {total_lines}  
**Functions**: {function_count}

## Features

{features}

## Installation

{installation}

## Usage

{usage}

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical architecture.

## Documentation

- [Architecture Documentation](ARCHITECTURE.md)
- [Dependencies](DEPENDENCIES.md)
- [Technical Debt Report](TECHNICAL_DEBT.md)

## Contributing

This is a legacy codebase undergoing modernization. Please refer to the documentation before making changes.

---
*Documentation generated by IBM Bob Documentation Agent*
"""
    
    def _get_architecture_template(self) -> str:
        """Return ARCHITECTURE.md template."""
        return """# Architecture Documentation

## System Overview

{system_overview}

**Language**: {language}  
**Total Functions**: {function_count}

## Components

{components}

## Data Flow

{data_flow}

## Module Dependencies

{dependency_tree}

## Technical Specifications

- **Architecture Pattern**: Modular
- **Language**: {language}
- **Components**: {function_count} functions

---
*Generated by Documentation Agent*
"""
    
    def _get_technical_debt_template(self) -> str:
        """Return TECHNICAL_DEBT.md template."""
        return """# Technical Debt Report

## Summary

- **Total Issues**: {total_warnings}
- **High Priority**: {high_count}
- **Medium Priority**: {medium_count}
- **Low Priority**: {low_count}

## High Priority Issues

{high_priority}

## Medium Priority Issues

{medium_priority}

## Low Priority Issues

{low_priority}

## Complexity Issues

{complexity_issues}

## Recommendations

{recommendations}

---
*Generated by Documentation Agent*
"""
    
    def save_documentation(self, docs: dict, output_dir: str) -> dict:
        """
        Save all generated documentation files.
        
        Args:
            docs: Dictionary of filename -> content
            output_dir: Output directory path
            
        Returns:
            Dictionary with paths to saved files
        """
        logger.info(f"Saving documentation to {output_dir}")
        
        # Ensure output directory exists
        ensure_directory(output_dir)
        
        saved_files = {}
        
        for filename, content in docs.items():
            file_path = Path(output_dir) / filename
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                saved_files[filename] = str(file_path)
                logger.info(f"Saved {filename}")
                
            except Exception as e:
                logger.error(f"Failed to save {filename}: {e}")
                raise
        
        logger.info(f"Successfully saved {len(saved_files)} documentation files")
        return saved_files

# Made with Bob
