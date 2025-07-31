from __future__ import annotations

"""video_pipeline.cluster_frames
---------------------------------
Clusters CLIP embeddings → segments.

* UMAP (10‑D, cosine) for dimensionality reduction
* HDBSCAN for density clustering
* Any frame HDBSCAN marks as *noise* (label ``-1``) is re‑segmented into
  **contiguous blocks** using the original frame order — this guarantees that
  clearly separated scenes still receive unique cluster IDs even when their
  embeddings are sparse or low‑variance.

The resulting mapping is persisted to ``clusters.json`` inside *run_dir*.
"""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import umap
import hdbscan

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(frames: List[Dict], video_duration: float, run_dir: Path) -> Dict[str, int]:  # noqa: D401,E501
    """Cluster frame embeddings into scene segments.

    Parameters
    ----------
    frames
        Output list from :pyfunc:`video_pipeline.embed_frames.run`.
        Each dict contains at least ``index`` (int), ``path`` (str), and
        ``embedding`` (list[float]).
    video_duration
        *Unused* today (kept for API stability).
    run_dir
        Directory for this pipeline run – used for artefacts.

    Returns
    -------
    dict[str, int]
        Mapping from *relative* frame path to cluster ID (0‑based).
    """

    # ---------------------------------------------------------------------
    # Fast‑path – trivial videos
    # ---------------------------------------------------------------------
    if len(frames) < 2:
        mapping = {f["path"]: 0 for f in frames}
        _save(run_dir, mapping)
        return mapping

    # ---------------------------------------------------------------------
    # Data preparation
    # ---------------------------------------------------------------------
    df = pd.DataFrame(frames).sort_values("index").reset_index(drop=True)

    X = np.stack(df["embedding"].to_numpy(), dtype=np.float32)

    # ---------------------------------------------------------------------
    # 1. UMAP 512‑D → 10‑D  (cosine distance preserves CLIP space nicely)
    # ---------------------------------------------------------------------
    reducer = umap.UMAP(
        n_components=10,
        metric="cosine",
        random_state=42,
        min_dist=0.0,
    )
    X_umap = reducer.fit_transform(X).astype(np.float32)
    np.save(run_dir / "umap_embeddings.npy", X_umap)  # debugging artefact

    # ---------------------------------------------------------------------
    # 2. HDBSCAN density clustering
    # ---------------------------------------------------------------------
    min_cluster_size = max(3, len(frames) // 20)  # ≥3 frames or 5 % of total
    clusterer = hdbscan.HDBSCAN(
        metric="euclidean",
        min_cluster_size=min_cluster_size,
        min_samples=None,
    ).fit(X_umap)

    labels = clusterer.labels_  # -1 for noise

    # ---------------------------------------------------------------------
    # 3. Re‑segment noise into contiguous blocks so that distinct scenes that
    #    HDBSCAN thought were sparse still get unique IDs.
    # ---------------------------------------------------------------------
    final_labels = labels.copy()
    next_cluster_id = final_labels.max() + 1  # first free positive integer

    in_noise_block = False
    for i, lbl in enumerate(labels):
        if lbl == -1 and not in_noise_block:
            # Start of a new contiguous noise block → assign new cluster ID
            current_id = next_cluster_id
            next_cluster_id += 1
            in_noise_block = True
        elif lbl != -1:
            in_noise_block = False
            current_id = lbl
        final_labels[i] = current_id

    mapping = dict(zip(df["path"], final_labels.astype(int).tolist()))

    _save(run_dir, mapping)
    return mapping


# ---------------------------------------------------------------------------
# Helper – persist mapping once
# ---------------------------------------------------------------------------

def _save(run_dir: Path, mapping: Dict[str, int]):
    (run_dir / "clusters.json").write_text(json.dumps(mapping, indent=2))
