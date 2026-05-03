# Legacy Code Modernization Agents

This directory contains the three AI agents that form the core of the Legacy Code Modernization Squad.

## Agent Overview

### 1. Code Analyzer (The Archaeologist) - `analyzer.py`

**Purpose:** Analyzes legacy code to understand its structure, dependencies, and complexity.

**Key Features:**
- Detects programming language automatically
- Parses code structure using AST
- Extracts functions and their metadata
- Analyzes dependencies and call graphs
- Detects technical debt and code smells
- Uses IBM Granite 13B for semantic insights

**Input:** Legacy code directory
**Output:** `output/analysis/analysis_report.json`

**Usage:**
```python
from agents.analyzer import CodeAnalyzer
import yaml

# Load configuration
with open('config/agent_configs.yaml') as f:
    config = yaml.safe_load(f)['analyzer']

# Initialize and run
analyzer = CodeAnalyzer(config)
report = analyzer.analyze_directory('samples/cobol')
```

**Test:** `python scripts/test_analyzer.py`

---

### 2. Documentation Agent (The Scribe) - `documentation.py`

**Purpose:** Generates comprehensive documentation from analysis reports.

**Key Features:**
- Generates project README.md
- Creates inline code comments
- Generates architecture documentation
- Creates data flow diagrams (ASCII)
- Documents dependencies and technical debt
- Uses IBM Granite 13B for intelligent documentation

**Input:** 
- `output/analysis/analysis_report.json`
- Legacy code files

**Output:** 
- `output/documentation/README.md`
- `output/documentation/inline_comments.json`
- `output/documentation/ARCHITECTURE.md`
- `output/documentation/DEPENDENCIES.md`
- `output/documentation/TECHNICAL_DEBT.md`

**Usage:**
```python
from agents.documentation import DocumentationAgent
import yaml

# Load configuration
with open('config/agent_configs.yaml') as f:
    config = yaml.safe_load(f)['documentation']

# Initialize and run
doc_agent = DocumentationAgent(config)
results = doc_agent.generate_documentation(
    analysis_path='output/analysis/analysis_report.json',
    legacy_dir='samples/cobol'
)
```

**Test:** `python scripts/test_documentation.py`

---

### 3. Refactoring Agent (The Architect) - `refactoring.py`

**Purpose:** Modernizes legacy code to Python with comprehensive tests.

**Key Features:**
- Converts COBOL, Visual Basic, and Java to modern Python
- Restructures procedural code to OOP
- Applies modern design patterns
- Inserts inline comments from Agent 2
- Generates pytest unit tests
- Runs tests automatically
- Uses IBM Granite 20B Code for intelligent conversion

**Input:**
- Legacy code directory
- `output/analysis/analysis_report.json`
- `output/documentation/inline_comments.json`

**Output:**
- `output/modernized/{module}.py` - Modernized Python code
- `output/modernized/test_{module}.py` - Unit tests
- `output/modernized/modernization_report.json` - Transformation summary

**Usage:**
```python
from agents.refactoring import RefactoringAgent
import yaml

# Load configuration
with open('config/agent_configs.yaml') as f:
    config = yaml.safe_load(f)['refactoring']

# Initialize and run
refactoring_agent = RefactoringAgent(config)
results = refactoring_agent.modernize_code(
    legacy_dir='samples/cobol',
    analysis_path='output/analysis/analysis_report.json',
    comments_path='output/documentation/inline_comments.json'
)
```

**Test:** `python scripts/test_refactoring.py`

---

## Complete Pipeline

To run all three agents in sequence:

```bash
# Step 1: Analyze legacy code
python scripts/test_analyzer.py

# Step 2: Generate documentation
python scripts/test_documentation.py

# Step 3: Modernize code
python scripts/test_refactoring.py
```

Or use the orchestrator (when implemented):

```python
from agents.orchestrator import Orchestrator

orchestrator = Orchestrator()
results = orchestrator.run_pipeline('samples/cobol')
```

---

## Language Support

### COBOL → Python
- ✅ IDENTIFICATION DIVISION → Module docstring
- ✅ DATA DIVISION → Class attributes
- ✅ PROCEDURE DIVISION → Methods
- ✅ PIC types → Python types
- ✅ PERFORM → Function calls
- ✅ DISPLAY → print() or logging

### Visual Basic → Python
- ✅ Sub/Function → def
- ✅ Dim → Variable assignments with type hints
- ✅ Class → Python class
- ✅ Error handling → try/except

### Java → Python
- ✅ Class structure preservation
- ✅ Methods with decorators
- ✅ Interfaces → Abstract Base Classes
- ✅ Exception handling

---

## IBM watsonx Integration

All agents use IBM watsonx AI models:

- **Analyzer:** `ibm/granite-13b-instruct-v2`
- **Documentation:** `ibm/granite-13b-instruct-v2`
- **Refactoring:** `ibm/granite-20b-code-instruct`

### Configuration

Set environment variables in `.env`:

```bash
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_REGION=us-south
```

If credentials are not provided, agents will fall back to template-based generation.

---

## Output Structure

```
output/
├── analysis/
│   └── analysis_report.json          # Code analysis results
├── documentation/
│   ├── README.md                      # Project documentation
│   ├── inline_comments.json           # Code comments
│   ├── ARCHITECTURE.md                # Architecture docs
│   ├── DEPENDENCIES.md                # Dependency analysis
│   └── TECHNICAL_DEBT.md              # Technical debt report
└── modernized/
    ├── {module}.py                    # Modernized Python code
    ├── test_{module}.py               # Unit tests
    ├── test_results.json              # Test execution results
    └── modernization_report.json      # Transformation summary
```

---

## Error Handling

All agents include comprehensive error handling:

- **File I/O errors:** Graceful fallback with logging
- **API failures:** Template-based generation fallback
- **Parsing errors:** Detailed error messages with context
- **Unsupported languages:** Clear warnings and suggestions

---

## Testing

Each agent has a dedicated test script:

- `scripts/test_analyzer.py` - Tests code analysis
- `scripts/test_documentation.py` - Tests documentation generation
- `scripts/test_refactoring.py` - Tests code modernization

All tests use the sample COBOL file in `samples/cobol/hello_world.cbl`.

---

## Performance

Typical execution times (without IBM watsonx):

- **Analyzer:** ~1-2 seconds for small files
- **Documentation:** ~2-3 seconds
- **Refactoring:** ~2-3 seconds

With IBM watsonx API calls, add 5-10 seconds per agent.

---

## Future Enhancements

- [ ] Support for more languages (C, C++, Fortran)
- [ ] Advanced design pattern detection
- [ ] Automated refactoring suggestions
- [ ] Integration with GitHub/GitLab
- [ ] Real-time collaboration features
- [ ] Code quality metrics dashboard
- [ ] Automated PR creation
- [ ] CI/CD integration

---

## Contributing

When adding new features to agents:

1. Update the agent class with new methods
2. Add corresponding tests
3. Update this README
4. Update `config/agent_configs.yaml` if needed
5. Document any new dependencies

---

## License

Part of the Legacy Code Modernization Squad project.

**Made with Bob** 🤖

---

## Support

For issues or questions:
- Check the main project README
- Review the ARCHITECTURE.md
- Run test scripts to verify setup
- Check logs in the console output
