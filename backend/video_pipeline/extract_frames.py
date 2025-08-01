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
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict

from backend.video_pipeline import config
from backend.video_pipeline.video_io import get_video_props

# Configure logging
logger = logging.getLogger(__name__)

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
    logger.info(f"Starting frame extraction from {video_path}")
    
    try:
        # Get video properties
        logger.info("Analyzing video properties")
        props = get_video_props(video_path)
        logger.info(f"Video properties: {props.fps} FPS, {props.duration}s duration")

        # Create frames directory
        frames_dir = run_dir / config.FRAMES_SUBDIR
        frames_dir.mkdir(exist_ok=True)
        logger.info(f"Created frames directory: {frames_dir}")

        # Calculate frame step
        step = max(int(round(props.fps / config.FRAME_RATE)), 1)  # frames to skip
        logger.info(f"Frame extraction step: {step} (extracting every {step}th frame)")

        # Open video capture
        logger.info("Opening video capture")
        cap = cv2.VideoCapture(str(props.path))
        
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video file: {video_path}")

        extracted = []
        frame_idx = 0
        saved_idx = 0

        logger.info("Starting frame extraction loop")
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.info(f"Reached end of video after {frame_idx} frames")
                break

            if frame_idx % step == 0:
                timestamp = frame_idx / props.fps
                filename = f"frame_{saved_idx:06d}.jpg"
                frame_path = frames_dir / filename
                
                # Save frame
                success = cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                if not success:
                    logger.error(f"Failed to save frame {saved_idx} to {frame_path}")
                    raise RuntimeError(f"Failed to save frame {saved_idx}")

                extracted.append(
                    {
                        "timestamp": timestamp,
                        "index": saved_idx,
                        "path": frame_path.relative_to(run_dir).as_posix(),
                    }
                )
                saved_idx += 1
                
                # Log progress every 10 frames
                if saved_idx % 10 == 0:
                    logger.info(f"Extracted {saved_idx} frames (processed {frame_idx} total frames)")

            frame_idx += 1

        cap.release()
        logger.info(f"Frame extraction complete: {len(extracted)} frames extracted")
        return extracted
        
    except Exception as e:
        logger.error(f"Frame extraction failed: {str(e)}")
        raise
