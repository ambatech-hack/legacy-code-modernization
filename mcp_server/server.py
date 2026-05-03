"""
MCP Server Implementation

This module implements the main MCP server that exposes tools to agents.
The server uses the MCP SDK to handle protocol communication and tool registration.
"""

import asyncio
import signal
import sys
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from loguru import logger

from .config import get_config, validate_config
from .tools import (
    read_file,
    write_file,
    run_tests,
    create_pull_request
)


class MCPServer:
    """
    MCP Server that exposes file operation and testing tools to agents.
    
    The server runs as a standalone process and communicates via stdio
    using the Model Context Protocol (MCP).
    """
    
    def __init__(self):
        """Initialize the MCP server"""
        self.config = get_config()
        self.server = Server("legacy-modernization-mcp")
        self._setup_logging()
        self._register_tools()
        self._shutdown_event = asyncio.Event()
    
    def _setup_logging(self):
        """Configure logging for the server"""
        logger.remove()  # Remove default handler
        
        # Add console handler
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.config.log_level,
            colorize=True
        )
        
        # Add file handler
        log_file = self.config.get_output_path() / "mcp_server.log"
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=self.config.log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip"
        )
        
        logger.info("MCP Server logging initialized")
    
    def _register_tools(self):
        """Register all MCP tools with the server"""
        
        # Tool 1: read_file
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools"""
            return [
                Tool(
                    name="read_file",
                    description="Safely read file contents from the workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the file within workspace"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="write_file",
                    description="Safely write content to a file in the workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the file within workspace"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                ),
                Tool(
                    name="run_tests",
                    description="Execute pytest in a specified directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "test_directory": {
                                "type": "string",
                                "description": "Path to the test directory"
                            }
                        },
                        "required": ["test_directory"]
                    }
                ),
                Tool(
                    name="create_pull_request",
                    description="Create a GitHub pull request with specified files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the pull request"
                            },
                            "branch": {
                                "type": "string",
                                "description": "Name of the source branch"
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of file paths to include in the PR"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description for the pull request"
                            }
                        },
                        "required": ["title", "branch", "files"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
            """Handle tool invocation requests"""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            try:
                # Route to appropriate tool
                if name == "read_file":
                    result = read_file(arguments["path"])
                
                elif name == "write_file":
                    result = write_file(
                        arguments["path"],
                        arguments["content"]
                    )
                
                elif name == "run_tests":
                    result = run_tests(arguments["test_directory"])
                
                elif name == "create_pull_request":
                    result = create_pull_request(
                        title=arguments["title"],
                        branch=arguments["branch"],
                        files=arguments["files"],
                        description=arguments.get("description")
                    )
                
                else:
                    error_msg = f"Unknown tool: {name}"
                    logger.error(error_msg)
                    result = {"success": False, "error": error_msg}
                
                # Log result
                if result.get("success"):
                    logger.info(f"Tool {name} completed successfully")
                else:
                    logger.warning(f"Tool {name} failed: {result.get('error')}")
                
                # Format result as TextContent
                import json
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
                
            except Exception as e:
                import json
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": error_msg
                    }, indent=2)
                )]
        
        logger.info("All tools registered successfully")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """
        Run the MCP server.
        
        This method starts the server and handles the main event loop.
        """
        try:
            # Validate configuration
            is_valid, error = validate_config()
            if not is_valid:
                logger.error(f"Configuration validation failed: {error}")
                raise RuntimeError(f"Invalid configuration: {error}")
            
            logger.info("Configuration validated successfully")
            logger.info(f"Workspace directory: {self.config.workspace_directory}")
            logger.info(f"Output directory: {self.config.output_directory}")
            logger.info(f"Max file size: {self.config.max_file_size_mb} MB")
            logger.info(f"GitHub integration: {'enabled' if self.config.github_enabled else 'disabled'}")
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            logger.info("Starting MCP server...")
            logger.info(f"Server ready on {self.config.mcp_server_host}:{self.config.mcp_server_port}")
            
            # Run the server using stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
            
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}", exc_info=True)
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the server"""
        logger.info("Shutting down MCP server...")
        
        # Perform cleanup tasks
        try:
            # Add any cleanup logic here
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
        
        logger.info("MCP server stopped")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the server.
        
        Returns:
            dict: Health check status
        """
        try:
            is_valid, error = validate_config()
            
            return {
                "status": "healthy" if is_valid else "unhealthy",
                "config_valid": is_valid,
                "error": error,
                "workspace": str(self.config.workspace_directory),
                "github_enabled": self.config.github_enabled
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


async def main():
    """Main entry point for the MCP server"""
    server = MCPServer()
    await server.run()


def run_server():
    """Synchronous wrapper to run the server"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_server()

# Made with Bob
