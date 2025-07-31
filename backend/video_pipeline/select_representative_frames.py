"""
select_representative_frames.py
===============================

Given:
    • frames  – list from embed_frames.run  (contains "embedding")
    • clusters – {frame_path: cluster_id}   (from cluster_frames.run)

Produces:
    • representatives.json  – list of dicts with the chosen representative
                              frame for every cluster id.
Returns:
    List[Dict]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

import numpy as np


def run(
    frames: List[Dict],
    clusters: Dict[str, int],
    run_dir: Path,
) -> List[Dict]:
    """
    Pick the frame whose embedding is *closest to the centroid* of each cluster.

    Parameters
    ----------
    frames   : output list from embed_frames.run
    clusters : mapping {frame_path: cluster_id}
    run_dir  : Path to run directory

    Returns
    -------
    List[Dict] with keys:
        cluster, timestamp, path, index, embedding
    """
    # -------------------- regroup frames by cluster ------------------------
    grouped: Dict[int, List[Dict]] = defaultdict(list)
    for meta in frames:
        cid = clusters[meta["path"]]
        grouped[cid].append(meta)

    representatives: List[Dict] = []

    for cid, items in grouped.items():
        # (N, 512)
        X = np.array([f["embedding"] for f in items], dtype=np.float32)
        centroid = X.mean(axis=0, keepdims=True)  # (1, 512)

        # Euclidean distance to centroid
        dists = np.linalg.norm(X - centroid, axis=1)
        best_idx = int(dists.argmin())
        best = items[best_idx]

        representatives.append(
            {
                "cluster": int(cid),
                "timestamp": best["timestamp"],
                "index": best["index"],
                "path": best["path"],        # relative path e.g. frames/frame_000123.jpg
                "embedding": best["embedding"],
            }
        )

    # Persist for debugging / later steps
    (run_dir / "representatives.json").write_text(json.dumps(representatives, indent=2))
    return representatives
