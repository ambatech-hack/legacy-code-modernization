"""
FastAPI REST API for Legacy Code Modernization Squad

Provides HTTP endpoints for:
- Triggering modernization workflows
- Checking job status
- Retrieving results
- Managing workflows
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from loguru import logger

from integrations.orchestrator import Orchestrator
from utils.file_handler import ensure_directory


# Pydantic models for request/response
class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModernizeRequest(BaseModel):
    """Request model for modernization."""
    legacy_code_path: str = Field(..., description="Path to legacy code file or directory")
    language: Optional[str] = Field(None, description="Programming language (auto-detected if not provided)")
    output_dir: Optional[str] = Field("output", description="Output directory for results")


class ModernizeResponse(BaseModel):
    """Response model for modernization request."""
    success: bool
    job_id: str
    message: str
    status: JobStatus
    created_at: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: JobStatus
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class JobResultsResponse(BaseModel):
    """Response model for job results."""
    job_id: str
    status: JobStatus
    success: bool
    results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    metadata: Dict[str, Any]


# Initialize FastAPI app
app = FastAPI(
    title="Legacy Code Modernization API",
    description="REST API for automated legacy code modernization using IBM watsonx",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for job tracking
jobs: Dict[str, Dict[str, Any]] = {}
orchestrator: Optional[Orchestrator] = None


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup."""
    global orchestrator
    try:
        orchestrator = Orchestrator()
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        orchestrator = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Legacy Code Modernization API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "modernize": "POST /modernize",
            "upload": "POST /upload",
            "status": "GET /status/{job_id}",
            "results": "GET /results/{job_id}",
            "jobs": "GET /jobs",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "orchestrator_available": orchestrator is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/modernize", response_model=ModernizeResponse)
async def modernize_code(
    request: ModernizeRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger legacy code modernization workflow.
    
    This endpoint accepts a path to legacy code and starts the modernization pipeline.
    The job runs asynchronously in the background.
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    # Validate input path
    if not os.path.exists(request.legacy_code_path):
        raise HTTPException(status_code=404, detail=f"Path not found: {request.legacy_code_path}")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    # Initialize job state
    jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "Job created, waiting to start",
        "created_at": created_at,
        "updated_at": created_at,
        "completed_at": None,
        "request": request.dict(),
        "results": None,
        "error": None
    }
    
    # Schedule background task
    background_tasks.add_task(
        run_modernization_pipeline,
        job_id,
        request.legacy_code_path,
        request.language,
        request.output_dir
    )
    
    logger.info(f"Created modernization job: {job_id}")
    
    return ModernizeResponse(
        success=True,
        job_id=job_id,
        message="Modernization job created successfully",
        status=JobStatus.PENDING,
        created_at=created_at
    )


@app.post("/upload")
async def upload_code(
    file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="Programming language")
):
    """
    Upload legacy code file and trigger modernization.
    
    This endpoint accepts a file upload, saves it, and starts the modernization pipeline.
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    # Create upload directory
    upload_dir = "uploads"
    ensure_directory(upload_dir)
    
    # Save uploaded file
    file_path = os.path.join(upload_dir, file.filename)
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Uploaded file saved: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create modernization request
    request = ModernizeRequest(
        legacy_code_path=file_path,
        language=language,
        output_dir="output"
    )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    # Initialize job state
    jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "File uploaded, job created",
        "created_at": created_at,
        "updated_at": created_at,
        "completed_at": None,
        "request": request.dict(),
        "results": None,
        "error": None
    }
    
    # Start pipeline in background
    asyncio.create_task(
        run_modernization_pipeline_async(
            job_id,
            file_path,
            language,
            "output"
        )
    )
    
    logger.info(f"Created modernization job from upload: {job_id}")
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "File uploaded and modernization job created",
        "status": JobStatus.PENDING,
        "filename": file.filename,
        "created_at": created_at
    }


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of a modernization job.
    
    Returns current status, progress, and any error messages.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    job = jobs[job_id]
    
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=job.get("message"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        completed_at=job.get("completed_at"),
        error=job.get("error")
    )


@app.get("/results/{job_id}", response_model=JobResultsResponse)
async def get_job_results(job_id: str):
    """
    Get results of a completed modernization job.
    
    Returns all outputs from the three agents.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    job = jobs[job_id]
    
    if job["status"] not in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed yet. Current status: {job['status']}"
        )
    
    results = job.get("results", {})
    
    return JobResultsResponse(
        job_id=job["job_id"],
        status=job["status"],
        success=results.get("success", False),
        results=results.get("results", {}),
        errors=results.get("errors", []),
        metadata=results.get("metadata", {})
    )


