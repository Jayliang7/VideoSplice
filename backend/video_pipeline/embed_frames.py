"""
embed_frames.py
===============

• Uses Hugging Face's CLIPProcessor + CLIPModel locally (GPU if available).
• Converts every extracted frame to a NORMALISED 512-D vector.
• Adds "embedding" to each frame dict and persists them once to embeddings.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Dict

import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from tqdm import tqdm
import numpy as np

from backend.video_pipeline import config

# Configure logging
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 🔄  Load model once (cold-start cost amortised)
# --------------------------------------------------------------------------- #
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL_NAME = "openai/clip-vit-base-patch32"          # tweak here if needed

_processor = CLIPProcessor.from_pretrained(_MODEL_NAME)
_model: CLIPModel = CLIPModel.from_pretrained(_MODEL_NAME).to(DEVICE).eval()


# --------------------------------------------------------------------------- #
# Public API expected by the pipeline
# --------------------------------------------------------------------------- #
def run(frames: List[Dict], run_dir: Path) -> List[Dict]:
    """
    Parameters
    ----------
    frames   : output list from extract_frames.run  (no embeddings yet)
    run_dir  : unique run directory

    Returns
    -------
    List[Dict]  # same length, each dict gains "embedding": [float, …]
    """
    logger.info(f"Starting frame embedding for {len(frames)} frames on {DEVICE}")
    
    try:
        enriched: List[Dict] = []
        
        # Import memory monitoring
        from backend.video_pipeline.config import BATCH_SIZE, check_memory_limit, force_memory_cleanup, get_memory_usage
        
        # Process frames in batches for memory efficiency
        for batch_start in range(0, len(frames), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(frames))
            batch_frames = frames[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//BATCH_SIZE + 1}/{(len(frames) + BATCH_SIZE - 1)//BATCH_SIZE} (frames {batch_start+1}-{batch_end})")
            
            # Check memory before processing batch
            memory_info = get_memory_usage()
            if memory_info["available"]:
                logger.info(f"Memory before batch: {memory_info['used_mb']:.1f}MB ({memory_info['percent']:.1f}%)")
            
            if not check_memory_limit():
                logger.warning("Memory usage high before batch, forcing cleanup...")
                force_memory_cleanup()
            
            # Process batch
            for i, meta in enumerate(batch_frames):
                try:
                    img_path = run_dir / meta["path"]
                    
                    # Check if image file exists
                    if not img_path.exists():
                        logger.error(f"Image file not found: {img_path}")
                        raise FileNotFoundError(f"Image file not found: {img_path}")
                    
                    # Load and convert image
                    image = Image.open(img_path).convert("RGB")
                    
                    # Process with CLIP
                    inputs = _processor(images=image, return_tensors="pt").to(DEVICE)

                    with torch.no_grad():
                        features = _model.get_image_features(**inputs)   # (1, 512)

                    # CLIP best practice: L2-normalise so cosine ≈ dot-product
                    embedding = torch.nn.functional.normalize(features, dim=-1)
                    meta_with_emb = {**meta, "embedding": embedding.cpu().squeeze().tolist()}
                    enriched.append(meta_with_emb)
                    
                    # Clear GPU memory if using CUDA
                    if DEVICE == "cuda":
                        del features, embedding, inputs
                        torch.cuda.empty_cache()
                    
                except Exception as e:
                    logger.error(f"Failed to embed frame {batch_start + i} ({meta.get('path', 'unknown')}): {str(e)}")
                    raise
            
            # Check memory after batch
            memory_info = get_memory_usage()
            if memory_info["available"]:
                logger.info(f"Memory after batch: {memory_info['used_mb']:.1f}MB ({memory_info['percent']:.1f}%)")
            
            # Force cleanup after each batch
            force_memory_cleanup()

        # Persist once for offline debugging / reuse
        logger.info("Saving embeddings to embeddings.json")
        (run_dir / "embeddings.json").write_text(json.dumps(enriched, indent=2))
        
        logger.info(f"Successfully embedded {len(enriched)} frames")
        return enriched
        
    except Exception as e:
        logger.error(f"Frame embedding failed: {str(e)}")
        raise
