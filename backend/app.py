from __future__ import annotations

"""FastAPI entry‑point for the VideoSplice backend.

Exposes three minimal endpoints so the bare‑bones React front‑end can:

1. **POST /api/upload**   – Upload a video and spawn a background job.
2. **GET  /api/status/{job_id}** – Poll for processing state.
3. **GET  /api/download/{job_id}** – Stream a ZIP archive with the clips &
   metadata once processing finishes.

The implementation keeps state in an in‑memory dict *JOBS*. For production you
would swap this for Redis / database + a real task queue, but this is enough
for a single‑node MVP.
"""

from pathlib import Path
from uuid import uuid4
import io
import json
import os
import shutil
import zipfile

import logging
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup & CORS
# ---------------------------------------------------------------------------

app = FastAPI(title="VideoSplice API", version="0.1.0")

origins = [
    "https://videosplicesite.onrender.com",   # your static‐site URL
    "https://videosplice.onrender.com",       # your API URL
    "http://localhost:5173",                  # local development
    "http://localhost:3000",                  # alternative local dev port
    "http://localhost:8000",                  # local backend
    "*",  # Allow all origins for debugging - remove in production
]

# Add CORS middleware with more explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Add a simple middleware to log requests for debugging
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# ---------------------------------------------------------------------------
# Crude in‑memory job registry: {job_id: {state, run_dir, error}}
# ---------------------------------------------------------------------------

JOBS: dict[str, dict] = {}

DATA_DIR = Path(__file__).resolve().parent / ".." / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    return {"status": "ok", "message": "VideoSplice API is running"}

@app.get("/health", include_in_schema=False)
def health_check():
    """Health check endpoint for Render."""
    from fastapi.responses import JSONResponse
    response_data = {"status": "healthy", "jobs_count": len(JOBS)}
    response = JSONResponse(content=response_data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.options("/api/status/{job_id}")
def status_options(job_id: str):
    """Handle OPTIONS requests for CORS preflight."""
    return {"message": "OK"}

@app.post("/api/upload", response_model=dict[str, str])
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Receive a video file and kick off pipeline processing in background."""

    logger.info(f"Received upload request for file: {file.filename}")
    
    job_id = str(uuid4())
    temp_path = UPLOAD_DIR / f"{job_id}_{file.filename}"

    # Stream upload to disk
    with temp_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    logger.info(f"File saved to {temp_path}, job_id: {job_id}")
    
    JOBS[job_id] = {"state": "processing", "run_dir": None, "error": None}
    background_tasks.add_task(_process_video, job_id, temp_path)

    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    """Return processing state: processing | done | error."""
    try:
        job = JOBS.get(job_id)
        if not job:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(404, detail="job not found")
        
        # Only log every 10th request to reduce log spam
        if job_id not in getattr(get_status, '_request_count', {}):
            get_status._request_count = {}
        get_status._request_count[job_id] = get_status._request_count.get(job_id, 0) + 1
        
        if get_status._request_count[job_id] % 10 == 0:
            logger.info(f"Job {job_id} state: {job['state']} (request #{get_status._request_count[job_id]})")
        
        # Add more detailed error information
        response_data = {"state": job["state"]}
        if job.get("error"):
            response_data["error"] = job["error"]
        if job.get("progress"):
            response_data["progress"] = job["progress"]
        
        # Add explicit CORS headers
        from fastapi.responses import JSONResponse
        response = JSONResponse(content=response_data)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error in status endpoint for job {job_id}: {str(e)}")
        raise HTTPException(500, detail=f"Internal server error: {str(e)}")


@app.get("/api/download/{job_id}")
def download_zip(job_id: str):
    """Stream ZIP archive containing clips + metadata for a finished job."""

    job = JOBS.get(job_id)
    if not job or job["state"] != "done":
        raise HTTPException(404, detail="job not ready")

    run_dir: Path = job["run_dir"]
    if not run_dir.exists():
        raise HTTPException(500, detail="run directory missing on server")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(run_dir):
            for fname in files:
                fp = Path(root) / fname
                zf.write(fp, fp.relative_to(run_dir))
    buffer.seek(0)

    headers = {"Content-Disposition": f"attachment; filename={job_id}.zip"}
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

def _process_video(job_id: str, video_path: Path):
    """Run the heavy pipeline in the background thread."""

    logger.info(f"Starting video processing for job {job_id}, video: {video_path}")
    
    try:
        # Check if video file exists
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Check file size
        file_size = video_path.stat().st_size
        if file_size == 0:
            raise ValueError("Video file is empty")
        
        logger.info(f"Video file size: {file_size} bytes")
        
        # Update job with progress
        JOBS[job_id].update(progress="Initializing pipeline...")
        
        from backend.video_pipeline.pipeline import run  # local import to avoid startup cost

        # use job_id as a prefix so each run dir is unique and traceable
        JOBS[job_id].update(progress="Running video analysis...")
        run_dir = run(video_path, prefix=job_id)
        
        JOBS[job_id].update(state="done", run_dir=run_dir, progress="Processing complete")
        logger.info(f"Video processing completed for job {job_id}, run_dir: {run_dir}")
        
    except Exception as exc:  # pragma: no cover – broad for MVP
        error_msg = f"Video processing failed for job {job_id}: {str(exc)}"
        logger.error(error_msg)
        JOBS[job_id].update(state="error", error=str(exc), progress="Processing failed")
        # Don't re-raise to prevent the background task from failing