@app.get("/jobs")
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of jobs to return")
):
    """
    List all modernization jobs.
    
    Optionally filter by status and limit results.
    """
    job_list = list(jobs.values())
    
    # Filter by status if provided
    if status:
        job_list = [job for job in job_list if job["status"] == status]
    
    # Sort by creation time (newest first)
    job_list.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Limit results
    job_list = job_list[:limit]
    
    return {
        "total": len(job_list),
        "jobs": job_list
    }


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a running job.
    
    Note: This only marks the job as cancelled. The actual pipeline may continue.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    job = jobs[job_id]
    
    if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    job["status"] = JobStatus.CANCELLED
    job["updated_at"] = datetime.utcnow().isoformat()
    job["message"] = "Job cancelled by user"
    
    logger.info(f"Job cancelled: {job_id}")
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Job cancelled successfully"
    }


@app.get("/download/{job_id}/{file_type}")
async def download_result(job_id: str, file_type: str):
    """
    Download specific result file from a completed job.
    
    file_type can be: analysis, documentation, modernized_code, tests
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    job = jobs[job_id]
    
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job['status']}"
        )
    
    # Get output directory from job request
    output_dir = job["request"].get("output_dir", "output")
    
    # Map file types to paths
    file_paths = {
        "analysis": os.path.join(output_dir, "analysis", "analysis_report.json"),
        "documentation": os.path.join(output_dir, "documentation", "README.md"),
        "modernized_code": os.path.join(output_dir, "modernized"),
        "tests": os.path.join(output_dir, "modernized")
    }
    
    if file_type not in file_paths:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file_type}")
    
    file_path = file_paths[file_type]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    return FileResponse(file_path)


# Background task functions
def run_modernization_pipeline(
    job_id: str,
    legacy_code_path: str,
    language: Optional[str],
    output_dir: str
):
    """Run modernization pipeline in background."""
    try:
        # Update job status
        jobs[job_id]["status"] = JobStatus.RUNNING
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Pipeline started"
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Starting pipeline for job {job_id}")
        
        # Run pipeline
        results = orchestrator.run_pipeline(
            legacy_code_path=legacy_code_path,
            language=language,
            output_dir=output_dir
        )
        
        # Update job with results
        jobs[job_id]["results"] = results
        jobs[job_id]["status"] = JobStatus.COMPLETED if results.get("success") else JobStatus.FAILED
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Pipeline completed" if results.get("success") else "Pipeline failed"
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        
        if not results.get("success"):
            jobs[job_id]["error"] = results.get("errors", [])
        
        logger.info(f"Pipeline completed for job {job_id}: {jobs[job_id]['status']}")
        
    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {e}")
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["progress"] = 0
        jobs[job_id]["message"] = f"Pipeline error: {str(e)}"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()


async def run_modernization_pipeline_async(
    job_id: str,
    legacy_code_path: str,
    language: Optional[str],
    output_dir: str
):
    """Run modernization pipeline asynchronously."""
    await asyncio.to_thread(
        run_modernization_pipeline,
        job_id,
        legacy_code_path,
        language,
        output_dir
    )


# Made with Bob