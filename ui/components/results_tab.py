"""
Results Tab Component

Displays analysis results, documentation, code diff, tests, and dependency graphs.
Provides download buttons for all generated outputs.
"""

import streamlit as st
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.utils import (
    show_info, create_download_button, display_metric_card,
    format_file_size, get_file_icon
)


def render_results_tab():
    """Render the Results tab with sub-tabs for different outputs."""
    
    st.header("📊 Modernization Results")
    
    # Check if workflow has been completed
    if not st.session_state.get('workflow_results'):
        st.info("👈 No results yet. Upload a file in the **Upload & Analyze** tab to get started.")
        return
    
    # Display workflow summary
    workflow_info = st.session_state.workflow_results
    
    st.success(f"✅ Modernization completed at {workflow_info.get('timestamp', 'N/A')}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Source File", workflow_info.get('source_file', 'N/A'))
    with col2:
        st.metric("Source Language", workflow_info.get('source_language', 'N/A').upper())
    with col3:
        st.metric("Target Language", workflow_info.get('target_language', 'N/A').upper())
    
    st.divider()
    
    # Create sub-tabs for different result types
    result_tabs = st.tabs([
        "📈 Analysis",
        "📝 Documentation",
        "🔄 Code Diff",
        "🧪 Tests",
        "🕸️ Dependency Graph"
    ])
    
    with result_tabs[0]:
        render_analysis_results()
    
    with result_tabs[1]:
        render_documentation_results()
    
    with result_tabs[2]:
        render_code_diff()
    
    with result_tabs[3]:
        render_test_results()
    
    with result_tabs[4]:
        render_dependency_graph()


def render_analysis_results():
    """Render code analysis results."""
    
    st.subheader("📈 Code Analysis Report")
    
    # Load analysis report
    analysis_report_path = "output/analysis/analysis_report.json"
    
    if not os.path.exists(analysis_report_path):
        st.warning("Analysis report not found.")
        return
    
    try:
        with open(analysis_report_path, 'r') as f:
            analysis = json.load(f)
        
        # Display metrics
        st.markdown("### 📊 Code Metrics")
        
        metrics = analysis.get('metrics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            display_metric_card(
                "Total Lines",
                metrics.get('total_lines', 0),
                help_text="Total lines of code"
            )
        
        with col2:
            display_metric_card(
                "Functions",
                metrics.get('total_functions', 0),
                help_text="Number of functions/procedures"
            )
        
        with col3:
            display_metric_card(
                "Complexity",
                metrics.get('avg_complexity', 0),
                help_text="Average cyclomatic complexity"
            )
        
        with col4:
            display_metric_card(
                "Dependencies",
                len(analysis.get('dependencies', [])),
                help_text="Number of external dependencies"
            )
        
        st.divider()
        
        # Display functions
        st.markdown("### 🔧 Functions Detected")
        
        functions = analysis.get('functions', [])
        
        if functions:
            for func in functions:
                with st.expander(f"📌 {func.get('name', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Line:** {func.get('line_number', 'N/A')}")
                        st.write(f"**Complexity:** {func.get('complexity', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Parameters:** {len(func.get('parameters', []))}")
                        st.write(f"**Returns:** {func.get('return_type', 'N/A')}")
                    
                    if func.get('docstring'):
                        st.markdown("**Description:**")
                        st.info(func['docstring'])
        else:
            st.info("No functions detected in the code.")
        
        st.divider()
        
        # Display dependencies
        st.markdown("### 📦 Dependencies")
        
        dependencies = analysis.get('dependencies', [])
        
        if dependencies:
            for dep in dependencies:
                st.write(f"- {dep}")
        else:
            st.info("No external dependencies detected.")
        
        st.divider()
        
        # Display technical debt
        st.markdown("### ⚠️ Technical Debt")
        
        tech_debt = analysis.get('technical_debt', [])
        
        if tech_debt:
            for issue in tech_debt:
                severity = issue.get('severity', 'info')
                icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
                
                st.write(f"{icon} **{issue.get('type', 'Issue')}** (Line {issue.get('line', 'N/A')})")
                st.write(f"   {issue.get('description', 'No description')}")
        else:
            st.success("No technical debt issues detected!")
        
        # Download button
        st.divider()
        with open(analysis_report_path, 'r') as f:
            analysis_json = f.read()
        
        create_download_button(
            label="📥 Download Analysis Report (JSON)",
            data=analysis_json,
            file_name="analysis_report.json",
            mime_type="application/json",
            key="download_analysis"
        )
        
    except Exception as e:
        st.error(f"Failed to load analysis report: {str(e)}")


