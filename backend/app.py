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

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# ---------------------------------------------------------------------------
# App setup & CORS
# ---------------------------------------------------------------------------

app = FastAPI(title="VideoSplice API", version="0.1.0")

origins = [
    "https://videosplicesite.onrender.com",   # your static‐site URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "ok"}

@app.post("/api/upload", response_model=dict[str, str])
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Receive a video file and kick off pipeline processing in background."""

    job_id = str(uuid4())
    temp_path = UPLOAD_DIR / f"{job_id}_{file.filename}"

    # Stream upload to disk
    with temp_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    JOBS[job_id] = {"state": "processing", "run_dir": None, "error": None}
    background_tasks.add_task(_process_video, job_id, temp_path)

    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    """Return processing state: processing | done | error."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, detail="job not found")
    return {"state": job["state"], "error": job["error"]}


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

    from video_pipeline.pipeline import run  # local import to avoid startup cost

    try:
        # use job_id as a prefix so each run dir is unique and traceable
        run_dir = run(video_path, prefix=job_id)
        JOBS[job_id].update(state="done", run_dir=run_dir)
    except Exception as exc:  # pragma: no cover – broad for MVP
        JOBS[job_id].update(state="error", error=str(exc))
        raise
