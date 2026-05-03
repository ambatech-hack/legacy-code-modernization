"""
Orchestrator for Legacy Code Modernization Squad

Coordinates the execution of three agents in sequence:
1. Code Analyzer (The Archaeologist)
2. Documentation Agent (The Scribe)
3. Refactoring Agent (The Architect)

Uses IBM watsonx Orchestrate for workflow management.
"""

import os
import json
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from loguru import logger

from agents.analyzer import CodeAnalyzer
from agents.documentation import DocumentationAgent
from agents.refactoring import RefactoringAgent
from integrations.watsonx_client import WatsonxClient
from utils.file_handler import read_file_safe, ensure_directory


class Orchestrator:
    """
    Main orchestrator that coordinates the three-agent modernization pipeline.
    
    Workflow:
    1. Agent 1 (Analyzer) → Analyzes legacy code
    2. Agent 2 (Documentation) → Generates documentation
    3. Agent 3 (Refactoring) → Modernizes code and creates tests
    
    Features:
    - Sequential agent execution
    - Error handling and recovery
    - Progress tracking
    - Result consolidation
    - watsonx Orchestrate integration
    """
    
    def __init__(self, config_path: str = "config/agent_configs.yaml"):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to agent configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize watsonx client
        self.watsonx_client = WatsonxClient()
        
        # Initialize agents
        self.analyzer = CodeAnalyzer(self.config.get('analyzer', {}))
        self.documentation_agent = DocumentationAgent(self.config.get('documentation', {}))
        self.refactoring_agent = RefactoringAgent(self.config.get('refactoring', {}))
        
        # Orchestrator config
        self.orchestrator_config = self.config.get('orchestrator', {})
        self.retry_attempts = self.orchestrator_config.get('retry_attempts', 3)
        self.retry_delay = self.orchestrator_config.get('retry_delay', 5)
        
        # Workflow state
        self.workflow_id = None
        self.execution_id = None
        
        logger.info("Orchestrator initialized with all three agents")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def run_pipeline(
        self,
        legacy_code_path: str,
        language: Optional[str] = None,
        output_dir: str = "output"
    ) -> Dict[str, Any]:
        """
        Execute the complete modernization pipeline.
        
        Args:
            legacy_code_path: Path to legacy code file or directory
            language: Programming language (auto-detected if None)
            output_dir: Base output directory
        
        Returns:
            Dict containing:
                - success: bool
                - results: dict with outputs from all agents
                - errors: list of errors encountered
                - metadata: execution metadata
        """
        start_time = time.time()
        execution_id = f"exec_{int(start_time)}"
        
        logger.info(f"Starting modernization pipeline (execution: {execution_id})")
        logger.info(f"Input: {legacy_code_path}")
        
        results = {
            "success": False,
            "execution_id": execution_id,
            "results": {},
            "errors": [],
            "metadata": {
                "start_time": datetime.utcnow().isoformat(),
                "input_path": legacy_code_path,
                "language": language,
                "output_dir": output_dir
            }
        }
        
        try:
            # Step 1: Run Code Analyzer
            logger.info("=" * 60)
            logger.info("STEP 1: Running Code Analyzer")
            logger.info("=" * 60)
            
            analysis_result = self._run_with_retry(
                agent_name="analyzer",
                agent_func=self.analyzer.analyze_directory,
                directory_path=legacy_code_path
            )
            
            if not analysis_result.get("success"):
                error_msg = f"Code Analyzer failed: {analysis_result.get('error')}"
                logger.error(error_msg)
                results["errors"].append({
                    "agent": "analyzer",
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                return results
            
            results["results"]["analysis"] = analysis_result
            # Save analysis report and get path
            analysis_data = analysis_result.get("data", analysis_result)
            analysis_report_path = os.path.join(output_dir, "analysis", "analysis_report.json")
            ensure_directory(os.path.dirname(analysis_report_path))
            with open(analysis_report_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            logger.info(f"[OK] Code Analyzer completed: {analysis_report_path}")
            
            # Step 2: Run Documentation Agent
            logger.info("=" * 60)
            logger.info("STEP 2: Running Documentation Agent")
            logger.info("=" * 60)
            
            documentation_result = self._run_with_retry(
                agent_name="documentation",
                agent_func=self.documentation_agent.generate_documentation,
                analysis_report_path=analysis_report_path
            )
            
            if not documentation_result.get("success"):
                error_msg = f"Documentation Agent failed: {documentation_result.get('error')}"
                logger.error(error_msg)
                results["errors"].append({
                    "agent": "documentation",
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                # Continue to refactoring even if documentation fails
                logger.warning("Continuing to refactoring despite documentation failure")
            else:
                # Save documentation files
                doc_data = documentation_result.get("data", documentation_result)
                doc_output_dir = os.path.join(output_dir, "documentation")
                save_result = self.documentation_agent.save_documentation(doc_data, doc_output_dir)
                documentation_result["output_dir"] = doc_output_dir
                documentation_result["save_result"] = save_result
                results["results"]["documentation"] = documentation_result
                logger.info(f"[OK] Documentation Agent completed")
            
            # Step 3: Run Refactoring Agent
            logger.info("=" * 60)
            logger.info("STEP 3: Running Refactoring Agent")
            logger.info("=" * 60)
            
            # Get comments path if documentation succeeded
            comments_path = os.path.join(output_dir, "documentation", "inline_comments.json")
            if not documentation_result.get("success") or not os.path.exists(comments_path):
                comments_path = None
            
            refactoring_result = self._run_with_retry(
                agent_name="refactoring",
                agent_func=self.refactoring_agent.modernize_code,
                legacy_dir=legacy_code_path,
                analysis_path=analysis_report_path,
                comments_path=comments_path if comments_path else analysis_report_path,  # Fallback to analysis if no comments
                output_dir=os.path.join(output_dir, "modernized")
            )
            
            if not refactoring_result.get("success"):
                error_msg = f"Refactoring Agent failed: {refactoring_result.get('error')}"
                logger.error(error_msg)
                results["errors"].append({
                    "agent": "refactoring",
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                return results
            
            results["results"]["refactoring"] = refactoring_result
            logger.info(f"[OK] Refactoring Agent completed")
            
            # Pipeline completed successfully
            elapsed_time = time.time() - start_time
            results["success"] = True
            results["metadata"]["end_time"] = datetime.utcnow().isoformat()
            results["metadata"]["elapsed_time"] = elapsed_time
            results["metadata"]["completed_agents"] = ["analyzer", "documentation", "refactoring"]
            
            logger.info("=" * 60)
            logger.info(f"[OK] Pipeline completed successfully in {elapsed_time:.2f}s")
            logger.info("=" * 60)
            
            # Save consolidated results
            self._save_consolidated_results(results, output_dir)
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            results["errors"].append({
                "agent": "orchestrator",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            results["metadata"]["end_time"] = datetime.utcnow().isoformat()
            return results
    
    def _run_with_retry(
        self,
        agent_name: str,
        agent_func: callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run an agent function with retry logic.
        
        Args:
            agent_name: Name of the agent
            agent_func: Agent function to call
            **kwargs: Arguments to pass to the agent function
        
        Returns:
            Agent result dict with success, data, and error fields
        """
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Executing {agent_name} (attempt {attempt + 1}/{self.retry_attempts})")
                result = agent_func(**kwargs)
                
                # If result is a dict with 'success' key, use it as-is
                if isinstance(result, dict) and "success" in result:
                    if result.get("success"):
                        if attempt > 0:
                            logger.info(f"{agent_name} succeeded on attempt {attempt + 1}")
                        return result
                    last_error = result.get("error", "Unknown error")
                    logger.warning(f"{agent_name} failed: {last_error}")
                # Otherwise, wrap the result as successful
                elif result is not None:
                    if attempt > 0:
                        logger.info(f"{agent_name} succeeded on attempt {attempt + 1}")
                    return {
                        "success": True,
                        "data": result,
                        "error": None
                    }
                else:
                    last_error = "Agent returned None"
                    logger.warning(f"{agent_name} returned None")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"{agent_name} raised exception: {e}")
            
            if attempt < self.retry_attempts - 1:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        logger.error(f"{agent_name} failed after {self.retry_attempts} attempts")
        return {
            "success": False,
            "error": f"Failed after {self.retry_attempts} attempts. Last error: {last_error}",
            "retry_count": self.retry_attempts
        }
    
    def _save_consolidated_results(self, results: Dict[str, Any], output_dir: str):
        """Save consolidated results to JSON file."""
        try:
            ensure_directory(output_dir)
            output_path = os.path.join(output_dir, "pipeline_results.json")
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Consolidated results saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save consolidated results: {e}")
    
    def create_watsonx_workflow(self) -> Dict[str, Any]:
        """
        Create workflow definition in watsonx Orchestrate.
        
        Returns:
            Dict containing workflow creation result
        """
        workflow_definition = {
            "name": "Legacy Code Modernization",
            "description": "Automated legacy code modernization pipeline with three agents",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "analyze",
                    "name": "Code Analysis",
                    "agent": "code_analyzer",
                    "description": "Analyze legacy code structure and dependencies",
                    "inputs": ["legacy_code_path", "language"],
                    "outputs": ["analysis_report"],
                    "timeout": 120,
                    "retry_policy": {
                        "max_attempts": 3,
                        "delay": 5
                    }
                },
                {
                    "id": "document",
                    "name": "Documentation Generation",
                    "agent": "documentation_agent",
                    "description": "Generate comprehensive documentation",
                    "inputs": ["analysis_report"],
                    "outputs": ["documentation"],
                    "depends_on": ["analyze"],
                    "timeout": 180,
                    "retry_policy": {
                        "max_attempts": 3,
                        "delay": 5
                    }
                },
                {
                    "id": "refactor",
                    "name": "Code Refactoring",
                    "agent": "refactoring_agent",
                    "description": "Modernize code and generate tests",
                    "inputs": ["legacy_code_path", "analysis_report", "documentation"],
                    "outputs": ["modernized_code", "tests", "test_results"],
                    "depends_on": ["analyze", "document"],
                    "timeout": 300,
                    "retry_policy": {
                        "max_attempts": 3,
                        "delay": 5
                    }
                }
            ],
            "error_handling": {
                "on_failure": "continue",
                "collect_partial_results": True
            }
        }
        
        result = self.watsonx_client.create_workflow(workflow_definition)
        
        if result.get("success"):
            self.workflow_id = result.get("workflow_id")
            logger.info(f"Workflow created: {self.workflow_id}")
        
        return result
    
    def execute_watsonx_workflow(
        self,
        legacy_code_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute workflow via watsonx Orchestrate.
        
        Args:
            legacy_code_path: Path to legacy code
            language: Programming language
        
        Returns:
            Execution result dict
        """
        if not self.workflow_id:
            logger.info("Creating workflow...")
            workflow_result = self.create_watsonx_workflow()
            if not workflow_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to create workflow"
                }
        
        inputs = {
            "legacy_code_path": legacy_code_path,
            "language": language
        }
        
        result = self.watsonx_client.execute_workflow(self.workflow_id, inputs)
        
        if result.get("success"):
            self.execution_id = result.get("execution_id")
            logger.info(f"Workflow execution started: {self.execution_id}")
        
        return result
    
    def get_execution_status(self) -> Dict[str, Any]:
        """
        Get status of current workflow execution.
        
        Returns:
            Status dict
        """
        if not self.execution_id:
            return {
                "success": False,
                "error": "No active execution"
            }
        
        return self.watsonx_client.get_execution_status(self.execution_id)
    
    def get_pipeline_summary(self, results: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of pipeline results.
        
        Args:
            results: Pipeline results dict
        
        Returns:
            Formatted summary string
        """
        summary = []
        summary.append("=" * 60)
        summary.append("LEGACY CODE MODERNIZATION PIPELINE SUMMARY")
        summary.append("=" * 60)
        summary.append("")
        
        # Overall status
        status = "[SUCCESS]" if results.get("success") else "[FAILED]"
        summary.append(f"Status: {status}")
        summary.append(f"Execution ID: {results.get('execution_id')}")
        summary.append("")
        
        # Metadata
        metadata = results.get("metadata", {})
        summary.append("Execution Details:")
        summary.append(f"  Input: {metadata.get('input_path')}")
        summary.append(f"  Language: {metadata.get('language', 'auto-detected')}")
        summary.append(f"  Start Time: {metadata.get('start_time')}")
        summary.append(f"  End Time: {metadata.get('end_time')}")
        if 'elapsed_time' in metadata:
            summary.append(f"  Duration: {metadata['elapsed_time']:.2f}s")
        summary.append("")
        
        # Agent results
        agent_results = results.get("results", {})
        summary.append("Agent Results:")
        
        for agent_name in ["analysis", "documentation", "refactoring"]:
            if agent_name in agent_results:
                agent_result = agent_results[agent_name]
                status = "[OK]" if agent_result.get("success") else "[FAIL]"
                summary.append(f"  {status} {agent_name.title()}")
                if agent_result.get("output_path"):
                    summary.append(f"      Output: {agent_result['output_path']}")
            else:
                summary.append(f"  - {agent_name.title()} (not executed)")
        
        summary.append("")
        
        # Errors
        errors = results.get("errors", [])
        if errors:
            summary.append("Errors:")
            for error in errors:
                summary.append(f"  [FAIL] {error.get('agent')}: {error.get('error')}")
            summary.append("")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)


# Made with Bob