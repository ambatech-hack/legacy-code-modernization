"""
MCP Server Package

This package provides the Model Context Protocol (MCP) server implementation
for the Legacy Code Modernization Squad project.

The MCP server exposes tools that allow agents to safely interact with:
- File system operations (read/write)
- Test execution (pytest)
- GitHub integration (pull requests)

Main Components:
- MCPServer: Main server class that handles tool registration and execution
- MCPServerConfig: Configuration management using Pydantic
- Tools: read_file, write_file, run_tests, create_pull_request

Usage:
    from mcp_server import MCPServer, get_config
    
    # Get configuration
    config = get_config()
    
    # Create and run server
    server = MCPServer()
    await server.run()

For standalone execution:
    python -m mcp_server.server
"""

from .config import (
    MCPServerConfig,
    get_config,
    reload_config,
    validate_config
)

from .server import (
    MCPServer,
    main,
    run_server
)

from .tools import (
    read_file,
    write_file,
    run_tests,
    create_pull_request,
    validate_path,
    validate_file_size,
    sanitize_content,
    SecurityError,
    ToolExecutionError
)

__version__ = "1.0.0"
__author__ = "Legacy Code Modernization Squad"

__all__ = [
    # Configuration
    "MCPServerConfig",
    "get_config",
    "reload_config",
    "validate_config",
    
    # Server
    "MCPServer",
    "main",
    "run_server",
    
    # Tools
    "read_file",
    "write_file",
    "run_tests",
    "create_pull_request",
    
    # Utilities
    "validate_path",
    "validate_file_size",
    "sanitize_content",
    
    # Exceptions
    "SecurityError",
    "ToolExecutionError",
    
    # Metadata
    "__version__",
    "__author__"
]

# Made with Bob
