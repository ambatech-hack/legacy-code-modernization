"""
Settings Tab Component

Handles configuration management for:
- IBM watsonx API settings
- GitHub integration
- MCP server connection
- Advanced options
"""

import streamlit as st
import os
from pathlib import Path
from typing import Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.utils import (
    load_user_settings, save_config, show_success, show_error, show_info,
    validate_api_key, test_watsonx_connection, test_github_connection,
    test_mcp_connection
)


def render_settings_tab():
    """Render the Settings tab."""
    
    st.header("⚙️ Settings & Configuration")
    st.markdown("Configure API keys, integrations, and preferences for the modernization pipeline.")
    
    # Load current settings
    settings = load_user_settings()
    
    # Create sections
    st.subheader("🔐 IBM watsonx Configuration")
    render_watsonx_settings(settings)
    
    st.divider()
    
    st.subheader("🐙 GitHub Integration")
    render_github_settings(settings)
    
    st.divider()
    
    st.subheader("🔌 MCP Server Settings")
    render_mcp_settings(settings)
    
    st.divider()
    
    st.subheader("🎛️ Advanced Options")
    render_advanced_settings(settings)
    
    st.divider()
    
    # Save button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Save Configuration", type="primary", use_container_width=True):
            save_settings(settings)


def render_watsonx_settings(settings: Dict[str, Any]):
    """Render IBM watsonx configuration section."""
    
    watsonx_config = settings.get('watsonx', {})
    
    st.markdown("""
    Configure your IBM watsonx credentials. You can obtain these from your 
    [IBM Cloud account](https://cloud.ibm.com/).
    """)
    
    # API Key
    api_key = st.text_input(
        "API Key",
        value=watsonx_config.get('api_key', ''),
        type="password",
        help="Your IBM watsonx API key",
        key="watsonx_api_key"
    )
    
    # Project ID
    project_id = st.text_input(
        "Project ID",
        value=watsonx_config.get('project_id', ''),
        help="Your IBM watsonx project ID",
        key="watsonx_project_id"
    )
    
    # URL
    url = st.text_input(
        "watsonx URL",
        value=watsonx_config.get('url', 'https://us-south.ml.cloud.ibm.com'),
        help="IBM watsonx API endpoint URL",
        key="watsonx_url"
    )
    
    # Update settings
    settings['watsonx'] = {
        'api_key': api_key,
        'project_id': project_id,
        'url': url
    }
    
    # Test connection button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔍 Test Connection", key="test_watsonx"):
            if not api_key or not project_id:
                show_error("Please provide API key and Project ID")
            else:
                with st.spinner("Testing connection..."):
                    success, message = test_watsonx_connection(api_key, project_id, url)
                    if success:
                        show_success(message)
                    else:
                        show_error(message)
    
    with col2:
        if not api_key:
            st.warning("⚠️ API key not configured. AI features will be limited.")


def render_github_settings(settings: Dict[str, Any]):
    """Render GitHub integration settings."""
    
    github_config = settings.get('github', {})
    
    st.markdown("""
    Configure GitHub integration to automatically create Pull Requests with modernized code.
    Generate a [Personal Access Token](https://github.com/settings/tokens) with `repo` scope.
    """)
    
    # Enable GitHub integration
    enable_github = st.checkbox(
        "Enable GitHub Integration",
        value=github_config.get('enable_pr', False),
        help="Enable automatic PR creation",
        key="github_enable"
    )
    
    if enable_github:
        # GitHub Token
        token = st.text_input(
            "Personal Access Token",
            value=github_config.get('token', ''),
            type="password",
            help="GitHub personal access token with repo scope",
            key="github_token"
        )
        
        # Repository
        repo = st.text_input(
            "Repository",
            value=github_config.get('repo', ''),
            placeholder="owner/repository",
            help="Target repository in format: owner/repository",
            key="github_repo"
        )
        
        # Update settings
        settings['github'] = {
            'token': token,
            'repo': repo,
            'enable_pr': enable_github
        }
        
        # Test connection button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔍 Test Connection", key="test_github"):
                if not token or not repo:
                    show_error("Please provide token and repository")
                else:
                    with st.spinner("Testing connection..."):
                        success, message = test_github_connection(token, repo)
                        if success:
                            show_success(message)
                        else:
                            show_error(message)
        
        with col2:
            if not token or not repo:
                st.warning("⚠️ GitHub not fully configured")
    else:
        settings['github'] = {
            'token': '',
            'repo': '',
            'enable_pr': False
        }
        st.info("GitHub integration is disabled. Enable it to create automatic PRs.")


