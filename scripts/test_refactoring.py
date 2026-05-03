"""
Test script for Refactoring Agent

This script tests the Refactoring Agent by:
1. Loading the sample COBOL code
2. Loading analysis and documentation from previous agents
3. Modernizing the code to Python
4. Generating unit tests
5. Running the tests
6. Displaying results
"""

import os
import sys
import yaml
import json
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.refactoring import RefactoringAgent
from utils.file_handler import ensure_directory


def load_config():
    """Load agent configuration."""
    config_path = Path(__file__).parent.parent / 'config' / 'agent_configs.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config['refactoring']


def test_refactoring_agent():
    """Test the Refactoring Agent with sample COBOL code."""
    logger.info("=" * 80)
    logger.info("Testing Refactoring Agent (The Architect)")
    logger.info("=" * 80)
    
    # Load configuration
    logger.info("\n1. Loading configuration...")
    config = load_config()
    logger.info(f"   Model: {config['model']}")
    logger.info(f"   Max tokens: {config['max_tokens']}")
    logger.info(f"   Temperature: {config['temperature']}")
    
    # Initialize agent
    logger.info("\n2. Initializing Refactoring Agent...")
    agent = RefactoringAgent(config)
    logger.info(f"   Agent: {agent.name}")
    logger.info(f"   Watsonx available: {agent.watsonx_client is not None}")
    
    # Set up paths
    base_dir = Path(__file__).parent.parent
    legacy_dir = base_dir / 'samples' / 'cobol'
    analysis_path = base_dir / 'output' / 'analysis' / 'analysis_report.json'
    comments_path = base_dir / 'output' / 'documentation' / 'inline_comments.json'
    output_dir = base_dir / 'output' / 'modernized'
    
    # Check if input files exist
    logger.info("\n3. Checking input files...")
    if not analysis_path.exists():
        logger.error(f"   Analysis report not found: {analysis_path}")
        logger.error("   Please run test_analyzer.py first")
        return False
    logger.info(f"   ✓ Analysis report found: {analysis_path}")
    
    if not comments_path.exists():
        logger.error(f"   Comments file not found: {comments_path}")
        logger.error("   Please run test_documentation.py first")
        return False
    logger.info(f"   ✓ Comments file found: {comments_path}")
    
    # Load and display analysis summary
    logger.info("\n4. Loading analysis report...")
    with open(analysis_path, 'r') as f:
        analysis = json.load(f)
    
    logger.info(f"   Language: {analysis['metadata']['language']}")
    logger.info(f"   Total files: {analysis['metadata']['total_files']}")
    logger.info(f"   Total lines: {analysis['metadata']['total_lines']}")
    logger.info(f"   Functions found: {len(analysis['functions'])}")
    
    # Load and display comments summary
    logger.info("\n5. Loading inline comments...")
    with open(comments_path, 'r') as f:
        comments = json.load(f)
    
    logger.info(f"   Total comments: {comments['total']}")
    
    # Modernize code
    logger.info("\n6. Modernizing legacy code...")
    logger.info(f"   Source: {legacy_dir}")
    logger.info(f"   Output: {output_dir}")
    
    try:
        results = agent.modernize_code(
            legacy_dir=str(legacy_dir),
            analysis_path=str(analysis_path),
            comments_path=str(comments_path),
            output_dir=str(output_dir)
        )
        
        logger.info("   ✓ Modernization complete!")
        
        # Display results
        logger.info("\n7. Modernization Results:")
        logger.info(f"   Files converted: {len(results['files'])}")
        for file_path in results['files']:
            logger.info(f"      - {Path(file_path).name}")
        
        logger.info(f"   Tests generated: {len(results['tests'])}")
        for test_path in results['tests']:
            logger.info(f"      - {Path(test_path).name}")
        
        # Display test results
        if results.get('test_results'):
            logger.info("\n8. Test Results:")
            test_results = results['test_results']
            
            if test_results.get('success'):
                logger.info("   ✓ All tests passed!")
            else:
                logger.warning("   ⚠ Some tests failed or pytest not available")
            
            if 'output' in test_results:
                logger.info(f"\n   Test output:\n{test_results['output']}")
        
        # Display warnings
        if results.get('warnings'):
            logger.info("\n9. Warnings:")
            for warning in results['warnings']:
                logger.warning(f"   - {warning}")
        
        # Show generated files
        logger.info("\n10. Generated Files:")
        for file_path in results['files']:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                logger.info(f"\n   {Path(file_path).name} ({len(lines)} lines):")
                logger.info("   " + "-" * 60)
                # Show first 30 lines
                for i, line in enumerate(lines[:30], 1):
                    logger.info(f"   {i:3d} | {line.rstrip()}")
                if len(lines) > 30:
                    logger.info(f"   ... ({len(lines) - 30} more lines)")
        
        # Show test files
        logger.info("\n11. Generated Test Files:")
        for test_path in results['tests']:
            if os.path.exists(test_path):
                with open(test_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                logger.info(f"\n   {Path(test_path).name} ({len(lines)} lines):")
                logger.info("   " + "-" * 60)
                # Show first 30 lines
                for i, line in enumerate(lines[:30], 1):
                    logger.info(f"   {i:3d} | {line.rstrip()}")
                if len(lines) > 30:
                    logger.info(f"   ... ({len(lines) - 30} more lines)")
        
        # Show modernization report
        report_path = output_dir / 'modernization_report.json'
        if report_path.exists():
            logger.info("\n12. Modernization Report:")
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            summary = report.get('summary', {})
            logger.info(f"   Files converted: {summary.get('files_converted', 0)}")
            logger.info(f"   Tests generated: {summary.get('tests_generated', 0)}")
            logger.info(f"   Original lines: {summary.get('original_lines', 0)}")
            logger.info(f"   Modernized lines: {summary.get('modernized_lines', 0)}")
            logger.info(f"   Line reduction: {summary.get('line_reduction', 0)}%")
            logger.info(f"   Tests passed: {summary.get('test_success', False)}")
            
            if report.get('improvements'):
                logger.info("\n   Improvements:")
                for improvement in report['improvements']:
                    logger.info(f"      ✓ {improvement}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ Refactoring Agent test completed successfully!")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Error during modernization: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main entry point."""
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Run test
    success = test_refactoring_agent()
    
    if success:
        logger.info("\n✓ All tests passed!")
        sys.exit(0)
    else:
        logger.error("\n✗ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()


