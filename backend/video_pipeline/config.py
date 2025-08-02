"""
config.py
=========

Centralised, *single source of truth* for every tweakable parameter the
VideoSplice pipeline needs.  Importing from here prevents "magic numbers" from
being hard-wired across modules and makes future tuning a one-file change.

This file is intentionally **side-effect–free** except for ensuring the
`backend/runs/` directory exists.  That tiny side-effect is acceptable because
every module will count on that folder being present during a request.
"""

from __future__ import annotations  # allows future type-hint syntax on <Py3.11
import os
import uuid
import gc
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 📂 DIRECTORY LAYOUT – all runtime artefacts live under backend/runs/
# --------------------------------------------------------------------------- #

PACKAGE_DIR: Path = Path(__file__).resolve().parent        # …/backend/video_pipeline
PROJECT_ROOT: Path = PACKAGE_DIR.parent                    # …/backend
RUNS_ROOT: Path = PROJECT_ROOT / "runs"                    # …/backend/runs
RUNS_ROOT.mkdir(exist_ok=True)                             # create once

#: Sub-folder names, kept as constants so every module spells them identically
FRAMES_SUBDIR = "frames"
CLIPS_SUBDIR = "clips"

# --------------------------------------------------------------------------- #
# 🧠 MEMORY OPTIMIZATION FOR RENDER FREE PLAN (512MB LIMIT)
# --------------------------------------------------------------------------- #

#: Maximum memory usage allowed (Render free plan: 512MB)
MAX_MEMORY_MB = 450  # Leave 62MB buffer for safety
MAX_MEMORY_BYTES = MAX_MEMORY_MB * 1024 * 1024

#: Memory warning threshold (80% of max)
MEMORY_WARNING_THRESHOLD = 0.8
MEMORY_CRITICAL_THRESHOLD = 0.9

#: Maximum video file size (50MB to leave room for processing)
MAX_VIDEO_SIZE_MB = 50
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024

#: Batch processing size for memory efficiency
BATCH_SIZE = 3  # Process 3 frames at a time instead of all at once

# --------------------------------------------------------------------------- #
# ✨ CORE PROCESSING PARAMETERS – OPTIMIZED FOR MEMORY
# --------------------------------------------------------------------------- #

#: How many *video frames per second* to sample during extraction.
#: Reduced from 1 fps to 0.5 fps for memory efficiency
FRAME_RATE: float = 0.5  # Extract 1 frame every 2 seconds

#: Maximum duration of each output clip in **seconds**. Reduced for memory efficiency
CLIP_MAX_LENGTH: int = 120  # Reduced from 240s to 120s (2 minutes)

#: Identifier of the Hugging Face model we'll call for embeddings.
#: Must match the model actually deployed behind your paid endpoint.
EMBEDDING_MODEL: str = "openai/clip-vit-base-patch32"

# --------------------------------------------------------------------------- #
# 🛠️  MEMORY MONITORING AND OPTIMIZATION
# --------------------------------------------------------------------------- #

# Check if we're on Render and disable memory monitoring
IS_RENDER = os.getenv("RENDER", "false").lower() == "true"

try:
    import psutil
    PSUTIL_AVAILABLE = True and not IS_RENDER  # Disable on Render
except ImportError:
    PSUTIL_AVAILABLE = False

if IS_RENDER:
    logger.warning("Running on Render - memory monitoring disabled due to container reporting issues")
elif not PSUTIL_AVAILABLE:
    logger.warning("psutil not available - memory monitoring disabled")

def get_memory_usage() -> dict:
    """Get current memory usage statistics."""
    if not PSUTIL_AVAILABLE:
        return {"available": False, "percent": 0, "used_mb": 0, "total_mb": 0}
    
    try:
        memory = psutil.virtual_memory()
        used_mb = memory.used / (1024 * 1024)
        total_mb = memory.total / (1024 * 1024)
        
        # Sanity check for impossibly high values (common on Render)
        if used_mb > 10000 or total_mb > 10000:
            logger.warning(f"Memory reporting error detected: {used_mb:.1f}MB used, {total_mb:.1f}MB total")
            return {"available": False, "percent": 0, "used_mb": 0, "total_mb": 0}
        
        return {
            "available": True,
            "percent": memory.percent,
            "used_mb": used_mb,
            "total_mb": total_mb,
            "available_mb": memory.available / (1024 * 1024)
        }
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return {"available": False, "percent": 0, "used_mb": 0, "total_mb": 0}

