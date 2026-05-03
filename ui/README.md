# Streamlit UI Documentation

## Overview

The Streamlit UI provides a user-friendly web interface for the Legacy Code Modernization Squad. It allows users to upload legacy code, configure settings, run the modernization pipeline, and view results.

## Architecture

```
ui/
├── app.py                      # Main Streamlit application
├── components/                 # UI components
│   ├── __init__.py
│   ├── upload_tab.py          # Upload & Analyze tab
│   ├── results_tab.py         # Results display tab
│   └── settings_tab.py        # Settings configuration tab
├── utils.py                    # Utility functions
└── README.md                   # This file
```

## Features

### 1. Upload & Analyze Tab (📤)

**Purpose**: Upload legacy code and run the modernization pipeline

**Features**:
- File upload widget (supports COBOL, VB, Java)
- Automatic language detection
- Target language selection (Python, Java)
- Configuration options:
  - Generate unit tests
  - Create GitHub PR
- Real-time progress tracking
- Live execution logs
- Pipeline orchestration (runs all 3 agents sequentially)

**Workflow**:
1. Upload legacy code file
2. Configure modernization options
3. Click "Modernize Code" button
4. Watch real-time progress and logs
5. Get completion notification

### 2. Results Tab (📊)

**Purpose**: View and download all generated outputs

**Sub-tabs**:

#### 📈 Analysis
- Code metrics (lines, functions, complexity)
- Function details with parameters and complexity
- External dependencies list
- Technical debt issues with severity levels
- Download analysis report (JSON)

#### 📝 Documentation
- Project README.md
- Architecture documentation
- Dependencies documentation
- Technical debt report
- Download individual documents

#### 🔄 Code Diff
- Side-by-side comparison of original vs modernized code
- Syntax highlighting for both languages
- Line count statistics and reduction percentage
- Download modernized code

#### 🧪 Tests
- Unit test execution results
- Test output and logs
- Generated test code display
- Download test files

#### 🕸️ Dependency Graph
- External dependencies visualization
- Function complexity breakdown
- High complexity function warnings
- Interactive graphs (with additional packages)

### 3. Settings Tab (⚙️)

**Purpose**: Configure API keys, integrations, and preferences

**Sections**:

#### 🔐 IBM watsonx Configuration
- API key (secure input)
- Project ID
- watsonx URL endpoint
- Connection testing

#### 🐙 GitHub Integration
- Enable/disable GitHub integration
- Personal access token
- Target repository configuration
- Connection testing

#### 🔌 MCP Server Settings
- Server host and port configuration
- Connection testing
- Server startup instructions

#### 🎛️ Advanced Options
- Default target language
- Generate tests by default
- Maximum file size limits
- Agent timeout settings
- Verbose logging
- Save intermediate results

## Usage

### Starting the UI

```bash
# Method 1: Using the startup script
python scripts/run_ui.py

# Method 2: Direct streamlit command
streamlit run ui/app.py

# Method 3: From ui directory
cd ui
streamlit run app.py
```

The UI will be available at: http://localhost:8501

### Configuration

1. **First Time Setup**:
   - Go to Settings tab
   - Configure IBM watsonx API credentials
   - Optionally configure GitHub integration
   - Save configuration

2. **Upload and Modernize**:
   - Go to Upload & Analyze tab
   - Upload a legacy code file
   - Configure options
   - Click "Modernize Code"

3. **View Results**:
   - Go to Results tab
   - Explore analysis, documentation, and code diff
   - Download generated files

### Supported File Types

- **COBOL**: `.cbl`, `.cob`
- **Visual Basic**: `.vb`, `.vbs`
- **Java**: `.java`

### Output Files

The UI generates and displays:

- `output/analysis/analysis_report.json` - Code analysis results
- `output/documentation/*.md` - Generated documentation
- `output/modernized/*.py` - Modernized Python code
- `output/modernized/test_*.py` - Generated unit tests

## Session State Management

The UI uses Streamlit's session state to maintain data across tabs:

- `workflow_results` - Pipeline execution results
- `uploaded_file` - Currently uploaded file
- `analysis_report` - Analysis results
- `documentation` - Generated documentation
- `modernized_code` - Refactored code
- `test_results` - Unit test results
- `execution_logs` - Pipeline execution logs

## Error Handling

The UI includes comprehensive error handling:

- **File Upload**: Validates file types and sizes
- **API Connections**: Tests and validates API credentials
- **Pipeline Execution**: Catches and displays agent errors
- **Configuration**: Validates settings before saving

## Customization

### Adding New File Types

1. Update `get_language_from_extension()` in `ui/utils.py`
2. Add file type to upload widget in `upload_tab.py`
3. Ensure agents support the new language

### Adding New Visualizations

1. Install additional packages (plotly, pyvis, etc.)
2. Add visualization functions to `results_tab.py`
3. Update dependency graph section

### Styling

The UI uses Streamlit's default styling with custom markdown for enhanced appearance. To customize:

1. Add CSS in `st.markdown()` with `unsafe_allow_html=True`
2. Use Streamlit's theming system
3. Customize colors and fonts in `.streamlit/config.toml`

## Dependencies

Required packages (see `requirements.txt`):

```
streamlit>=1.28.0
pyyaml>=6.0
loguru>=0.7.0
requests>=2.31.0
```

Optional packages for enhanced features:

```
plotly>=5.17.0          # Interactive charts
pyvis>=0.3.2            # Network graphs
streamlit-ace>=0.1.1    # Code editor
streamlit-aggrid>=0.3.4 # Data tables
```

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure all dependencies are installed
   - Check Python path configuration
   - Verify agent modules are accessible

2. **API Connection Failures**:
   - Verify API keys and credentials
   - Check network connectivity
   - Test connections in Settings tab

3. **File Upload Issues**:
   - Check file size limits
   - Verify file type is supported
   - Ensure proper file encoding

4. **Pipeline Failures**:
   - Check execution logs for details
   - Verify agent configurations
   - Ensure output directories exist

### Debug Mode

Enable debug mode by setting environment variable:

```bash
export STREAMLIT_DEBUG=true
streamlit run ui/app.py
```

## Performance Considerations

- **Large Files**: Files over 10MB may cause performance issues
- **Memory Usage**: Complex analysis may require more RAM
- **Concurrent Users**: Single-user application by design
- **Session State**: Large files stored in session state use memory

## Security Notes

- API keys are stored securely using Streamlit's password input
- Configuration files may contain sensitive data
- Use HTTPS in production deployments
- Validate all user inputs

## Future Enhancements

Planned improvements:

1. **Multi-file Upload**: Support for project directories
2. **Real-time Collaboration**: Multiple users working together
3. **Advanced Visualizations**: Interactive dependency graphs
4. **Custom Themes**: User-selectable UI themes
5. **Export Options**: PDF reports, ZIP downloads
6. **Integration APIs**: REST API for external tools

## Support

For issues or questions:

1. Check the execution logs in the Upload tab
2. Review error messages in the UI
3. Consult the main project README.md
4. Check agent-specific documentation in `agents/README.md`