"""
Test script for Code Analyzer Agent

Tests the analyzer with the sample COBOL file.
"""

import os
import sys
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.analyzer import CodeAnalyzer
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def load_config():
    """Load agent configuration."""
    config_path = Path(__file__).parent.parent / 'config' / 'agent_configs.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config['analyzer']


def test_analyzer():
    """Test the Code Analyzer with sample COBOL file."""
    logger.info("=" * 60)
    logger.info("Testing Code Analyzer Agent")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config()
    logger.info(f"Loaded configuration: {config['name']}")
    
    # Initialize analyzer
    analyzer = CodeAnalyzer(config)
    logger.info("Analyzer initialized")
    
    # Test with sample COBOL directory
    sample_dir = Path(__file__).parent.parent / 'samples' / 'cobol'
    logger.info(f"Analyzing directory: {sample_dir}")
    
    try:
        # Run analysis
        report = analyzer.analyze_directory(str(sample_dir))
        
        # Display results
        logger.info("\n" + "=" * 60)
        logger.info("ANALYSIS RESULTS")
        logger.info("=" * 60)
        
        metadata = report['metadata']
        logger.info(f"\nMetadata:")
        logger.info(f"  Language: {metadata['language']}")
        logger.info(f"  Total Files: {metadata['total_files']}")
        logger.info(f"  Total Lines: {metadata['total_lines']}")
        logger.info(f"  Analyzed At: {metadata['analyzed_at']}")
        
        logger.info(f"\nFunctions/Procedures: {len(report['functions'])}")
        for func in report['functions']:
            logger.info(f"  - {func['name']}: {func['loc']} lines, complexity {func['complexity']}")
        
        logger.info(f"\nDependencies:")
        logger.info(f"  Modules: {len(report['dependencies']['modules'])}")
        logger.info(f"  Edges: {len(report['dependencies']['graph']['edges'])}")
        
        logger.info(f"\nWarnings: {len(report['warnings'])}")
        for warning in report['warnings']:
            logger.info(f"  [{warning['severity'].upper()}] {warning['type']}: {warning['message']}")
            logger.info(f"    Location: {warning['location']}")
        
        # Save report
        output_dir = Path(__file__).parent.parent / 'output' / 'analysis'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'analysis_report.json'
        
        if analyzer.save_report(report, str(output_path)):
            logger.info(f"\n✓ Report saved to: {output_path}")
        else:
            logger.error(f"\n✗ Failed to save report")
        
        logger.info("\n" + "=" * 60)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        return True
    
    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_analyzer()
    sys.exit(0 if success else 1)

