"""
Upload & Analyze Tab Component

Handles file upload, language detection, and pipeline orchestration.
Runs all three agents sequentially with real-time progress updates.
"""

import streamlit as st
import os
import tempfile
import time
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file
load_dotenv()

from agents.analyzer import CodeAnalyzer
from agents.documentation import DocumentationAgent
from agents.refactoring import RefactoringAgent
from ui.utils import (
    show_success, show_error, show_warning, show_info,
    add_log, clear_logs, get_log_icon, get_language_from_extension,
    format_file_size, format_duration, load_config, load_user_settings
)


def render_upload_tab():
    """Render the Upload & Analyze tab."""
    
    st.header("📤 Upload & Analyze Legacy Code")
    st.markdown("Upload your legacy code file and let our AI agents modernize it for you.")
    
    # File upload section
    st.subheader("📁 Upload Legacy Code File")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['cbl', 'cob', 'vb', 'vbs', 'java'],
        help="Supported formats: COBOL (.cbl, .cob), Visual Basic (.vb, .vbs), Java (.java)"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("File Name", uploaded_file.name)
        
        with col2:
            file_size = len(uploaded_file.getvalue())
            st.metric("File Size", format_file_size(file_size))
        
        with col3:
            detected_lang = get_language_from_extension(uploaded_file.name)
            st.metric("Detected Language", detected_lang.upper())
        
        # Store in session state
        st.session_state.uploaded_file = uploaded_file
        
        st.divider()
        
        # Configuration section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Target Language")
            target_language = st.radio(
                "Select target language",
                options=["Python 3.11+", "Java 17+"],
                index=0,
                help="The modern language to convert your legacy code to"
            )
        
        with col2:
            st.subheader("⚙️ Options")
            generate_tests = False
            
            create_pr = st.checkbox(
                "Create GitHub PR",
                value=False,
                help="Automatically create a Pull Request (requires GitHub configuration)"
            )
        
        st.divider()
        
        # Modernize button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            modernize_button = st.button(
                "🚀 Modernize Code",
                type="primary",
                use_container_width=True,
                help="Start the modernization pipeline"
            )
        
        if modernize_button:
            run_modernization_pipeline(
                uploaded_file,
                detected_lang,
                target_language.split()[0].lower(),
                generate_tests,
                create_pr
            )
    
    else:
        st.info("👆 Please upload a legacy code file to get started")
    
    # Execution log section
    st.divider()
    st.subheader("📋 Execution Log")
    
    log_container = st.container()
    
    with log_container:
        if 'execution_logs' in st.session_state and st.session_state.execution_logs:
            # Display logs in a styled container
            log_text = ""
            for log in st.session_state.execution_logs:
                icon = get_log_icon(log['level'])
                log_text += f"{icon} [{log['timestamp']}] {log['message']}\n"
            
            st.text_area(
                "Logs",
                value=log_text,
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )
            
            # Clear logs button
            if st.button("🗑️ Clear Logs"):
                clear_logs()
                st.rerun()
        else:
            st.info("No logs yet. Start the modernization process to see logs here.")


