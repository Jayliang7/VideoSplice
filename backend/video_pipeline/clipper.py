from __future__ import annotations

"""video_pipeline.clipper
-------------------------
Cuts the source video into clips whose *boundaries are defined purely by the
frame–cluster assignments* produced in :pyfunc:`video_pipeline.cluster_frames`.

Changes in this revision
~~~~~~~~~~~~~~~~~~~~~~~~
* **MoviePy v2 compatibility** – wraps the call to ``subclip`` so the code works
  with either MoviePy ≤1 (``.subclip``) or the upcoming MoviePy 2 (``.subclipped``).
* Rest of the logic (240‑second cap, JSON manifest, etc.) is unchanged.
"""

from pathlib import Path
from typing import Dict, List, Any

import json
import math
import logging

from moviepy.video.io.VideoFileClip import VideoFileClip

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _subclip_compat(clip: VideoFileClip, start: float, end: float):  # noqa: D401
    """Return a video segment using the appropriate MoviePy API.

    * MoviePy ≤1.x exposes ``VideoClip.subclip``.
    * MoviePy 2.x (alpha) renamed it to ``VideoClip.subclipped``.
    """

    if hasattr(clip, "subclip"):
        return clip.subclip(start, end)
    return clip.subclipped(start, end)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(
    *,
    frames: List[Dict[str, Any]],
    clusters: Dict[str, int],
    video_path: Path,
    run_dir: Path,
    max_clip_seconds: int = 240,
) -> List[Dict[str, Any]]:
    """Generate clips based on contiguous cluster blocks (≤240 s each)."""

    # ---------------------------------------------------------------------
    # Build a timeline sorted by original frame index
    # ---------------------------------------------------------------------
    df = sorted(frames, key=lambda f: f["index"])  # chronological order

    if not df:
        return []

    clip_blocks: List[tuple[int, float, float]] = []  # (cluster_id, start, end)

    current_cluster = clusters[df[0]["path"]]
    block_start = df[0]["timestamp"]
    last_ts = block_start

    for frame in df[1:]:
        ts = frame["timestamp"]
        cid = clusters[frame["path"]]
        if cid != current_cluster:
            clip_blocks.append((current_cluster, block_start, last_ts))
            current_cluster = cid
            block_start = ts
        last_ts = ts

    clip_blocks.append((current_cluster, block_start, last_ts))

    # ---------------------------------------------------------------------
    # Write clips to disk (respect 240‑s cap)
    # ---------------------------------------------------------------------
    clips_dir = run_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clips_meta: List[Dict[str, Any]] = []

    with VideoFileClip(str(video_path)) as video:
        for seq, (cid, start, end) in enumerate(clip_blocks):
            duration = end - start
            n_chunks = max(1, math.ceil(duration / max_clip_seconds))
            chunk_len = min(duration, max_clip_seconds)

            for chunk_idx in range(n_chunks):
                chunk_start = start + chunk_idx * chunk_len
                chunk_end = min(chunk_start + chunk_len, end)

                out_name = f"clip_{seq:03d}_{chunk_idx}.mp4"
                out_path = clips_dir / out_name

                logger.info(
                    "Writing clip %s (cluster=%d, %.2f–%.2f s)",
                    out_name,
                    cid,
                    chunk_start,
                    chunk_end,
                )

                (
                    _subclip_compat(video, chunk_start, chunk_end)
                    .write_videofile(
                        str(out_path),
                        codec="libx264",
                        audio_codec="aac",
                        temp_audiofile=str(out_path.with_suffix(".temp.aac")),
                        remove_temp=True,
                        logger=None,
                    )
                )

                clips_meta.append(
                    {
                        "path": str(out_path.relative_to(run_dir)),
                        "start": float(chunk_start),
                        "end": float(chunk_end),
                        "cluster_id": int(cid),
                    }
                )

    (run_dir / "clips.json").write_text(json.dumps(clips_meta, indent=2))
    return clips_meta
