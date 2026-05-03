"""
Test Script for watsonx Orchestrate Integration

Tests the complete orchestration workflow:
1. Initialize orchestrator
2. Run pipeline with sample COBOL code
3. Verify all agents execute
4. Check results
"""

import os
import sys
import json
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from integrations.orchestrator import Orchestrator
from integrations.watsonx_client import WatsonxClient


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_watsonx_client():
    """Test watsonx client initialization."""
    print_section("TEST 1: watsonx Client Initialization")
    
    try:
        client = WatsonxClient()
        
        print(f"[OK] Client created")
        print(f"  - Available: {client.is_available()}")
        print(f"  - Region: {client.region}")
        print(f"  - URL: {client.url}")
        
        if client.is_available():
            print("\n[OK] watsonx client is fully initialized and ready")
        else:
            print("\n[WARN] watsonx client is in mock mode (credentials not configured)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to initialize client: {e}")
        return False


def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    print_section("TEST 2: Orchestrator Initialization")
    
    try:
        orchestrator = Orchestrator()
        
        print(f"[OK] Orchestrator created")
        print(f"  - Analyzer: {orchestrator.analyzer.name}")
        print(f"  - Documentation Agent: {orchestrator.documentation_agent.name}")
        print(f"  - Refactoring Agent: {orchestrator.refactoring_agent.name}")
        print(f"  - Retry attempts: {orchestrator.retry_attempts}")
        print(f"  - Retry delay: {orchestrator.retry_delay}s")
        
        print("\n[OK] All three agents initialized successfully")
        
        return orchestrator
        
    except Exception as e:
        print(f"[FAIL] Failed to initialize orchestrator: {e}")
        return None


