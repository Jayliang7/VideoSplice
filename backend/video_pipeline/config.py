"""
config.py
=========

Centralised, *single source of truth* for every tweakable parameter the
VideoSplice pipeline needs.  Importing from here prevents “magic numbers” from
being hard-wired across modules and makes future tuning a one-file change.

This file is intentionally **side-effect–free** except for ensuring the
`backend/runs/` directory exists.  That tiny side-effect is acceptable because
every module will count on that folder being present during a request.
"""

from __future__ import annotations  # allows future type-hint syntax on <Py3.11
import os
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

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
# ✨ CORE PROCESSING PARAMETERS – change these to alter pipeline behaviour
# --------------------------------------------------------------------------- #

#: How many *video frames per second* to sample during extraction.
#: 1 fps keeps Hugging Face calls ≈60/min for a 1-minute clip.
FRAME_RATE: int = 1

#: Maximum duration of each output clip in **seconds**. 240 s = 4 min.
CLIP_MAX_LENGTH: int = 240

#: Identifier of the Hugging Face model we’ll call for embeddings.
#: Must match the model actually deployed behind your paid endpoint.
EMBEDDING_MODEL: str = "openai/clip-vit-base-patch32"

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
    raise RuntimeError(
        "HF_API_TOKEN not set. Add it to your .env or OS environment."
    )

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
