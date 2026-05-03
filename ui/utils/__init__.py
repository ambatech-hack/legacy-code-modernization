"""
Utility functions for Streamlit UI components.

Provides helper functions for:
- Configuration management
- File formatting
- UI components
- Error handling
"""

import os
import json
import yaml
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import streamlit as st
from loguru import logger


def load_config(config_path: str = "config/agent_configs.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: str = "config/settings.json") -> bool:
    """
    Save configuration to JSON file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def load_user_settings() -> Dict[str, Any]:
    """
    Load user settings from JSON file.
    
    Returns:
        User settings dictionary
    """
    settings_path = "config/settings.json"
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load user settings: {e}")
    
    # Return default settings
    return {
        "watsonx": {
            "api_key": os.getenv("WATSONX_API_KEY", ""),
            "project_id": os.getenv("WATSONX_PROJECT_ID", ""),
            "url": os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        },
        "github": {
            "token": os.getenv("GITHUB_TOKEN", ""),
            "repo": os.getenv("GITHUB_REPO", ""),
            "enable_pr": False
        },
        "mcp": {
            "host": os.getenv("MCP_HOST", "localhost"),
            "port": int(os.getenv("MCP_PORT", "8000"))
        },
        "advanced": {
            "target_language": "python",
            "max_file_size_mb": 10,
            "generate_tests": True
        }
    }


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def create_download_button(
    label: str,
    data: str,
    file_name: str,
    mime_type: str = "text/plain",
    key: Optional[str] = None
) -> None:
    """
    Create a download button for file content.
    
    Args:
        label: Button label
        data: File content
        file_name: Name for downloaded file
        mime_type: MIME type of file
        key: Unique key for button
    """
    st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime=mime_type,
        key=key
    )


def display_metric_card(
    title: str,
    value: Any,
    delta: Optional[str] = None,
    help_text: Optional[str] = None
) -> None:
    """
    Display a metric card with optional delta and help text.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Optional delta value
        help_text: Optional help text
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=help_text
    )


def show_success(message: str) -> None:
    """
    Display success message.
    
    Args:
        message: Success message
    """
    st.success(f"✅ {message}")


def show_error(message: str) -> None:
    """
    Display error message.
    
    Args:
        message: Error message
    """
    st.error(f"❌ {message}")


def show_warning(message: str) -> None:
    """
    Display warning message.
    
    Args:
        message: Warning message
    """
    st.warning(f"⚠️ {message}")


def show_info(message: str) -> None:
    """
    Display info message.
    
    Args:
        message: Info message
    """
    st.info(f"ℹ️ {message}")


def get_file_icon(file_extension: str) -> str:
    """
    Get icon for file type.
    
    Args:
        file_extension: File extension (e.g., '.py', '.cbl')
        
    Returns:
        Icon emoji
    """
    icons = {
        '.py': '🐍',
        '.cbl': '📜',
        '.vb': '📘',
        '.java': '☕',
        '.json': '📋',
        '.md': '📝',
        '.yaml': '⚙️',
        '.yml': '⚙️',
        '.txt': '📄'
    }
    return icons.get(file_extension.lower(), '📄')


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False
    # Basic validation - should be at least 20 characters
    return len(api_key) >= 20


def test_watsonx_connection(api_key: str, project_id: str, url: str) -> tuple[bool, str]:
    """
    Test connection to IBM watsonx.
    
    Args:
        api_key: IBM watsonx API key
        project_id: IBM watsonx project ID
        url: IBM watsonx URL
        
    Returns:
        Tuple of (success, message)
    """
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        
        credentials = Credentials(
            api_key=api_key,
            url=url
        )
        
        client = APIClient(credentials)
        client.set.default_project(project_id)
        
        return True, "Connection successful!"
    except ImportError:
        return False, "IBM watsonx AI library not installed"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def test_github_connection(token: str, repo: str) -> tuple[bool, str]:
    """
    Test connection to GitHub.
    
    Args:
        token: GitHub personal access token
        repo: Repository name (owner/repo)
        
    Returns:
        Tuple of (success, message)
    """
    try:
        import requests
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(
            f"https://api.github.com/repos/{repo}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "Connection successful!"
        elif response.status_code == 404:
            return False, "Repository not found"
        elif response.status_code == 401:
            return False, "Invalid token"
        else:
            return False, f"Connection failed: {response.status_code}"
    except ImportError:
        return False, "requests library not installed"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def test_mcp_connection(host: str, port: int) -> tuple[bool, str]:
    """
    Test connection to MCP server.
    
    Args:
        host: MCP server host
        port: MCP server port
        
    Returns:
        Tuple of (success, message)
    """
    try:
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return True, "MCP server is reachable"
        else:
            return False, "MCP server is not reachable"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def get_language_from_extension(filename: str) -> str:
    """
    Detect programming language from file extension.
    
    Args:
        filename: Name of file
        
    Returns:
        Language name (cobol, vb, java, python)
    """
    ext = Path(filename).suffix.lower()
    
    language_map = {
        '.cbl': 'cobol',
        '.cob': 'cobol',
        '.vb': 'vb',
        '.vbs': 'vb',
        '.java': 'java',
        '.py': 'python'
    }
    
    return language_map.get(ext, 'unknown')


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'workflow_results' not in st.session_state:
        st.session_state.workflow_results = None
    
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    
    if 'analysis_report' not in st.session_state:
        st.session_state.analysis_report = None
    
    if 'documentation' not in st.session_state:
        st.session_state.documentation = None
    
    if 'modernized_code' not in st.session_state:
        st.session_state.modernized_code = None
    
    if 'test_results' not in st.session_state:
        st.session_state.test_results = None
    
    if 'execution_logs' not in st.session_state:
        st.session_state.execution_logs = []


def add_log(message: str, level: str = "info"):
    """
    Add log message to session state.
    
    Args:
        message: Log message
        level: Log level (info, success, warning, error)
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "message": message,
        "level": level
    }
    
    if 'execution_logs' not in st.session_state:
        st.session_state.execution_logs = []
    
    st.session_state.execution_logs.append(log_entry)


def clear_logs():
    """Clear execution logs from session state."""
    st.session_state.execution_logs = []


def get_log_icon(level: str) -> str:
    """
    Get icon for log level.
    
    Args:
        level: Log level
        
    Returns:
        Icon emoji
    """
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    return icons.get(level, "ℹ️")

