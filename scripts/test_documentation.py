"""
Test script for Documentation Agent (Agent 2)

This script tests the documentation generation functionality.
"""

import os
import sys
import yaml
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.documentation import DocumentationAgent


def load_config():
    """Load agent configuration."""
    config_path = project_root / 'config' / 'agent_configs.yaml'
    
    logger.info(f"Loading configuration from {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('documentation', {})


def test_documentation_agent():
    """Test the documentation agent."""
    logger.info("=" * 60)
    logger.info("Testing Documentation Agent (The Scribe)")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config()
    logger.info(f"Configuration loaded: {config.get('name')}")
    
    # Initialize agent
    logger.info("\n1. Initializing Documentation Agent...")
    agent = DocumentationAgent(config)
    logger.success("✓ Agent initialized successfully")
    
    # Find analysis report
    analysis_report_path = project_root / 'output' / 'analysis' / 'analysis_report.json'
    
    if not analysis_report_path.exists():
        logger.error(f"Analysis report not found: {analysis_report_path}")
        logger.info("Please run test_analyzer.py first to generate the analysis report")
        return False
    
    logger.info(f"\n2. Found analysis report: {analysis_report_path}")
    
    # Generate documentation
    logger.info("\n3. Generating documentation...")
    try:
        result = agent.generate_documentation(str(analysis_report_path))
        logger.success("✓ Documentation generated successfully")
        
        # Display results
        logger.info("\n4. Generated Documentation Files:")
        logger.info("-" * 60)
        for filename, filepath in result.items():
            file_size = os.path.getsize(filepath)
            logger.info(f"  ✓ {filename:30} ({file_size:,} bytes)")
            logger.info(f"    Path: {filepath}")
        
        # Display sample content from README
        logger.info("\n5. Sample Content from README.md:")
        logger.info("-" * 60)
        readme_path = result.get('README.md')
        if readme_path:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Show first 500 characters
                preview = content[:500]
                logger.info(preview)
                if len(content) > 500:
                    logger.info(f"\n... (showing first 500 of {len(content)} characters)")
        
        # Display sample from inline comments
        logger.info("\n6. Sample Inline Comments:")
        logger.info("-" * 60)
        comments_path = result.get('inline_comments.json')
        if comments_path:
            import json
            with open(comments_path, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)
                total = comments_data.get('total', 0)
                comments = comments_data.get('comments', [])
                logger.info(f"Total comments generated: {total}")
                if comments:
                    logger.info("\nFirst comment:")
                    first_comment = comments[0]
                    logger.info(f"  Function: {first_comment.get('function')}")
                    logger.info(f"  File: {Path(first_comment.get('file', '')).name}")
                    logger.info(f"  Line: {first_comment.get('line')}")
                    logger.info(f"  Comment: {first_comment.get('comment')}")
        
        # Display architecture diagram sample
        logger.info("\n7. Sample from ARCHITECTURE.md:")
        logger.info("-" * 60)
        arch_path = result.get('ARCHITECTURE.md')
        if arch_path:
            with open(arch_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find and show the data flow diagram
                if 'Data Flow' in content:
                    start = content.find('## Data Flow')
                    end = content.find('##', start + 1)
                    if end == -1:
                        end = start + 500
                    diagram_section = content[start:end]
                    logger.info(diagram_section[:400])
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Documentation Generation Summary")
        logger.info("=" * 60)
        logger.info(f"✓ Total files generated: {len(result)}")
        logger.info(f"✓ Output directory: {project_root / 'output' / 'documentation'}")
        logger.info("\nGenerated files:")
        for filename in result.keys():
            logger.info(f"  - {filename}")
        
        logger.success("\n✓ All tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Documentation generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    # Configure logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Run test
    success = test_documentation_agent()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("Next Steps:")
        logger.info("=" * 60)
        logger.info("1. Review generated documentation in output/documentation/")
        logger.info("2. Check README.md for project overview")
        logger.info("3. Review ARCHITECTURE.md for technical details")
        logger.info("4. Check inline_comments.json for code comments")
        logger.info("5. Review TECHNICAL_DEBT.md for improvement areas")
        sys.exit(0)
    else:
        logger.error("\nTests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()

