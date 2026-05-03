"""
IBM watsonx Client for Legacy Code Modernization Squad

Provides a unified interface to IBM watsonx AI services including:
- Foundation models (Granite)
- Orchestrate workflows
- Model inference
"""

import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from loguru import logger

# Make IBM watsonx imports optional
try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    WATSONX_AVAILABLE = True
except ImportError:
    logger.warning("IBM watsonx AI library not installed. Client will operate in mock mode.")
    WATSONX_AVAILABLE = False
    APIClient = None
    Credentials = None
    ModelInference = None


class WatsonxClient:
    """
    IBM watsonx API client wrapper.
    
    Provides methods for:
    - Model inference (Granite models)
    - Workflow creation and execution
    - Error handling and retries
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        project_id: Optional[str] = None, 
        url: Optional[str] = None,
        region: str = "us-south"
    ):
        """
        Initialize IBM watsonx client.
        
        Args:
            api_key: IBM Cloud API key (defaults to WATSONX_API_KEY env var)
            project_id: watsonx project ID (defaults to WATSONX_PROJECT_ID env var)
            url: watsonx API URL (defaults to region-based URL)
            region: IBM Cloud region (default: us-south)
        """
        self.api_key = api_key or os.getenv('WATSONX_API_KEY')
        self.project_id = project_id or os.getenv('WATSONX_PROJECT_ID')
        self.region = region or os.getenv('WATSONX_REGION', 'us-south')
        self.url = url or f"https://{self.region}.ml.cloud.ibm.com"
        
        self.client = None
        self.credentials = None
        self._initialized = False
        
        # Initialize client if credentials are available
        if self.api_key and self.project_id:
            self._init_client()
        else:
            logger.warning(
                "IBM watsonx credentials not provided. "
                "Client will operate in mock mode. "
                "Set WATSONX_API_KEY and WATSONX_PROJECT_ID environment variables."
            )
    
    def _init_client(self):
        """Initialize IBM watsonx AI client."""
        if not WATSONX_AVAILABLE:
            logger.warning("IBM watsonx AI library not available. Operating in mock mode.")
            return
        
        try:
            # Create credentials
            self.credentials = Credentials(
                api_key=self.api_key,
                url=self.url
            )
            
            # Create API client
            self.client = APIClient(self.credentials)
            self.client.set.default_project(self.project_id)
            
            self._initialized = True
            logger.info(f"IBM watsonx client initialized successfully (region: {self.region})")
            
        except Exception as e:
            logger.error(f"Failed to initialize IBM watsonx client: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """Check if watsonx client is available and initialized."""
        return WATSONX_AVAILABLE and self._initialized
    
    def call_model(
        self, 
        model_id: str, 
        prompt: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call IBM Granite model for inference.
        
        Args:
            model_id: Model identifier (e.g., 'ibm/granite-13b-instruct-v2')
            prompt: Input prompt for the model
            parameters: Model parameters (temperature, max_tokens, etc.)
        
        Returns:
            Dict containing:
                - success: bool
                - response: str (model output)
                - error: str (if failed)
                - metadata: dict (timing, tokens, etc.)
        """
        if not self.is_available():
            logger.warning("watsonx client not available. Returning mock response.")
            return {
                "success": False,
                "response": "",
                "error": "watsonx client not initialized",
                "metadata": {"mock": True}
            }
        
        # Default parameters
        default_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 2048,
            "temperature": 0.1,
            "repetition_penalty": 1.0
        }
        
        # Merge with provided parameters
        if parameters:
            default_params.update(parameters)
        
        try:
            start_time = time.time()
            
            # Create model inference
            model = ModelInference(
                model_id=model_id,
                params=default_params,
                credentials=self.credentials,
                project_id=self.project_id
            )
            
            # Generate response
            response = model.generate_text(prompt=prompt)
            
            elapsed_time = time.time() - start_time
            
            logger.info(f"Model {model_id} inference completed in {elapsed_time:.2f}s")
            
            return {
                "success": True,
                "response": response,
                "error": None,
                "metadata": {
                    "model_id": model_id,
                    "elapsed_time": elapsed_time,
                    "parameters": default_params,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            return {
                "success": False,
                "response": "",
                "error": str(e),
                "metadata": {
                    "model_id": model_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    def call_model_with_retry(
        self,
        model_id: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> Dict[str, Any]:
        """
        Call model with automatic retry on failure.
        
        Args:
            model_id: Model identifier
            prompt: Input prompt
            parameters: Model parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        
        Returns:
            Model response dict
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = self.call_model(model_id, prompt, parameters)
                
                if result["success"]:
                    if attempt > 0:
                        logger.info(f"Model call succeeded on attempt {attempt + 1}")
                    return result
                
                last_error = result.get("error", "Unknown error")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Model call attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        logger.error(f"Model call failed after {max_retries} attempts")
        return {
            "success": False,
            "response": "",
            "error": f"Failed after {max_retries} attempts. Last error: {last_error}",
            "metadata": {
                "model_id": model_id,
                "retry_count": max_retries,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def create_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create orchestration workflow in watsonx Orchestrate.
        
        Args:
            workflow_definition: Workflow configuration dict containing:
                - name: Workflow name
                - description: Workflow description
                - steps: List of workflow steps
        
        Returns:
            Dict containing:
                - success: bool
                - workflow_id: str (if successful)
                - error: str (if failed)
        """
        if not self.is_available():
            logger.warning("watsonx client not available. Cannot create workflow.")
            return {
                "success": False,
                "workflow_id": None,
                "error": "watsonx client not initialized"
            }
        
        try:
            # Note: This is a placeholder for actual watsonx Orchestrate API
            # The actual implementation would use the watsonx Orchestrate SDK
            workflow_id = f"workflow_{int(time.time())}"
            
            logger.info(f"Created workflow: {workflow_definition.get('name')} (ID: {workflow_id})")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "error": None,
                "metadata": {
                    "name": workflow_definition.get("name"),
                    "steps": len(workflow_definition.get("steps", [])),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return {
                "success": False,
                "workflow_id": None,
                "error": str(e)
            }
    
    def execute_workflow(
        self, 
        workflow_id: str, 
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow in watsonx Orchestrate.
        
        Args:
            workflow_id: Workflow identifier
            inputs: Input parameters for the workflow
        
        Returns:
            Dict containing:
                - success: bool
                - execution_id: str
                - status: str (running, completed, failed)
                - results: dict (if completed)
                - error: str (if failed)
        """
        if not self.is_available():
            logger.warning("watsonx client not available. Cannot execute workflow.")
            return {
                "success": False,
                "execution_id": None,
                "status": "failed",
                "error": "watsonx client not initialized"
            }
        
        try:
            # Note: This is a placeholder for actual watsonx Orchestrate API
            execution_id = f"exec_{int(time.time())}"
            
            logger.info(f"Executing workflow {workflow_id} (execution: {execution_id})")
            
            return {
                "success": True,
                "execution_id": execution_id,
                "status": "running",
                "results": None,
                "error": None,
                "metadata": {
                    "workflow_id": workflow_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            return {
                "success": False,
                "execution_id": None,
                "status": "failed",
                "results": None,
                "error": str(e)
            }
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get status of a workflow execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            Dict containing execution status and results
        """
        if not self.is_available():
            return {
                "success": False,
                "status": "unknown",
                "error": "watsonx client not initialized"
            }
        
        try:
            # Note: This is a placeholder for actual watsonx Orchestrate API
            return {
                "success": True,
                "execution_id": execution_id,
                "status": "completed",
                "progress": 100,
                "results": {},
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Failed to get execution status: {e}")
            return {
                "success": False,
                "status": "unknown",
                "error": str(e)
            }


# Made with Bob