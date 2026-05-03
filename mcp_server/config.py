"""
MCP Server Configuration Management

This module provides configuration management for the MCP server using Pydantic.
All settings are loaded from environment variables with validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class MCPServerConfig(BaseModel):
    """MCP Server configuration loaded from environment variables"""
    
    # MCP Server Settings
    mcp_server_host: str = Field(
        default="localhost",
        description="Host address for MCP server"
    )
    mcp_server_port: int = Field(
        default=8765,
        ge=1024,
        le=65535,
        description="Port number for MCP server (1024-65535)"
    )
    
    # File Operation Settings
    workspace_directory: str = Field(
        default="./",
        description="Root workspace directory for file operations"
    )
    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum file size in MB (1-100)"
    )
    allowed_extensions: List[str] = Field(
        default=[
            ".py", ".java", ".cbl", ".cob", ".vb", ".js", ".ts",
            ".txt", ".md", ".json", ".yaml", ".yml", ".xml",
            ".html", ".css", ".sql", ".sh", ".bat"
        ],
        description="Allowed file extensions for read/write operations"
    )
    backup_enabled: bool = Field(
        default=True,
        description="Enable automatic backup before file writes"
    )
    backup_directory: str = Field(
        default="./backups",
        description="Directory for file backups"
    )
    
    # Test Execution Settings
    test_timeout_seconds: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Timeout for test execution in seconds (10-3600)"
    )
    pytest_args: List[str] = Field(
        default=["-v", "--tb=short", "--maxfail=5"],
        description="Default pytest arguments"
    )
    
    # GitHub Integration Settings
    github_token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional)"
    )
    github_repo: Optional[str] = Field(
        default=None,
        description="GitHub repository in format 'owner/repo' (optional)"
    )
    github_default_branch: str = Field(
        default="main",
        description="Default branch for GitHub operations"
    )
    github_enabled: bool = Field(
        default=False,
        description="Enable GitHub integration"
    )
    
    # Application Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    output_directory: str = Field(
        default="./output",
        description="Directory for output files"
    )
    
    # Security Settings
    enable_path_validation: bool = Field(
        default=True,
        description="Enable path traversal validation"
    )
    enable_content_sanitization: bool = Field(
        default=True,
        description="Enable content sanitization"
    )
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""
        extra = "ignore"
    
    @field_validator("workspace_directory", "output_directory", "backup_directory")
    @classmethod
    def validate_directory_path(cls, v: str) -> str:
        """Validate and normalize directory paths"""
        path = Path(v).resolve()
        return str(path)
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @field_validator("github_repo")
    @classmethod
    def validate_github_repo(cls, v: Optional[str]) -> Optional[str]:
        """Validate GitHub repository format"""
        if v is None:
            return v
        if "/" not in v:
            raise ValueError("github_repo must be in format 'owner/repository'")
        parts = v.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError("github_repo must be in format 'owner/repository'")
        return v
    
    def model_post_init(self, __context) -> None:
        """Post-initialization validation and setup"""
        # Enable GitHub if token and repo are provided
        if self.github_token and self.github_repo:
            object.__setattr__(self, 'github_enabled', True)
        
        # Create necessary directories
        for directory in [self.workspace_directory, self.output_directory, self.backup_directory]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    def is_allowed_extension(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        ext = Path(filename).suffix.lower()
        return ext in [e.lower() for e in self.allowed_extensions]
    
    def get_workspace_path(self) -> Path:
        """Get workspace directory as Path object"""
        return Path(self.workspace_directory)
    
    def get_output_path(self) -> Path:
        """Get output directory as Path object"""
        return Path(self.output_directory)
    
    def get_backup_path(self) -> Path:
        """Get backup directory as Path object"""
        return Path(self.backup_directory)


# Global configuration instance
_config: Optional[MCPServerConfig] = None


def get_config() -> MCPServerConfig:
    """
    Get the global configuration instance.
    Creates a new instance if one doesn't exist.
    
    Returns:
        MCPServerConfig: The configuration instance
    """
    global _config
    if _config is None:
        _config = MCPServerConfig()
    return _config


def reload_config() -> MCPServerConfig:
    """
    Reload configuration from environment variables.
    Useful for testing or when environment changes.
    
    Returns:
        MCPServerConfig: The new configuration instance
    """
    global _config
    load_dotenv(override=True)
    _config = MCPServerConfig()
    return _config


def validate_config() -> tuple[bool, Optional[str]]:
    """
    Validate the current configuration.
    
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        config = get_config()
        
        # Check workspace directory exists and is accessible
        workspace = config.get_workspace_path()
        if not workspace.exists():
            return False, f"Workspace directory does not exist: {workspace}"
        if not os.access(workspace, os.R_OK | os.W_OK):
            return False, f"Workspace directory is not readable/writable: {workspace}"
        
        # Check output directory is writable
        output = config.get_output_path()
        if not os.access(output, os.W_OK):
            return False, f"Output directory is not writable: {output}"
        
        # Check backup directory is writable if backups are enabled
        if config.backup_enabled:
            backup = config.get_backup_path()
            if not os.access(backup, os.W_OK):
                return False, f"Backup directory is not writable: {backup}"
        
        return True, None
        
    except Exception as e:
        return False, f"Configuration validation error: {str(e)}"

# Made with Bob
