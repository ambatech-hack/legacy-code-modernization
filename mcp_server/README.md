# MCP Server - Model Context Protocol Server

This directory contains the complete implementation of the MCP (Model Context Protocol) server for the Legacy Code Modernization Squad project.

## Overview

The MCP server acts as a secure intermediary between AI agents and file system operations. It exposes four main tools that allow agents to safely interact with the codebase:

1. **read_file** - Safely read file contents
2. **write_file** - Safely write content to files
3. **run_tests** - Execute pytest in specified directories
4. **create_pull_request** - Create GitHub pull requests

## Architecture

```
mcp_server/
├── __init__.py       # Package exports and initialization
├── config.py         # Configuration management with Pydantic
├── server.py         # Main MCP server implementation
├── tools.py          # Tool implementations (read_file, write_file, etc.)
└── README.md         # This file
```

## Components

### config.py
Configuration management using Pydantic with validation:
- Environment variable loading
- Path validation
- File size limits
- GitHub integration settings
- Security settings

**Key Classes:**
- `MCPServerConfig` - Main configuration model
- `get_config()` - Get global configuration instance
- `validate_config()` - Validate current configuration

### tools.py
Implementation of all four MCP tools with comprehensive error handling:

**Tool 1: read_file(path: str)**
- Validates path is within workspace
- Checks file exists and is readable
- Enforces max file size limit
- Returns file contents as string
- Handles encoding errors gracefully

**Tool 2: write_file(path: str, content: str)**
- Validates path is within workspace
- Creates backup of existing file
- Writes content with atomic operations
- Returns success status and file info
- Handles write errors with rollback

**Tool 3: run_tests(test_directory: str)**
- Validates test directory exists
- Executes pytest with timeout
- Captures stdout/stderr
- Parses test results (passed, failed, errors)
- Returns structured test results

**Tool 4: create_pull_request(title: str, branch: str, files: list)**
- Validates GitHub token is configured
- Creates new branch from main
- Commits specified files
- Creates pull request via GitHub API
- Fallback to local branch if GitHub unavailable

### server.py
Main MCP server implementation:
- Initializes MCP server with proper configuration
- Registers all four tools
- Implements request/response handling
- Adds logging for all operations
- Includes health check endpoint
- Handles graceful shutdown

**Key Classes:**
- `MCPServer` - Main server class
- `run_server()` - Synchronous wrapper to run server

## Security Features

### Path Traversal Prevention
- All paths are validated against the workspace directory
- Prevents access to files outside the workspace
- Blocks path traversal attempts (../, absolute paths)

### File Size Limits
- Configurable maximum file size (default: 10 MB)
- Enforced for both read and write operations
- Prevents memory exhaustion attacks

### Timeout Protection
- Test execution has configurable timeout (default: 300 seconds)
- Prevents long-running operations from blocking the server

### Safe File Operations
- Atomic writes using temporary files
- Automatic backups before modifications
- Rollback on write failures

### Input Sanitization
- Content sanitization for write operations
- Null byte removal
- UTF-8 encoding validation

### Error Messages
- Error messages don't leak sensitive information
- Detailed logging for debugging (separate from user-facing errors)

## Configuration

Configuration is loaded from environment variables (see `.env.example`):

```bash
# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8765

# Application Settings
WORKSPACE_DIRECTORY=./
OUTPUT_DIRECTORY=./output
MAX_FILE_SIZE_MB=10
LOG_LEVEL=INFO

# GitHub Configuration (Optional)
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/repository
GITHUB_DEFAULT_BRANCH=main
```

## Usage

### Starting the Server

**Using the startup script:**
```bash
python scripts/start_mcp_server.py
```

**With custom settings:**
```bash
python scripts/start_mcp_server.py --port 9000 --workspace /path/to/workspace
```

**Validate configuration only:**
```bash
python scripts/start_mcp_server.py --validate-only
```

**Direct execution:**
```bash
python -m mcp_server.server
```

### Using the Tools

**From Python code:**
```python
from mcp_server import read_file, write_file, run_tests, create_pull_request

# Read a file
result = read_file("src/main.py")
if result["success"]:
    print(result["content"])

# Write a file
result = write_file("output/result.txt", "Hello, World!")
if result["success"]:
    print(f"File written to: {result['path']}")

# Run tests
result = run_tests("tests/")
print(f"Tests passed: {result['passed']}/{result['total']}")

# Create pull request
result = create_pull_request(
    title="Refactor legacy code",
    branch="refactor/cobol-modernization",
    files=["src/main.py", "tests/test_main.py"]
)
if result["success"]:
    print(f"PR created: {result['pr_url']}")
```

**Via MCP Protocol:**
The server communicates via stdio using the MCP protocol. Agents can invoke tools by sending properly formatted MCP requests.

## Error Handling

Each tool returns a structured response with error information:

```python
{
    "success": bool,          # Whether the operation succeeded
    "error": str or None,     # Error message if failed
    # ... tool-specific fields
}
```

**Common Error Types:**
- `FileNotFoundError` - File doesn't exist
- `PermissionError` - Insufficient permissions
- `ValueError` - Invalid parameters
- `TimeoutError` - Operation exceeded timeout
- `SecurityError` - Security validation failed
- `RuntimeError` - General execution errors

## Logging

The server uses `loguru` for comprehensive logging:

- **Console output**: Colored, formatted logs to stderr
- **File output**: Rotated log files in `output/mcp_server.log`
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log rotation**: 10 MB per file, 7 days retention, compressed

## Testing

To test the MCP server:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_mcp_server.py -v

# Run with coverage
pytest tests/test_mcp_server.py --cov=mcp_server --cov-report=html
```

## Dependencies

Required packages (from `requirements.txt`):
- `mcp==0.9.0` - MCP protocol implementation
- `pydantic==2.5.0` - Configuration validation
- `loguru==0.7.2` - Logging
- `python-dotenv==1.0.0` - Environment variable loading
- `PyGithub==2.1.1` - GitHub API integration
- `pytest==8.0.0` - Test execution

## Troubleshooting

### Server won't start
- Check that all required environment variables are set
- Verify workspace directory exists and is accessible
- Check port is not already in use

### File operations fail
- Verify paths are relative to workspace directory
- Check file permissions
- Ensure file size is within limits

### Tests timeout
- Increase `TEST_TIMEOUT_SECONDS` in configuration
- Check test directory path is correct
- Verify pytest is installed

### GitHub integration fails
- Verify `GITHUB_TOKEN` is set and valid
- Check `GITHUB_REPO` format is correct (owner/repository)
- Ensure token has required permissions (repo access)
- Server will fallback to local mode if GitHub unavailable

## Development

### Adding New Tools

1. Implement the tool function in `tools.py`
2. Add proper error handling and validation
3. Register the tool in `server.py`
4. Update `__init__.py` exports
5. Add tests for the new tool
6. Update this README

### Code Style

- Follow PEP 8 guidelines
- Use type hints throughout
- Add comprehensive docstrings
- Include usage examples in docstrings

## License

Part of the Legacy Code Modernization Squad project.

## Support

For issues or questions, please refer to the main project documentation or contact the development team.