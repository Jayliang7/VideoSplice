"""
video_io.py
===========

Thin wrapper around OpenCV (`cv2`) that extracts *basic, immutable* properties
from any video file:

• frame rate (fps)        • total frame count
• width & height (pixels) • calculated duration (seconds)

It deliberately **does not** write anything to disk or alter the source file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import cv2


# --------------------------------------------------------------------------- #
# 📦 Public surface
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class VideoProps:
    """Immutable container for video properties."""
    path: Path
    duration: float      # seconds
    fps: float
    frame_count: int
    width: int
    height: int


#: OpenCV sometimes reports fps as 0 for variable-frame-rate files.
#: When that happens we substitute this fallback to avoid ZeroDivision.
_FPS_FALLBACK: Final[float] = 30.0


def get_video_props(src: str | Path) -> VideoProps:
    """
    Inspect *src* and return a :class:`VideoProps`.

    Parameters
    ----------
    src : str | Path
        Path to a readable video file.

    Raises
    ------
    FileNotFoundError
        If *src* does not exist.
    RuntimeError
        If OpenCV cannot open the video container.
    """
    path = Path(src).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {path}")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV failed to open video: {path}")

    # --- gather raw numbers --------------------------------------------------
    fps         = cap.get(cv2.CAP_PROP_FPS)          or 0.0   # guard None
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()   # always free resources ASAP

    # --- sanitize values -----------------------------------------------------
    if fps < 1e-3:   # treat near-zero as invalid
        fps = _FPS_FALLBACK

    duration = frame_count / fps if frame_count else 0.0

    return VideoProps(
        path=path,
        duration=duration,
        fps=fps,
        frame_count=frame_count,
        width=width,
        height=height,
    )
