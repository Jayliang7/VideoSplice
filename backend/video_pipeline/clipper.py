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
    """Generate clips based on contiguous cluster blocks (≤240 s each)."""

    # ---------------------------------------------------------------------
    # Validate video file
    # ---------------------------------------------------------------------
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # ---------------------------------------------------------------------
    # Validate input - handle empty frames list
    # ---------------------------------------------------------------------
    if not frames:
        logger.warning("No frames available for clipping - video may be too short or frame extraction failed")
        # Create empty clips.json and return empty list
        clips_dir = run_dir / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "clips.json").write_text(json.dumps([], indent=2))
        return []

    # ---------------------------------------------------------------------
    # Validate clusters dictionary
    # ---------------------------------------------------------------------
    if not clusters:
        logger.warning("No clusters available for clipping - clustering may have failed")
        # Create empty clips.json and return empty list
        clips_dir = run_dir / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "clips.json").write_text(json.dumps([], indent=2))
        return []

    # ---------------------------------------------------------------------
    # Build a timeline sorted by original frame index
    # ---------------------------------------------------------------------
    df = sorted(frames, key=lambda f: f["index"])  # chronological order

    # Double-check that we have frames after sorting
    if not df:
        logger.warning("No frames available after sorting - video may be too short or frame extraction failed")
        clips_dir = run_dir / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "clips.json").write_text(json.dumps([], indent=2))
        return []

    # Validate that all frames have corresponding cluster assignments
    missing_clusters = [f["path"] for f in df if f["path"] not in clusters]
    if missing_clusters:
        logger.error(f"Missing cluster assignments for frames: {missing_clusters[:5]}...")
        raise ValueError(f"Missing cluster assignments for {len(missing_clusters)} frames")

    clip_blocks: List[tuple[int, float, float]] = []  # (cluster_id, start, end)

    # Now we can safely access df[0] since we've validated the list is not empty
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
            
            # Validate clip duration
            if duration <= 0:
                logger.warning(f"Skipping clip with invalid duration: {duration}s (start={start}, end={end})")
                continue
                
            n_chunks = max(1, math.ceil(duration / max_clip_seconds))
            chunk_len = min(duration, max_clip_seconds)

            for chunk_idx in range(n_chunks):
                chunk_start = start + chunk_idx * chunk_len
                chunk_end = min(chunk_start + chunk_len, end)
                
                # Validate chunk duration
                chunk_duration = chunk_end - chunk_start
                if chunk_duration <= 0:
                    logger.warning(f"Skipping chunk with invalid duration: {chunk_duration}s (start={chunk_start}, end={chunk_end})")
                    continue

                out_name = f"clip_{seq:03d}_{chunk_idx}.mp4"
                out_path = clips_dir / out_name

                logger.info(
                    "Writing clip %s (cluster=%d, %.2f–%.2f s)",
                    out_name,
                    cid,
                    chunk_start,
                    chunk_end,
                )

                try:
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
                except Exception as e:
                    logger.error(f"Failed to write clip {out_name}: {str(e)}")
                    # Continue with other clips instead of failing completely
                    continue

    (run_dir / "clips.json").write_text(json.dumps(clips_meta, indent=2))
    return clips_meta