def render_documentation_results():
    """Render generated documentation."""
    
    st.subheader("📝 Generated Documentation")
    
    docs_dir = "output/documentation"
    
    if not os.path.exists(docs_dir):
        st.warning("Documentation not found.")
        return
    
    # List available documentation files
    doc_files = {
        "README.md": "📘 Project README",
        "ARCHITECTURE.md": "🏗️ Architecture Documentation",
        "DEPENDENCIES.md": "📦 Dependencies Documentation",
        "TECHNICAL_DEBT.md": "⚠️ Technical Debt Report"
    }
    
    # Create tabs for each document
    doc_tabs = st.tabs(list(doc_files.values()))
    
    for idx, (filename, title) in enumerate(doc_files.items()):
        with doc_tabs[idx]:
            file_path = os.path.join(docs_dir, filename)
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Display markdown content
                    st.markdown(content)
                    
                    st.divider()
                    
                    # Download button
                    create_download_button(
                        label=f"📥 Download {filename}",
                        data=content,
                        file_name=filename,
                        mime_type="text/markdown",
                        key=f"download_{filename}"
                    )
                    
                except Exception as e:
                    st.error(f"Failed to load {filename}: {str(e)}")
            else:
                st.info(f"{filename} not generated.")


def render_code_diff():
    """Render side-by-side code comparison."""
    
    st.subheader("🔄 Code Comparison")
    
    # Get original and modernized code
    original_file = st.session_state.get('uploaded_file')
    modernized_dir = "output/modernized"
    
    if not original_file:
        st.warning("Original file not found.")
        return
    
    # Find modernized file — prefer the one that matches session state
    modernized_files = []
    if os.path.exists(modernized_dir):
        for file in sorted(os.listdir(modernized_dir), key=lambda f: os.path.getmtime(os.path.join(modernized_dir, f)), reverse=True):
            if (file.endswith('.py') or file.endswith('.java')) and not file.startswith('test_'):
                modernized_files.append(file)
    
    # Try to match by uploaded file stem first
    original_stem = Path(original_file.name).stem
    matched = [f for f in modernized_files if Path(f).stem == original_stem]
    if matched:
        modernized_files = matched  # use only the matching file
    
    if not modernized_files:
        st.warning("Modernized code not found.")
        return
    
    modernized_file = os.path.join(modernized_dir, modernized_files[0])
    
    try:
        # Read original code
        original_code = original_file.getvalue().decode('utf-8')
        
        # Read modernized code
        with open(modernized_file, 'r', encoding='utf-8') as f:
            modernized_code = f.read()
        
        # Display side-by-side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📜 Original Code")
            st.code(original_code, language=get_language_from_extension(original_file.name))
        
        with col2:
            st.markdown("### ✨ Modernized Code")
            output_lang = 'java' if modernized_files[0].endswith('.java') else 'python'
            st.code(modernized_code, language=output_lang)
        
        st.divider()
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            original_lines = len(original_code.split('\n'))
            st.metric("Original Lines", original_lines)
        
        with col2:
            modernized_lines = len(modernized_code.split('\n'))
            st.metric("Modernized Lines", modernized_lines)
        
        with col3:
            reduction = ((original_lines - modernized_lines) / original_lines * 100) if original_lines > 0 else 0
            st.metric("Line Reduction", f"{reduction:.1f}%")
        
        st.divider()
        
        # Download modernized code
        create_download_button(
            label="📥 Download Modernized Code",
            data=modernized_code,
            file_name=modernized_files[0],
            mime_type="text/plain",
            key="download_modernized"
        )
        
    except Exception as e:
        st.error(f"Failed to load code files: {str(e)}")