def test_workflow_creation(orchestrator: Orchestrator):
    """Test workflow creation in watsonx Orchestrate."""
    print_section("TEST 3: Workflow Creation")
    
    try:
        result = orchestrator.create_watsonx_workflow()
        
        print(f"Success: {result.get('success')}")
        print(f"Workflow ID: {result.get('workflow_id')}")
        
        if result.get('metadata'):
            metadata = result['metadata']
            print(f"Workflow Name: {metadata.get('name')}")
            print(f"Steps: {metadata.get('steps')}")
        
        if result.get('success'):
            print("\n[OK] Workflow created successfully")
        else:
            print(f"\n[WARN] Workflow creation returned: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"[FAIL] Failed to create workflow: {e}")
        return False


def test_pipeline_execution(orchestrator: Orchestrator):
    """Test complete pipeline execution with sample COBOL code."""
    print_section("TEST 4: Pipeline Execution")
    
    # Use sample COBOL directory
    sample_path = "samples/cobol"
    
    if not os.path.exists(sample_path):
        print(f"[FAIL] Sample directory not found: {sample_path}")
        return None
    
    print(f"Input directory: {sample_path}")
    print(f"Language: COBOL")
    print(f"Output directory: output/test_orchestration")
    print("\nStarting pipeline execution...\n")
    
    try:
        start_time = time.time()
        
        # Run pipeline
        results = orchestrator.run_pipeline(
            legacy_code_path=sample_path,
            language="cobol",
            output_dir="output/test_orchestration"
        )
        
        elapsed_time = time.time() - start_time
        
        # Print results
        print("\n" + "-" * 70)
        print("PIPELINE RESULTS")
        print("-" * 70)
        
        print(f"\nOverall Success: {results.get('success')}")
        print(f"Execution ID: {results.get('execution_id')}")
        print(f"Elapsed Time: {elapsed_time:.2f}s")
        
        # Agent results
        print("\nAgent Results:")
        agent_results = results.get('results', {})
        
        for agent_name in ['analysis', 'documentation', 'refactoring']:
            if agent_name in agent_results:
                agent_result = agent_results[agent_name]
                status = "[OK]" if agent_result.get('success') else "[FAIL]"
                print(f"  {status} {agent_name.title()}")
                
                if agent_result.get('output_path'):
                    print(f"      Output: {agent_result['output_path']}")
                elif agent_result.get('output_dir'):
                    print(f"      Output: {agent_result['output_dir']}")
            else:
                print(f"  - {agent_name.title()} (not executed)")
        
        # Errors
        errors = results.get('errors', [])
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  [FAIL] {error.get('agent')}: {error.get('error')}")
        
        # Metadata
        metadata = results.get('metadata', {})
        if metadata:
            print("\nMetadata:")
            print(f"  Start Time: {metadata.get('start_time')}")
            print(f"  End Time: {metadata.get('end_time')}")
            if 'completed_agents' in metadata:
                print(f"  Completed Agents: {', '.join(metadata['completed_agents'])}")
        
        # Print summary
        print("\n" + orchestrator.get_pipeline_summary(results))
        
        return results
        
    except Exception as e:
        print(f"\n[FAIL] Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_outputs(results: dict):
    """Verify that all expected outputs were created."""
    print_section("TEST 5: Output Verification")
    
    if not results or not results.get('success'):
        print("[WARN] Pipeline did not complete successfully, skipping verification")
        return False
    
    output_dir = "output/test_orchestration"
    expected_files = [
        "analysis/analysis_report.json",
        "documentation/README.md",
        "documentation/ARCHITECTURE.md",
        "modernized/*.py",
        "pipeline_results.json"
    ]
    
    all_found = True
    
    for file_pattern in expected_files:
        file_path = os.path.join(output_dir, file_pattern)
        
        if "*" in file_pattern:
            # Check if directory exists and has files
            dir_path = os.path.dirname(file_path)
            if os.path.exists(dir_path) and os.listdir(dir_path):
                print(f"[OK] {file_pattern} - Found files in directory")
            else:
                print(f"[FAIL] {file_pattern} - No files found")
                all_found = False
        else:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"[OK] {file_pattern} - {size} bytes")
            else:
                print(f"[FAIL] {file_pattern} - Not found")
                all_found = False
    
    if all_found:
        print("\n[OK] All expected outputs were created")
    else:
        print("\n[WARN] Some expected outputs are missing")
    
    return all_found


def test_api_endpoints():
    """Test API endpoints (if FastAPI is available)."""
    print_section("TEST 6: API Endpoints (Optional)")
    
    try:
        import requests
        
        # Check if API server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("[OK] API server is running")
                print(f"  Health check: {response.json()}")
                return True
            else:
                print(f"[WARN] API server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("[WARN] API server is not running")
            print("  To test API endpoints, run: uvicorn integrations.api:app --reload")
            return False
            
    except ImportError:
        print("[WARN] requests library not installed, skipping API tests")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  WATSONX ORCHESTRATE INTEGRATION TEST SUITE")
    print("=" * 70)
    
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    results = {
        "watsonx_client": False,
        "orchestrator": False,
        "workflow_creation": False,
        "pipeline_execution": False,
        "output_verification": False,
        "api_endpoints": False
    }
    
    # Test 1: watsonx Client
    results["watsonx_client"] = test_watsonx_client()
    
    # Test 2: Orchestrator Initialization
    orchestrator = test_orchestrator_initialization()
    results["orchestrator"] = orchestrator is not None
    
    if not orchestrator:
        print("\n[FAIL] Cannot continue tests without orchestrator")
        print_final_summary(results)
        return
    
    # Test 3: Workflow Creation
    results["workflow_creation"] = test_workflow_creation(orchestrator)
    
    # Test 4: Pipeline Execution
    pipeline_results = test_pipeline_execution(orchestrator)
    results["pipeline_execution"] = pipeline_results is not None and pipeline_results.get('success', False)
    
    # Test 5: Output Verification
    if pipeline_results:
        results["output_verification"] = verify_outputs(pipeline_results)
    
    # Test 6: API Endpoints (optional)
    results["api_endpoints"] = test_api_endpoints()
    
    # Print final summary
    print_final_summary(results)


def print_final_summary(results: dict):
    """Print final test summary."""
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print("Test Results:")
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n[SUCCESS] All tests passed! Orchestration is working correctly.")
    elif passed_tests >= total_tests - 1:  # Allow API test to fail
        print("\n[OK] Core orchestration tests passed!")
    else:
        print("\n[WARN] Some tests failed. Check the output above for details.")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()


