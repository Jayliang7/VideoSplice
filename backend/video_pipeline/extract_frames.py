"""
extract_frames.py
=================

Reads a video and saves *exactly* FRAME_RATE still-images per second into:

    <run_dir>/frames/frame_<000001>.jpg

Returns        : list[dict]  (timestamp, index, path)
Writes nothing : outside <run_dir>/frames/
"""

from __future__ import annotations

import math
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict

from video_pipeline import config
from video_pipeline.video_io import get_video_props

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def run(video_path: str | Path, run_dir: Path) -> List[Dict]:
    """
    Extract frames at *config.FRAME_RATE* and return metadata.

    Parameters
    ----------
    video_path : str | Path
        Source video.
    run_dir : Path
        The unique run directory created by `config.new_run_dir()`.

    Returns
    -------
    List[Dict]
        [{'timestamp': float, 'index': int, 'path': Path}, ...]
    """
    props = get_video_props(video_path)

    frames_dir = run_dir / config.FRAMES_SUBDIR
    frames_dir.mkdir(exist_ok=True)

    step = max(int(round(props.fps / config.FRAME_RATE)), 1)  # frames to skip
    cap = cv2.VideoCapture(str(props.path))

    extracted = []
    frame_idx = 0
    saved_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % step == 0:
            timestamp = frame_idx / props.fps
            filename = f"frame_{saved_idx:06d}.jpg"
            frame_path = frames_dir / filename
            cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

            extracted.append(
                {
                    "timestamp": timestamp,
                    "index": saved_idx,
                    "path": frame_path.relative_to(run_dir).as_posix(),
                }
            )
            saved_idx += 1

        frame_idx += 1

    cap.release()
    return extracted
