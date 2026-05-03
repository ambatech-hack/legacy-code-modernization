# User Guide

Welcome to the IBM Bob Legacy Code Modernization Platform! This guide will help you get started and make the most of the platform's features.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Using the Web Interface](#using-the-web-interface)
- [Using the REST API](#using-the-rest-api)
- [Using the Command Line](#using-the-command-line)
- [Understanding the Output](#understanding-the-output)
- [Configuration Options](#configuration-options)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Introduction

IBM Bob is an AI-powered platform that automates the modernization of legacy code using IBM watsonx.ai. It consists of three specialized agents:

1. **Analyzer Agent** - Analyzes code quality, complexity, and issues
2. **Documentation Agent** - Generates comprehensive documentation
3. **Refactoring Agent** - Modernizes code to target languages

### What Can IBM Bob Do?

- ✅ Analyze legacy code for issues and complexity
- ✅ Generate comprehensive documentation automatically
- ✅ Convert COBOL, Java, VB to modern Python
- ✅ Create unit tests for modernized code
- ✅ Identify technical debt and security vulnerabilities
- ✅ Provide migration guides and recommendations

### Supported Languages

**Source Languages:**
- COBOL
- Java
- Visual Basic (VB)
- More coming soon!

**Target Languages:**
- Python (primary)
- JavaScript (experimental)
- Java (modern version)

## Getting Started

### Prerequisites

Before you begin, ensure you have:
- ✅ IBM Bob installed (see [INSTALLATION.md](INSTALLATION.md))
- ✅ IBM watsonx.ai API key configured
- ✅ Legacy code files ready for modernization

### Quick Start

1. **Start the application:**
```bash
# Option 1: Web Interface
streamlit run ui/app.py

# Option 2: REST API
python scripts/run_api_server.py
```

2. **Access the interface:**
- Web UI: http://localhost:8501
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

3. **Upload your legacy code**
4. **Select the modernization options**
5. **Run the agents**
6. **Download the results**

## Using the Web Interface

The Streamlit web interface provides an intuitive way to modernize your code.

### Step 1: Upload Code

1. Navigate to the **Upload** tab
2. Click **Browse files** or drag and drop your file
3. Supported formats: `.cbl`, `.java`, `.vb`, `.txt`
4. Maximum file size: 10 MB

**Tips:**
- Upload one file at a time for best results
- Ensure file encoding is UTF-8
- Remove any sensitive data before uploading

### Step 2: Configure Options

In the **Settings** tab, configure:

**Analysis Options:**
- ☑️ Detect code smells
- ☑️ Calculate complexity metrics
- ☑️ Identify security issues
- ☑️ Generate recommendations

**Documentation Options:**
- ☑️ Generate README
- ☑️ Create architecture docs
- ☑️ Map dependencies
- ☑️ Document technical debt
- ☑️ Add inline comments

**Refactoring Options:**
- **Target Language:** Python, JavaScript, Java
- **Style:** Object-oriented, Functional, Hybrid
- ☑️ Generate unit tests
- ☑️ Add type hints
- ☑️ Include migration guide

### Step 3: Run Agents

1. Click **Analyze Code** to run the Analyzer Agent
2. Review the analysis results
3. Click **Generate Documentation** to create docs
4. Review the generated documentation
5. Click **Modernize Code** to refactor
6. Review the modernized code

**Progress Indicators:**
- 🔄 Processing - Agent is working
- ✅ Complete - Agent finished successfully
- ❌ Error - Something went wrong

### Step 4: Review Results

Each agent produces different outputs:

**Analysis Results:**
- Code metrics (LOC, complexity, maintainability)
- Issues by severity (critical, high, medium, low)
- Recommendations for improvement
- Detailed analysis report (JSON)

**Documentation Results:**
- README.md with usage instructions
- ARCHITECTURE.md with design overview
- DEPENDENCIES.md with dependency map
- TECHNICAL_DEBT.md with debt analysis
- Inline comments (JSON format)

**Refactoring Results:**
- Modernized code in target language
- Unit tests
- Migration guide
- Modernization report (JSON)

### Step 5: Download Results

1. Navigate to the **Results** tab
2. Click **Download All** for complete package
3. Or download individual files:
   - Analysis report
   - Documentation files
   - Modernized code
   - Unit tests

**Output Structure:**
```
output/
├── analysis/
│   └── analysis_report.json
├── documentation/
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── DEPENDENCIES.md
│   ├── TECHNICAL_DEBT.md
│   └── inline_comments.json
└── modernized/
    ├── your_file.py
    ├── test_your_file.py
    └── modernization_report.json
```

## Using the REST API

The REST API provides programmatic access to all features.

### Authentication

Include your API key in requests (if authentication is enabled):

```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/v1/analyze
```

### Endpoints

#### 1. Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-01T14:00:00Z"
}
```

#### 2. Analyze Code

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@samples/cobol/hello_world.cbl" \
  -F "options={\"detect_code_smells\":true,\"calculate_metrics\":true}"
```

Response:
```json
{
  "status": "success",
  "analysis_id": "abc123",
  "metrics": {
    "lines_of_code": 50,
    "complexity_score": 7.5,
    "maintainability_index": 65
  },
  "issues": [...],
  "recommendations": [...]
}
```

#### 3. Generate Documentation

```bash
curl -X POST http://localhost:8000/api/v1/document \
  -F "file=@samples/cobol/hello_world.cbl" \
  -F "options={\"generate_readme\":true,\"generate_architecture\":true}"
```

Response:
```json
{
  "status": "success",
  "documentation_id": "def456",
  "files": [
    "README.md",
    "ARCHITECTURE.md",
    "DEPENDENCIES.md"
  ]
}
```

#### 4. Modernize Code

```bash
curl -X POST http://localhost:8000/api/v1/refactor \
  -F "file=@samples/cobol/hello_world.cbl" \
  -F "target_language=python" \
  -F "options={\"generate_tests\":true,\"add_type_hints\":true}"
```

Response:
```json
{
  "status": "success",
  "refactoring_id": "ghi789",
  "target_language": "python",
  "output_file": "hello_world.py",
  "test_file": "test_hello_world.py"
}
```

#### 5. Run Complete Workflow

```bash
curl -X POST http://localhost:8000/api/v1/orchestrate \
  -F "file=@samples/cobol/hello_world.cbl" \
  -F "target_language=python" \
  -F "run_analysis=true" \
  -F "run_documentation=true" \
  -F "run_refactoring=true"
```

Response:
```json
{
  "status": "success",
  "workflow_id": "jkl012",
  "analysis": {...},
  "documentation": {...},
  "refactoring": {...}
}
```

### Python Client Example

```python
import requests

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "your_api_key"

# Headers
headers = {"X-API-Key": API_KEY}

# Upload and analyze
with open("samples/cobol/hello_world.cbl", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{API_URL}/api/v1/analyze",
        files=files,
        headers=headers
    )
    
result = response.json()
print(f"Analysis complete: {result['status']}")
print(f"Complexity: {result['metrics']['complexity_score']}")
```

### JavaScript Client Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const API_URL = 'http://localhost:8000';
const API_KEY = 'your_api_key';

async function analyzeCode(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  
  const response = await axios.post(
    `${API_URL}/api/v1/analyze`,
    form,
    {
      headers: {
        ...form.getHeaders(),
        'X-API-Key': API_KEY
      }
    }
  );
  
  return response.data;
}

// Usage
analyzeCode('samples/cobol/hello_world.cbl')
  .then(result => console.log('Analysis:', result))
  .catch(error => console.error('Error:', error));
```

## Using the Command Line

For automation and scripting, use the command-line interface.

### Analyze Code

```bash
python -m agents.analyzer samples/cobol/hello_world.cbl
```

### Generate Documentation

```bash
python -m agents.documentation samples/cobol/hello_world.cbl
```

### Modernize Code

```bash
python -m agents.refactoring samples/cobol/hello_world.cbl --target python
```

### Run Complete Workflow

```bash
python scripts/test_orchestration.py samples/cobol/hello_world.cbl
```

### Batch Processing

Process multiple files:

```bash
# Create a script
cat > process_all.sh << 'EOF'
#!/bin/bash
for file in samples/cobol/*.cbl; do
  echo "Processing $file..."
  python -m agents.analyzer "$file"
  python -m agents.documentation "$file"
  python -m agents.refactoring "$file" --target python
done
EOF

chmod +x process_all.sh
./process_all.sh
```

## Understanding the Output

### Analysis Report

The analysis report (`analysis_report.json`) contains:

```json
{
  "file_info": {
    "name": "hello_world.cbl",
    "language": "COBOL",
    "size_bytes": 1024,
    "lines_of_code": 50
  },
  "metrics": {
    "complexity_score": 7.5,
    "maintainability_index": 65,
    "technical_debt_ratio": 0.15
  },
  "issues": [
    {
      "severity": "high",
      "type": "code_smell",
      "description": "Long method detected",
      "line": 42,
      "recommendation": "Split into smaller methods"
    }
  ],
  "recommendations": [
    "Refactor long methods",
    "Add error handling",
    "Improve naming conventions"
  ]
}
```

**Key Metrics:**
- **Complexity Score:** 0-10 (lower is better)
  - 0-3: Simple
  - 4-6: Moderate
  - 7-10: Complex
- **Maintainability Index:** 0-100 (higher is better)
  - 0-25: Difficult to maintain
  - 26-50: Moderate maintainability
  - 51-75: Good maintainability
  - 76-100: Excellent maintainability
- **Technical Debt Ratio:** 0-1 (lower is better)
  - 0-0.05: Low debt
  - 0.06-0.15: Moderate debt
  - 0.16+: High debt

### Documentation Files

**README.md:**
- Project overview
- Installation instructions
- Usage examples
- Configuration options

**ARCHITECTURE.md:**
- System design
- Component relationships
- Data flow
- Design patterns used

**DEPENDENCIES.md:**
- External dependencies
- Internal dependencies
- Dependency graph
- Version requirements

**TECHNICAL_DEBT.md:**
- Identified debt items
- Priority levels
- Remediation suggestions
- Estimated effort

### Modernized Code

The modernized code includes:

**Main Code File:**
- Clean, readable code
- Modern language features
- Type hints (Python)
- Comprehensive comments
- Error handling
- Logging

**Test File:**
- Unit tests for all functions
- Edge case coverage
- Mock objects for dependencies
- Test fixtures
- Assertions

**Migration Guide:**
- Step-by-step migration process
- Breaking changes
- Configuration updates
- Testing recommendations
- Rollback procedures

## Configuration Options

### Agent Configuration

Edit `config/agent_configs.yaml`:

```yaml
analyzer:
  model_id: "ibm/granite-13b-chat-v2"
  max_tokens: 2048
  temperature: 0.7
  detect_code_smells: true
  calculate_metrics: true
  identify_security_issues: true

documentation:
  model_id: "ibm/granite-13b-chat-v2"
  max_tokens: 3000
  temperature: 0.5
  generate_readme: true
  generate_architecture: true
  generate_dependencies: true
  generate_technical_debt: true
  add_inline_comments: true

refactoring:
  model_id: "ibm/granite-13b-chat-v2"
  max_tokens: 4096
  temperature: 0.3
  target_language: "python"
  code_style: "object_oriented"
  generate_tests: true
  add_type_hints: true
  include_migration_guide: true
```

### Environment Variables

Edit `.env`:

```env
# watsonx.ai Configuration
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2

# Generation Parameters
WATSONX_MAX_TOKENS=2048
WATSONX_TEMPERATURE=0.7
WATSONX_TOP_P=1.0
WATSONX_TOP_K=50

# Output Configuration
OUTPUT_DIR=./output
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

## Best Practices

### Preparing Your Code

1. **Clean Up First:**
   - Remove commented-out code
   - Fix obvious syntax errors
   - Remove sensitive data

2. **Organize Files:**
   - One logical unit per file
   - Keep files under 5,000 lines
   - Use meaningful file names

3. **Document Context:**
   - Add comments explaining business logic
   - Document external dependencies
   - Note any special requirements

### Running the Agents

1. **Start with Analysis:**
   - Always run analyzer first
   - Review issues before modernizing
   - Address critical issues manually if needed

2. **Generate Documentation:**
   - Run before refactoring
   - Review for accuracy
   - Use as reference during migration

3. **Modernize Incrementally:**
   - Start with small files
   - Test each conversion
   - Refactor in stages

### Reviewing Output

1. **Verify Correctness:**
   - Compare logic with original
   - Run generated tests
   - Test edge cases

2. **Check Quality:**
   - Review code style
   - Verify error handling
   - Check performance

3. **Validate Documentation:**
   - Ensure accuracy
   - Update as needed
   - Add project-specific details

## Troubleshooting

### Common Issues

#### Issue: Upload Fails

**Symptoms:** File upload returns error

**Solutions:**
- Check file size (max 10 MB)
- Verify file format is supported
- Ensure file is not corrupted
- Check file encoding (use UTF-8)

#### Issue: Analysis Takes Too Long

**Symptoms:** Analysis doesn't complete

**Solutions:**
- Check internet connection
- Verify watsonx.ai API status
- Reduce file size
- Lower max_tokens in config

#### Issue: Poor Quality Output

**Symptoms:** Generated code has issues

**Solutions:**
- Improve input code quality
- Add more context in comments
- Adjust temperature (lower = more conservative)
- Try different model
- Review and manually refine

#### Issue: API Authentication Fails

**Symptoms:** 401 or 403 errors

**Solutions:**
- Verify API key in `.env`
- Check API key permissions
- Regenerate API key if needed
- Verify project ID is correct

### Getting Help

1. **Check Logs:**
```bash
tail -f logs/app.log
```

2. **Enable Debug Mode:**
```env
LOG_LEVEL=DEBUG
```

3. **Contact Support:**
- GitHub Issues
- Email: support@example.com
- Documentation: [docs/](docs/)

## FAQ

**Q: How long does modernization take?**
A: Typically 30-120 seconds per file, depending on size and complexity.

**Q: Is the output production-ready?**
A: The output is high-quality but should be reviewed and tested before production use.

**Q: Can I customize the output style?**
A: Yes, through agent configuration files and environment variables.

**Q: What if my language isn't supported?**
A: Contact us about adding support, or contribute to the project.

**Q: How accurate is the conversion?**
A: IBM watsonx.ai provides high accuracy, but manual review is recommended.

**Q: Can I process multiple files at once?**
A: Yes, use the API or command-line batch processing.

**Q: Is my code kept private?**
A: Code is processed through IBM watsonx.ai. Review IBM's privacy policy.

**Q: What about database connections?**
A: The agents identify and document dependencies. Modern equivalents are suggested.

**Q: Can I undo a modernization?**
A: Original files are never modified. Keep backups of all files.

**Q: How much does it cost?**
A: Costs are based on IBM watsonx.ai API usage, typically $0.10-$1.00 per file.

## Next Steps

Now that you're familiar with IBM Bob:

1. **Try the Demo:** [DEMO.md](DEMO.md)
2. **Explore the API:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
3. **Learn Development:** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
4. **Deploy to Production:** [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Happy modernizing! 🚀**

Need help? Check our [documentation](docs/) or [create an issue](https://github.com/your-org/ibm-bob-hackathon/issues).