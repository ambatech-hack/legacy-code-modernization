#!/usr/bin/env python3
"""
MCP Server Startup Script

This script starts the MCP server with command-line argument support.

Usage:
    python scripts/start_mcp_server.py [--port PORT] [--workspace PATH]
    
Examples:
    # Start with default settings
    python scripts/start_mcp_server.py
    
    # Start with custom port
    python scripts/start_mcp_server.py --port 9000
    
    # Start with custom workspace
    python scripts/start_mcp_server.py --workspace /path/to/workspace
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path to import mcp_server
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server import run_server, get_config
from loguru import logger


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Start the MCP Server for Legacy Code Modernization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --port 9000
  %(prog)s --workspace /path/to/workspace
  %(prog)s --port 9000 --workspace /path/to/workspace --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Port number for MCP server (default: from config or 8765)"
    )
    
    parser.add_argument(
        "--workspace",
        type=str,
        help="Workspace directory path (default: from config or ./)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: from config or INFO)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        help="Host address for MCP server (default: from config or localhost)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration without starting server"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    # Override environment variables if command-line args provided
    if args.port:
        os.environ["MCP_SERVER_PORT"] = str(args.port)
    
    if args.workspace:
        os.environ["WORKSPACE_DIRECTORY"] = args.workspace
    
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    
    if args.host:
        os.environ["MCP_SERVER_HOST"] = args.host
    
    try:
        # Load configuration
        from mcp_server import reload_config, validate_config
        config = reload_config()
        
        # Display configuration
        print("=" * 60)
        print("MCP Server Configuration")
        print("=" * 60)
        print(f"Host:              {config.mcp_server_host}")
        print(f"Port:              {config.mcp_server_port}")
        print(f"Workspace:         {config.workspace_directory}")
        print(f"Output Directory:  {config.output_directory}")
        print(f"Backup Directory:  {config.backup_directory}")
        print(f"Max File Size:     {config.max_file_size_mb} MB")
        print(f"Test Timeout:      {config.test_timeout_seconds} seconds")
        print(f"Log Level:         {config.log_level}")
        print(f"GitHub Enabled:    {config.github_enabled}")
        if config.github_enabled:
            print(f"GitHub Repo:       {config.github_repo}")
        print("=" * 60)
        
        # Validate configuration
        is_valid, error = validate_config()
        if not is_valid:
            print(f"\n❌ Configuration validation failed: {error}")
            sys.exit(1)
        
        print("✅ Configuration validated successfully\n")
        
        # If validate-only mode, exit here
        if args.validate_only:
            print("Validation complete. Exiting (--validate-only mode).")
            sys.exit(0)
        
        # Start the server
        print("Starting MCP Server...")
        print("Press Ctrl+C to stop the server\n")
        
        run_server()
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Fatal error during startup")
        sys.exit(1)


if __name__ == "__main__":
    main()