def render_mcp_settings(settings: Dict[str, Any]):
    """Render MCP server settings."""
    
    mcp_config = settings.get('mcp', {})
    
    st.markdown("""
    Configure connection to the Model Context Protocol (MCP) server for advanced code analysis tools.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Host
        host = st.text_input(
            "MCP Server Host",
            value=mcp_config.get('host', 'localhost'),
            help="MCP server hostname or IP address",
            key="mcp_host"
        )
    
    with col2:
        # Port
        port = st.number_input(
            "MCP Server Port",
            value=mcp_config.get('port', 8000),
            min_value=1,
            max_value=65535,
            help="MCP server port number",
            key="mcp_port"
        )
    
    # Update settings
    settings['mcp'] = {
        'host': host,
        'port': port
    }
    
    # Test connection button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔍 Test Connection", key="test_mcp"):
            with st.spinner("Testing connection..."):
                success, message = test_mcp_connection(host, port)
                if success:
                    show_success(message)
                else:
                    show_error(message)
    
    with col2:
        st.info("💡 Start MCP server with: `python scripts/start_mcp_server.py`")


def render_advanced_settings(settings: Dict[str, Any]):
    """Render advanced configuration options."""
    
    advanced_config = settings.get('advanced', {})
    
    st.markdown("Configure advanced options for the modernization pipeline.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Target language preference
        target_language = st.selectbox(
            "Default Target Language",
            options=["python", "java"],
            index=0 if advanced_config.get('target_language', 'python') == 'python' else 1,
            help="Default target language for modernization",
            key="advanced_target_lang"
        )
        
        # Generate tests by default
        generate_tests = st.checkbox(
            "Generate Tests by Default",
            value=advanced_config.get('generate_tests', True),
            help="Automatically generate unit tests",
            key="advanced_gen_tests"
        )
    
    with col2:
        # Max file size
        max_file_size = st.number_input(
            "Max File Size (MB)",
            value=advanced_config.get('max_file_size_mb', 10),
            min_value=1,
            max_value=100,
            help="Maximum file size for upload",
            key="advanced_max_size"
        )
        
        # Timeout
        timeout = st.number_input(
            "Agent Timeout (seconds)",
            value=advanced_config.get('timeout', 300),
            min_value=60,
            max_value=3600,
            help="Maximum time for each agent to complete",
            key="advanced_timeout"
        )
    
    # Update settings
    settings['advanced'] = {
        'target_language': target_language,
        'generate_tests': generate_tests,
        'max_file_size_mb': max_file_size,
        'timeout': timeout
    }
    
    # Additional options
    st.markdown("#### 🔧 Additional Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        verbose_logging = st.checkbox(
            "Verbose Logging",
            value=advanced_config.get('verbose_logging', False),
            help="Enable detailed logging output",
            key="advanced_verbose"
        )
    
    with col2:
        save_intermediate = st.checkbox(
            "Save Intermediate Results",
            value=advanced_config.get('save_intermediate', True),
            help="Save intermediate outputs from each agent",
            key="advanced_intermediate"
        )
    
    settings['advanced']['verbose_logging'] = verbose_logging
    settings['advanced']['save_intermediate'] = save_intermediate


def save_settings(settings: Dict[str, Any]):
    """Save settings to configuration file."""
    
    try:
        # Save to config file
        success = save_config(settings, "config/settings.json")
        
        if success:
            show_success("Configuration saved successfully!")
            
            # Also update environment variables for current session
            if settings.get('watsonx', {}).get('api_key'):
                os.environ['WATSONX_API_KEY'] = settings['watsonx']['api_key']
            if settings.get('watsonx', {}).get('project_id'):
                os.environ['WATSONX_PROJECT_ID'] = settings['watsonx']['project_id']
            if settings.get('watsonx', {}).get('url'):
                os.environ['WATSONX_URL'] = settings['watsonx']['url']
            
            if settings.get('github', {}).get('token'):
                os.environ['GITHUB_TOKEN'] = settings['github']['token']
            if settings.get('github', {}).get('repo'):
                os.environ['GITHUB_REPO'] = settings['github']['repo']
            
            if settings.get('mcp', {}).get('host'):
                os.environ['MCP_HOST'] = settings['mcp']['host']
            if settings.get('mcp', {}).get('port'):
                os.environ['MCP_PORT'] = str(settings['mcp']['port'])
            
            show_info("💡 Settings will take effect on next pipeline run")
        else:
            show_error("Failed to save configuration")
    
    except Exception as e:
        show_error(f"Error saving configuration: {str(e)}")


def render_help_section():
    """Render help and documentation section."""
    
    with st.expander("📚 Help & Documentation"):
        st.markdown("""
        ### Getting Started
        
        1. **Configure IBM watsonx**: Enter your API key and project ID
        2. **Upload Code**: Go to Upload & Analyze tab and upload your legacy code
        3. **Modernize**: Click the Modernize button to start the pipeline
        4. **View Results**: Check the Results tab for analysis, documentation, and modernized code
        
        ### API Keys
        
        - **IBM watsonx**: Get your API key from [IBM Cloud](https://cloud.ibm.com/)
        - **GitHub**: Generate a token from [GitHub Settings](https://github.com/settings/tokens)
        
        ### Support
        
        For issues or questions, please refer to the [documentation](README.md) or contact support.
        """)

