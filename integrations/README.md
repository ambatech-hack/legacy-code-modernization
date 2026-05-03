# IBM watsonx Orchestrate Integration

This directory contains the IBM watsonx Orchestrate integration for the Legacy Code Modernization Squad.

## Overview

The orchestration system coordinates three specialized agents in a sequential workflow:

1. **Code Analyzer (The Archaeologist)** - Analyzes legacy code structure and dependencies
2. **Documentation Agent (The Scribe)** - Generates comprehensive documentation
3. **Refactoring Agent (The Architect)** - Modernizes code to Python with tests

## Components

### 1. watsonx Client (`watsonx_client.py`)

Provides a unified interface to IBM watsonx AI services.

**Key Features:**
- Foundation model inference (Granite models)
- Workflow creation and execution
- Automatic retry logic
- Error handling

**Usage:**
```python
from integrations.watsonx_client import WatsonxClient

# Initialize client
client = WatsonxClient()

# Call a model
result = client.call_model(
    model_id="ibm/granite-13b-instruct-v2",
    prompt="Analyze this code...",
    parameters={"temperature": 0.1, "max_new_tokens": 2048}
)

# Create workflow
workflow = client.create_workflow(workflow_definition)
```

### 2. Orchestrator (`orchestrator.py`)

Coordinates the execution of all three agents in sequence.

**Key Features:**
- Sequential agent execution
- Error handling and recovery
- Progress tracking
- Result consolidation
- watsonx Orchestrate integration

**Usage:**
```python
from integrations.orchestrator import Orchestrator

# Initialize orchestrator
orchestrator = Orchestrator()

# Run complete pipeline
results = orchestrator.run_pipeline(
    legacy_code_path="samples/cobol/hello_world.cbl",
    language="cobol",
    output_dir="output"
)

# Print summary
print(orchestrator.get_pipeline_summary(results))
```

### 3. REST API (`api.py`)

FastAPI-based REST API for external access to the orchestration workflow.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| POST | `/modernize` | Trigger modernization workflow |
| POST | `/upload` | Upload file and trigger workflow |
| GET | `/status/{job_id}` | Get job status |
| GET | `/results/{job_id}` | Get job results |
| GET | `/jobs` | List all jobs |
| DELETE | `/jobs/{job_id}` | Cancel a job |
| GET | `/download/{job_id}/{file_type}` | Download result files |

**Usage:**
```bash
# Start API server
python scripts/run_api_server.py

# Or use uvicorn directly
uvicorn integrations.api:app --reload

# Access API documentation
# http://localhost:8000/docs
```

**Example API Calls:**

```bash
# Trigger modernization
curl -X POST "http://localhost:8000/modernize" \
  -H "Content-Type: application/json" \
  -d '{
    "legacy_code_path": "samples/cobol/hello_world.cbl",
    "language": "cobol",
    "output_dir": "output"
  }'

# Check job status
curl "http://localhost:8000/status/{job_id}"

# Get results
curl "http://localhost:8000/results/{job_id}"

# Upload file
curl -X POST "http://localhost:8000/upload" \
  -F "file=@path/to/legacy_code.cbl" \
  -F "language=cobol"
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# IBM watsonx Configuration
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_REGION=us-south

# Application Settings
LOG_LEVEL=INFO
OUTPUT_DIRECTORY=./output
```

### Agent Configuration

Agent settings are defined in `config/agent_configs.yaml`:

```yaml
analyzer:
  model: "ibm/granite-13b-instruct-v2"
  max_tokens: 4096
  temperature: 0.1

documentation:
  model: "ibm/granite-13b-instruct-v2"
  max_tokens: 8192
  temperature: 0.3

refactoring:
  model: "ibm/granite-20b-code-instruct"
  max_tokens: 8192
  temperature: 0.2

orchestrator:
  retry_attempts: 3
  retry_delay: 5
```

### Workflow Definition

The workflow is defined in `config/orchestrate_workflow.yaml`. This YAML file specifies:
- Workflow metadata
- Input parameters
- Step definitions
- Dependencies between steps
- Error handling policies
- Output specifications

## Testing