def check_memory_limit() -> bool:
    """Check if memory usage is within limits."""
    memory_info = get_memory_usage()
    
    if not memory_info["available"]:
        return True  # Assume OK if we can't check
    
    # Check against our configured limit
    if memory_info["used_mb"] > MAX_MEMORY_MB:
        logger.error(f"Memory limit exceeded: {memory_info['used_mb']:.1f}MB > {MAX_MEMORY_MB}MB")
        return False
    
    # Check percentage thresholds
    if memory_info["percent"] > (MEMORY_CRITICAL_THRESHOLD * 100):
        logger.error(f"Critical memory usage: {memory_info['percent']:.1f}%")
        return False
    
    if memory_info["percent"] > (MEMORY_WARNING_THRESHOLD * 100):
        logger.warning(f"High memory usage: {memory_info['percent']:.1f}%")
    
    return True

def force_memory_cleanup():
    """Force garbage collection and memory cleanup."""
    logger.info("Forcing memory cleanup...")
    
    # Force garbage collection
    collected = gc.collect()
    logger.info(f"Garbage collection freed {collected} objects")
    
    # Get memory usage after cleanup
    memory_info = get_memory_usage()
    if memory_info["available"]:
        logger.info(f"Memory after cleanup: {memory_info['used_mb']:.1f}MB ({memory_info['percent']:.1f}%)")

def check_video_size(file_size_bytes: int) -> bool:
    """Check if video file size is within limits."""
    if file_size_bytes > MAX_VIDEO_SIZE_BYTES:
        logger.error(f"Video file too large: {file_size_bytes / (1024*1024):.1f}MB > {MAX_VIDEO_SIZE_MB}MB")
        return False
    return True

class MemoryLimitExceededError(Exception):
    """Raised when memory usage exceeds the plan limit."""
    def __init__(self, current_mb: float, limit_mb: float):
        self.current_mb = current_mb
        self.limit_mb = limit_mb
        super().__init__(f"Memory limit exceeded: {current_mb:.1f}MB > {limit_mb}MB (Render free plan limit)")

def assert_memory_available():
    """Assert that memory is available for processing."""
    memory_info = get_memory_usage()
    
    if not memory_info["available"]:
        return  # Can't check, assume OK
    
    if memory_info["used_mb"] > MAX_MEMORY_MB:
        raise MemoryLimitExceededError(memory_info["used_mb"], MAX_MEMORY_MB)
    
    if memory_info["percent"] > (MEMORY_CRITICAL_THRESHOLD * 100):
        raise MemoryLimitExceededError(memory_info["used_mb"], MAX_MEMORY_MB)

# --------------------------------------------------------------------------- #
# ⚙️  HUGGING FACE INFERENCE ENDPOINT DETAILS
# --------------------------------------------------------------------------- #

# ...
REPO_ROOT: Path = PROJECT_ROOT.parent                 # D:\Projects\videoSplice
dotenv_path = REPO_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path, override=False)  # populate os.environ

#: Bearer token pulled from .env  (raises if absent)
HF_API_TOKEN: str | None = os.getenv("HF_API_TOKEN")
if HF_API_TOKEN is None:
    print("WARNING: HF_API_TOKEN not set. Some features may not work.")
    # Don't raise immediately - let the pipeline handle it gracefully

#: Full endpoint URL, with a sensible fallback to the public feature-extraction route
HF_API_URL: str = os.getenv(
    "HF_API_URL",
    f"https://api-inference.huggingface.co/pipeline/feature-extraction/{EMBEDDING_MODEL}",
)

# --------------------------------------------------------------------------- #
# 🛠️  FFMPEG BEHAVIOUR
# --------------------------------------------------------------------------- #

#: Codec flag sent to FFmpeg when cutting clips. `"copy"` ⇒ *stream copy*
#: (no re-encode, fastest, lossless). If it fails on exotic containers,
#: caller can fall back to e.g. `"libx264"`.
FFMPEG_COPY_CODEC: str = "copy"

def new_run_dir(prefix: str | None = None) -> Path:
    """
    Create **one unique directory** for a single pipeline execution and return
    the `Path` object.

    Layout created:

        backend/runs/<prefix_?>YYYYMMDD_HHMMSS_<8charUUID>/
        ├── frames/
        └── clips/

    Sub-directories ensure other modules can blindly write
    `run_dir / FRAMES_SUBDIR / "frame_0001.jpg"` without checking.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")  # sortable
    uid8 = uuid.uuid4().hex[:8]                               # collision-proof
    name = f"{prefix+'_' if prefix else ''}{timestamp}_{uid8}"
    run_dir = RUNS_ROOT / name
    run_dir.mkdir(parents=True, exist_ok=False)               # crash if clash

    # Pre-create folders used by later steps
    (run_dir / FRAMES_SUBDIR).mkdir()
    (run_dir / CLIPS_SUBDIR).mkdir()
    return run_dir