def get_language_from_extension(filename: str) -> str:
    """Get language name for syntax highlighting."""
    ext = Path(filename).suffix.lower()
    
    lang_map = {
        '.cbl': 'cobol',
        '.cob': 'cobol',
        '.vb': 'vbnet',
        '.vbs': 'vbscript',
        '.java': 'java',
        '.py': 'python'
    }
    
    return lang_map.get(ext, 'text')


def render_test_results():
    """Render unit test results."""
    
    st.subheader("🧪 Unit Test Results")
    
    test_results = st.session_state.get('test_results')
    
    if not test_results:
        st.info("No test results available. Enable 'Generate unit tests' option when modernizing code.")
        return
    
    # Display test status
    status = test_results.get('status', 'unknown')
    
    if status == 'passed':
        st.success("✅ All tests passed!")
    elif status == 'failed':
        st.error("❌ Some tests failed")
    else:
        st.warning("⚠️ Test status unknown")
    
    # Display test output
    st.markdown("### 📋 Test Output")
    
    output = test_results.get('output', 'No output available')
    st.code(output, language='text')
    
    st.divider()
    
    # Show test file if available
    modernized_dir = "output/modernized"
    test_files = []
    
    if os.path.exists(modernized_dir):
        for file in os.listdir(modernized_dir):
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(file)
    
    if test_files:
        st.markdown("### 📝 Generated Test Code")
        
        test_file_path = os.path.join(modernized_dir, test_files[0])
        
        try:
            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_code = f.read()
            
            st.code(test_code, language='python')
            
            st.divider()
            
            # Download test file
            create_download_button(
                label="📥 Download Test File",
                data=test_code,
                file_name=test_files[0],
                mime_type="text/plain",
                key="download_tests"
            )
            
        except Exception as e:
            st.error(f"Failed to load test file: {str(e)}")


def render_dependency_graph():
    """Render dependency graph visualization."""
    
    st.subheader("🕸️ Dependency Graph")
    
    # Load analysis report for dependencies
    analysis_report_path = "output/analysis/analysis_report.json"
    
    if not os.path.exists(analysis_report_path):
        st.warning("Analysis report not found.")
        return
    
    try:
        with open(analysis_report_path, 'r') as f:
            analysis = json.load(f)
        
        dependencies = analysis.get('dependencies', [])
        functions = analysis.get('functions', [])
        
        if not dependencies and not functions:
            st.info("No dependencies or functions to visualize.")
            return
        
        # Create a simple text-based dependency visualization
        st.markdown("### 📦 External Dependencies")
        
        if dependencies:
            for dep in dependencies:
                st.write(f"- 📦 {dep}")
        else:
            st.info("No external dependencies detected.")
        
        st.divider()
        
        # Function call graph (simplified)
        st.markdown("### 🔗 Function Structure")
        
        if functions:
            st.write(f"Total Functions: {len(functions)}")
            
            # Group by complexity
            high_complexity = [f for f in functions if f.get('complexity', 0) > 10]
            medium_complexity = [f for f in functions if 5 < f.get('complexity', 0) <= 10]
            low_complexity = [f for f in functions if f.get('complexity', 0) <= 5]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Low Complexity", len(low_complexity), help="Complexity ≤ 5")
            
            with col2:
                st.metric("Medium Complexity", len(medium_complexity), help="5 < Complexity ≤ 10")
            
            with col3:
                st.metric("High Complexity", len(high_complexity), help="Complexity > 10")
            
            # List high complexity functions
            if high_complexity:
                st.warning("⚠️ High Complexity Functions (may need refactoring):")
                for func in high_complexity:
                    st.write(f"- {func.get('name', 'Unknown')} (Complexity: {func.get('complexity', 'N/A')})")
        else:
            st.info("No functions detected.")
        
        # Note about advanced visualization
        st.divider()
        st.info("💡 **Note:** For interactive dependency graphs with plotly or pyvis, install additional packages: `pip install plotly pyvis`")
        
    except Exception as e:
        st.error(f"Failed to load dependency data: {str(e)}")