def run_modernization_pipeline(
    uploaded_file,
    source_language: str,
    target_language: str,
    generate_tests: bool,
    create_pr: bool
):
    """
    Run the complete modernization pipeline.
    
    Args:
        uploaded_file: Uploaded file object
        source_language: Source language (cobol, vb, java)
        target_language: Target language (python, java)
        generate_tests: Whether to generate unit tests
        create_pr: Whether to create GitHub PR
    """
    
    # Clear previous logs
    clear_logs()
    
    # Load configurations
    agent_config = load_config("config/agent_configs.yaml")
    user_settings = load_user_settings()
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Save uploaded file to temp directory
        add_log("Starting modernization workflow...", "info")
        status_text.text("Preparing files...")
        progress_bar.progress(5)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file
            input_path = os.path.join(temp_dir, uploaded_file.name)
            with open(input_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            add_log(f"Saved file to: {input_path}", "info")
            
            # Create output directories
            output_dir = "output"
            analysis_dir = os.path.join(output_dir, "analysis")
            docs_dir = os.path.join(output_dir, "documentation")
            modernized_dir = os.path.join(output_dir, "modernized")
            
            for dir_path in [analysis_dir, docs_dir]:
                os.makedirs(dir_path, exist_ok=True)
            
            # Always clear the modernized dir to avoid showing stale files
            import shutil
            if os.path.exists(modernized_dir):
                shutil.rmtree(modernized_dir)
            os.makedirs(modernized_dir)
            
            # ===== AGENT 1: CODE ANALYZER =====
            add_log("Agent 1: Starting code analysis...", "info")
            status_text.text("🔍 Agent 1: Analyzing code structure...")
            progress_bar.progress(10)
            
            start_time = time.time()
            
            try:
                analyzer = CodeAnalyzer(agent_config.get('analyzer', {}))
                analysis_result = analyzer.analyze(
                    code_path=input_path,
                    language=source_language,
                    output_dir=analysis_dir
                )
                
                duration = time.time() - start_time
                add_log(f"Agent 1: Analysis complete in {format_duration(duration)} ✓", "success")
                
                # Store in session state
                st.session_state.analysis_report = analysis_result
                
                progress_bar.progress(35)
                
            except Exception as e:
                add_log(f"Agent 1: Analysis failed - {str(e)}", "error")
                show_error(f"Analysis failed: {str(e)}")
                return
            
            # ===== AGENT 2: DOCUMENTATION =====
            add_log("Agent 2: Generating documentation...", "info")
            status_text.text("📝 Agent 2: Creating documentation...")
            progress_bar.progress(40)
            
            start_time = time.time()
            
            try:
                doc_agent = DocumentationAgent(agent_config.get('documentation', {}))
                
                # Load analysis report
                analysis_report_path = os.path.join(analysis_dir, "analysis_report.json")
                
                doc_result = doc_agent.generate_documentation(
                    analysis_report_path=analysis_report_path
                )
                
                duration = time.time() - start_time
                add_log(f"Agent 2: Documentation complete in {format_duration(duration)} ✓", "success")
                
                # Store in session state
                st.session_state.documentation = doc_result
                
                progress_bar.progress(65)
                
            except Exception as e:
                add_log(f"Agent 2: Documentation failed - {str(e)}", "error")
                show_error(f"Documentation generation failed: {str(e)}")
                return
            
            # ===== AGENT 3: REFACTORING =====
            add_log("Agent 3: Modernizing code...", "info")
            status_text.text("🔧 Agent 3: Refactoring to modern code...")
            progress_bar.progress(70)
            
            start_time = time.time()
            
            try:
                refactor_agent = RefactoringAgent(agent_config.get('refactoring', {}))
                
                # Load documentation
                inline_comments_path = os.path.join(docs_dir, "inline_comments.json")
                
                refactor_result = refactor_agent.modernize_code(
                    legacy_dir=os.path.dirname(input_path),
                    analysis_path=analysis_report_path,
                    comments_path=inline_comments_path,
                    output_dir=modernized_dir,
                    target_language=target_language
                )
                
                duration = time.time() - start_time
                add_log(f"Agent 3: Code modernized in {format_duration(duration)} ✓", "success")
                
                # Store in session state
                st.session_state.modernized_code = refactor_result
                
                progress_bar.progress(90)
                
            except Exception as e:
                add_log(f"Agent 3: Refactoring failed - {str(e)}", "error")
                show_error(f"Code modernization failed: {str(e)}")
                return
            
            # ===== RUN TESTS =====
            if generate_tests:
                add_log("Running generated tests...", "info")
                status_text.text("🧪 Running unit tests...")
                progress_bar.progress(92)
                
                try:
                    # Run pytest on generated tests
                    import subprocess
                    
                    test_files = refactor_result.get('tests', [])
                    test_file = test_files[0] if test_files else None
                    if test_file and os.path.exists(test_file):
                        result = subprocess.run(
                            ['python', '-m', 'pytest', test_file, '-v', '--tb=short'],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        
                        if result.returncode == 0:
                            add_log("Tests passed: All tests successful ✓", "success")
                            st.session_state.test_results = {
                                'status': 'passed',
                                'output': result.stdout
                            }
                        else:
                            add_log("Tests failed: Some tests did not pass", "warning")
                            st.session_state.test_results = {
                                'status': 'failed',
                                'output': result.stdout + "\n" + result.stderr
                            }
                    else:
                        add_log("No test file generated", "warning")
                        
                except Exception as e:
                    add_log(f"Test execution failed: {str(e)}", "warning")
            
            progress_bar.progress(95)
            
            # ===== CREATE GITHUB PR (OPTIONAL) =====
            if create_pr:
                add_log("Creating GitHub Pull Request...", "info")
                status_text.text("📤 Creating GitHub PR...")
                
                try:
                    from utils.github_integration import create_github_pr_from_workflow
                    
                    # Check if GitHub is configured
                    github_token = os.getenv('GITHUB_TOKEN')
                    github_repo = os.getenv('GITHUB_REPO')
                    
                    if not github_token or not github_repo:
                        add_log("GitHub not configured. Set GITHUB_TOKEN and GITHUB_REPO in .env file", "warning")
                        show_warning("⚠️ GitHub not configured. PR creation skipped.")
                    else:
                        # Create PR
                        pr_result = create_github_pr_from_workflow(
                            source_file=uploaded_file.name,
                            output_dir=output_dir
                        )
                        
                        if pr_result.get('success'):
                            pr_url = pr_result.get('pr_url')
                            pr_number = pr_result.get('pr_number')
                            add_log(f"✓ Pull Request created: #{pr_number}", "success")
                            add_log(f"PR URL: {pr_url}", "info")
                            
                            # Store PR info in session state
                            st.session_state.pr_info = {
                                'url': pr_url,
                                'number': pr_number,
                                'branch': pr_result.get('branch')
                            }
                            
                            show_success(f"✅ Pull Request #{pr_number} created successfully!")
                        else:
                            error_msg = pr_result.get('error', 'Unknown error')
                            add_log(f"PR creation failed: {error_msg}", "error")
                            show_error(f"Failed to create PR: {error_msg}")
                            
                except ImportError as e:
                    add_log(f"GitHub integration module not available: {str(e)}", "warning")
                    show_warning("GitHub integration not available. Install required packages.")
                except Exception as e:
                    add_log(f"PR creation failed: {str(e)}", "error")
                    show_error(f"Failed to create PR: {str(e)}")
            
            # ===== COMPLETE =====
            progress_bar.progress(100)
            status_text.text("✅ Workflow complete!")
            
            add_log("Workflow complete! ✓", "success")
            add_log(f"Results saved to: {output_dir}", "info")
            
            # Store workflow completion
            st.session_state.workflow_results = {
                'completed': True,
                'timestamp': datetime.now().isoformat(),
                'source_file': uploaded_file.name,
                'source_language': source_language,
                'target_language': target_language
            }
            
            show_success("Modernization complete! Check the Results tab to view outputs.")
            
            # Auto-switch to results tab hint
            st.info("💡 Switch to the **Results** tab to view analysis, documentation, and modernized code.")
            
    except Exception as e:
        add_log(f"Pipeline failed: {str(e)}", "error")
        show_error(f"Pipeline execution failed: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Workflow failed")

