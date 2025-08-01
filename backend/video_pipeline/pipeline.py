"""
pipeline.py
===========

Single public function `run()` orchestrates the entire VideoSplice MVP flow:

    extract_frames
      → embed_frames (local CLIP)
      → cluster_frames (UMAP + HDBSCAN)
      → select_representative_frames
      → label_representative_frames (HF endpoint)
      → clipper (centre clips on reps)
      → metadata_writer
"""

from __future__ import annotations

from pathlib import Path
import dataclasses

from backend.video_pipeline import config
from backend.video_pipeline.video_io import get_video_props
from backend.video_pipeline.extract_frames import run as extract_frames
from backend.video_pipeline.embed_frames import run as embed_frames
from backend.video_pipeline.cluster_frames import run as cluster_frames
from backend.video_pipeline.select_representative_frames import run as choose_reps
from backend.video_pipeline.label_representative_frames import run as label_reps
from backend.video_pipeline.clipper import run as clipper
from backend.video_pipeline.metadata_writer import write as write_meta


def run(video_path: str | Path, *, prefix: str | None = None) -> Path:
    """
    Execute the full pipeline and return the run directory containing all outputs.

    Parameters
    ----------
    video_path : str | Path
        Path to the source video.
    prefix     : Optional prefix for the run directory name.

    Returns
    -------
    Path
        Absolute path to the run directory (ready for zipping or further use).
    """
    # ------------------------------------------------------------------ #
    # 0. unique workspace
    # ------------------------------------------------------------------ #
    run_dir = config.new_run_dir(prefix=prefix)

    # ------------------------------------------------------------------ #
    # 1. basic video properties
    # ------------------------------------------------------------------ #
    props = get_video_props(video_path)

    # ------------------------------------------------------------------ #
    # 2. frame extraction
    # ------------------------------------------------------------------ #
    frames = extract_frames(video_path, run_dir)

    # ------------------------------------------------------------------ #
    # 3. local CLIP embeddings
    # ------------------------------------------------------------------ #
    embedded_frames = embed_frames(frames, run_dir)

    # ------------------------------------------------------------------ #
    # 4. clustering via UMAP + HDBSCAN
    # ------------------------------------------------------------------ #
    clusters = cluster_frames(embedded_frames, props.duration, run_dir)

    # ------------------------------------------------------------------ #
    # 5. representative frame selection
    # ------------------------------------------------------------------ #
    representatives = choose_reps(embedded_frames, clusters, run_dir)

    # ------------------------------------------------------------------ #
    # 6. Hugging Face labeling of representatives
    # ------------------------------------------------------------------ #
    labeled_reps = label_reps(representatives, run_dir)

    # ------------------------------------------------------------------ #
    # 7. clip generation centred on reps
    # ------------------------------------------------------------------ #
    clips = clipper(
    frames=frames,
    clusters=clusters,
    video_path=video_path,
    run_dir=run_dir,
    )

    # ------------------------------------------------------------------ #
    # 8. write consolidated metadata
    # ------------------------------------------------------------------ #
    write_meta(
        run_dir,
        video_props=dataclasses.asdict(props),
        frame_rate=config.FRAME_RATE,
        embedding_model="openai/clip-vit-base-patch32",
        representatives=labeled_reps,  # includes labels
        clips=clips,
    )

    return run_dir
