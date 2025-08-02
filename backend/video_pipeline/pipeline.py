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
import logging

from backend.video_pipeline import config
from backend.video_pipeline.video_io import get_video_props
from backend.video_pipeline.extract_frames import run as extract_frames
from backend.video_pipeline.embed_frames import run as embed_frames
from backend.video_pipeline.cluster_frames import run as cluster_frames
from backend.video_pipeline.select_representative_frames import run as choose_reps
from backend.video_pipeline.label_representative_frames import run as label_reps
from backend.video_pipeline.clipper import run as clipper
from backend.video_pipeline.metadata_writer import write as write_meta

# Configure logging
logger = logging.getLogger(__name__)

def run(video_path: str | Path, *, prefix: str | None = None, progress_callback=None) -> Path:
    """
    Execute the full pipeline and return the run directory containing all outputs.

    Parameters
    ----------
    video_path : str | Path
        Path to the source video.
    prefix     : Optional prefix for the run directory name.
    progress_callback : Optional callback function to report progress

    Returns
    -------
    Path
        Absolute path to the run directory (ready for zipping or further use).
    """
    
    def checkpoint(stage: str, message: str = ""):
        """Send progress update if callback is provided"""
        full_message = f"Pipeline: {stage}"
        if message:
            full_message += f" - {message}"
        logger.info(full_message)
        if progress_callback:
            try:
                progress_callback(stage, message)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def check_memory():
        """Check memory and force cleanup if needed"""
        from backend.video_pipeline.config import check_memory_limit, force_memory_cleanup, get_memory_usage, IS_RENDER
        
        # Skip memory checks on Render due to reporting issues
        if IS_RENDER:
            return True
        
        memory_info = get_memory_usage()
        if memory_info["available"]:
            logger.info(f"Memory check: {memory_info['used_mb']:.1f}MB ({memory_info['percent']:.1f}%)")
        
        if not check_memory_limit():
            logger.warning("Memory usage high, forcing cleanup...")
            force_memory_cleanup()
            return check_memory_limit()  # Check again after cleanup
        return True
    
    try:
        # ------------------------------------------------------------------ #
        # 0. unique workspace
        # ------------------------------------------------------------------ #
        checkpoint("Initializing", "Creating workspace directory")
        check_memory()  # Check memory before starting
        run_dir = config.new_run_dir(prefix=prefix)
        checkpoint("Workspace created", f"Directory: {run_dir}")

        # ------------------------------------------------------------------ #
        # 1. basic video properties
        # ------------------------------------------------------------------ #
        checkpoint("Analyzing video", "Extracting video properties")
        check_memory()
        props = get_video_props(video_path)
        checkpoint("Video analysis complete", f"Duration: {props.duration}s, FPS: {props.fps}")

        # ------------------------------------------------------------------ #
        # 2. frame extraction
        # ------------------------------------------------------------------ #
        checkpoint("Extracting frames", f"Sampling at {config.FRAME_RATE} FPS")
        check_memory()
        frames = extract_frames(video_path, run_dir)
        checkpoint("Frame extraction complete", f"Extracted {len(frames)} frames")
        check_memory()  # Check after frame extraction

        # ------------------------------------------------------------------ #
        # 3. local CLIP embeddings (with batch processing)
        # ------------------------------------------------------------------ #
        checkpoint("Computing embeddings", "Running CLIP model on frames")
        check_memory()
        embedded_frames = embed_frames(frames, run_dir)
        checkpoint("Embeddings complete", f"Processed {len(embedded_frames)} frames")
        check_memory()  # Check after embeddings

        # ------------------------------------------------------------------ #
        # 4. clustering via UMAP + HDBSCAN
        # ------------------------------------------------------------------ #
        checkpoint("Clustering frames", "Running UMAP + HDBSCAN")
        check_memory()
        clusters = cluster_frames(embedded_frames, props.duration, run_dir)
        checkpoint("Clustering complete", f"Found {len(clusters)} clusters")
        check_memory()  # Check after clustering

        # ------------------------------------------------------------------ #
        # 5. representative frame selection
        # ------------------------------------------------------------------ #
        checkpoint("Selecting representatives", "Choosing best frames from each cluster")
        check_memory()
        representatives = choose_reps(embedded_frames, clusters, run_dir)
        checkpoint("Representative selection complete", f"Selected {len(representatives)} representatives")
        check_memory()  # Check after selection

        # ------------------------------------------------------------------ #
        # 6. Hugging Face labeling of representatives
        # ------------------------------------------------------------------ #
        checkpoint("Labeling frames", "Generating descriptions via Hugging Face")
        check_memory()
        labeled_reps = label_reps(representatives, run_dir)
        checkpoint("Labeling complete", f"Labeled {len(labeled_reps)} frames")
        check_memory()  # Check after labeling

        # ------------------------------------------------------------------ #
        # 7. clip generation centred on reps
        # ------------------------------------------------------------------ #
        checkpoint("Generating clips", "Creating video clips around representatives")
        check_memory()
        clips = clipper(
            frames=frames,
            clusters=clusters,
            video_path=video_path,
            run_dir=run_dir,
        )
        checkpoint("Clip generation complete", f"Generated {len(clips)} clips")
        check_memory()  # Check after clip generation

        # ------------------------------------------------------------------ #
        # 8. write consolidated metadata
        # ------------------------------------------------------------------ #
        checkpoint("Writing metadata", "Creating final output files")
        check_memory()
        write_meta(
            run_dir,
            video_props=dataclasses.asdict(props),
            frame_rate=config.FRAME_RATE,
            embedding_model="openai/clip-vit-base-patch32",
            representatives=labeled_reps,  # includes labels
            clips=clips,
        )
        checkpoint("Pipeline complete", "All processing finished successfully")
        check_memory()  # Final memory check

        return run_dir
        
    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}"
        logger.error(error_msg)
        checkpoint("Pipeline failed", error_msg)
        raise
