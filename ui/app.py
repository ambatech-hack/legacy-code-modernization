"""
Main Streamlit application for Legacy Code Modernization Squad.

Provides three-tab interface:
1. Upload & Analyze - Upload legacy code and run modernization pipeline
2. Results - View analysis, documentation, and modernized code
3. Settings - Configure API keys and preferences
"""

import streamlit as st
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.components.upload_tab import render_upload_tab
from ui.components.results_tab import render_results_tab
from ui.components.settings_tab import render_settings_tab
from ui.utils import initialize_session_state


def main():
    """Main application entry point."""
    
    # Configure page
    st.set_page_config(
        page_title="Legacy Code Modernization Squad",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🔄 Legacy Code Modernization Squad")
    st.markdown("""
    **Powered by IBM watsonx and Granite AI**
    
    Transform your legacy code (COBOL, VB, Java) into modern, maintainable Python with AI-powered analysis, 
    documentation, and refactoring.
    """)
    
    st.divider()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📤 Upload & Analyze",
        "📊 Results",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_upload_tab()
    
    with tab2:
        render_results_tab()
    
    with tab3:
        render_settings_tab()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <p>Legacy Code Modernization Squad | Built with ❤️</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