### Run Complete Test Suite

```bash
python scripts/test_orchestration.py
```

This will test:
1. watsonx client initialization
2. Orchestrator initialization
3. Workflow creation
4. Pipeline execution with sample COBOL
5. Output verification
6. API endpoints (if server is running)

### Run Individual Components

```python
# Test watsonx client
from integrations.watsonx_client import WatsonxClient
client = WatsonxClient()
print(f"Client available: {client.is_available()}")

# Test orchestrator
from integrations.orchestrator import Orchestrator
orchestrator = Orchestrator()
results = orchestrator.run_pipeline("samples/cobol/hello_world.cbl")

# Test API (start server first)
import requests
response = requests.get("http://localhost:8000/health")
print(response.json())
```

## Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request (API/UI)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Orchestrator  │
                  └────────┬───────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │   Agent 1: Code Analyzer            │
         │   - Parse code structure            │
         │   - Analyze dependencies            │
         │   - Calculate complexity            │
         │   Output: analysis_report.json      │
         └─────────────┬───────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────────────┐
         │   Agent 2: Documentation Agent      │
         │   - Generate README                 │
         │   - Create architecture docs        │
         │   - Add inline comments             │
         │   Output: documentation/            │
         └─────────────┬───────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────────────┐
         │   Agent 3: Refactoring Agent        │
         │   - Convert to Python               │
         │   - Apply best practices            │
         │   - Generate tests                  │
         │   Output: modernized/               │
         └─────────────┬───────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Return Results │
              └────────────────┘
```

## Error Handling

The orchestration system implements comprehensive error handling:

### Retry Logic
- Automatic retry on transient failures
- Configurable retry attempts and delays
- Exponential backoff

### Error Recovery
- Continue on non-critical failures
- Collect partial results
- Detailed error reporting

### Error Types

| Error Type | Recovery Strategy |
|------------|-------------------|
| File Not Found | Halt workflow, return error |
| Parse Error | Log warning, attempt partial analysis |
| Model API Error | Retry with exponential backoff |
| MCP Connection Error | Reconnect, retry operation |
| Test Failure | Log failures, continue |

## Performance Considerations

### Resource Limits
- Memory: 4GB recommended
- CPU: 2+ cores recommended
- Timeout: 15 minutes per workflow

### Optimization Tips
1. Use appropriate model sizes for your use case
2. Adjust temperature and max_tokens based on needs
3. Enable caching for repeated operations
4. Monitor API rate limits

## Security

### Authentication
- API key-based authentication for watsonx
- Optional token-based auth for REST API

### Data Protection
- Sensitive data masking in logs
- Secure credential storage
- Audit logging enabled

### Best Practices
1. Never commit API keys to version control
2. Use environment variables for credentials
3. Implement rate limiting in production
4. Enable HTTPS for API endpoints

## Troubleshooting

### Common Issues

**Issue: watsonx client not available**
```
Solution: Check that WATSONX_API_KEY and WATSONX_PROJECT_ID are set
```

**Issue: Pipeline fails at Agent 1**
```
Solution: Verify input file exists and is readable
Check file format is supported (COBOL, Java, VB)
```

**Issue: API server won't start**
```
Solution: Install dependencies: pip install fastapi uvicorn[standard]
Check port 8000 is not already in use
```

**Issue: Tests fail**
```
Solution: Ensure sample files exist in samples/cobol/
Run: python scripts/test_orchestration.py
Check logs for detailed error messages
```

## Development

### Adding New Agents

1. Create agent class in `agents/` directory
2. Add configuration to `config/agent_configs.yaml`
3. Update orchestrator to include new agent
4. Update workflow definition
5. Add tests

### Extending the API

1. Add new endpoint in `integrations/api.py`
2. Define request/response models
3. Implement endpoint logic
4. Add tests
5. Update documentation

## Support

For issues or questions:
- Check the logs in `logs/` directory
- Review error messages in API responses
- Run test suite for diagnostics
- Consult ARCHITECTURE.md for system design

## License

Made with Bob - IBM watsonx Hackathon 2026

---

**Last Updated:** 2026-05-01
**Version:** 1.0.0