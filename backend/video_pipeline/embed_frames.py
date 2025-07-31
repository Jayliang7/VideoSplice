"""
embed_frames.py
===============

• Uses Hugging Face's CLIPProcessor + CLIPModel locally (GPU if available).
• Converts every extracted frame to a NORMALISED 512-D vector.
• Adds "embedding" to each frame dict and persists them once to embeddings.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from tqdm import tqdm
import numpy as np

from video_pipeline import config

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
    enriched: List[Dict] = []

    for meta in tqdm(frames, desc="Embedding frames"):
        img_path = run_dir / meta["path"]
        image = Image.open(img_path).convert("RGB")

        inputs = _processor(images=image, return_tensors="pt").to(DEVICE)

        with torch.no_grad():
            features = _model.get_image_features(**inputs)   # (1, 512)

        # CLIP best practice: L2-normalise so cosine ≈ dot-product
        embedding = torch.nn.functional.normalize(features, dim=-1)
        meta_with_emb = {**meta, "embedding": embedding.cpu().squeeze().tolist()}
        enriched.append(meta_with_emb)

    # Persist once for offline debugging / reuse
    (run_dir / "embeddings.json").write_text(json.dumps(enriched, indent=2))
    return enriched
