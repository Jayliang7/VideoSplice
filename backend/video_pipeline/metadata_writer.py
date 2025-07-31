from __future__ import annotations

"""Metadata writer for the VideoSplice pipeline.

Key features
------------
* **Flexible signature** – Accepts any extra keyword arguments (e.g. ``frame_rate``)
  so upstream modules can evolve without breaking this writer.
* **Safe JSON serialisation** – Converts unsupported objects (``pathlib.Path``,
  NumPy scalars, datetimes, …) to strings via a single fallback.
* **Backwards‑compatibility alias** – ``write`` points to :func:`write_meta` so
  older imports keep working.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

__all__: list[str] = ["write_meta", "write"]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _json_fallback(obj: Any) -> Any:  # noqa: D401
    """Fallback converter passed to ``json.dumps(default=…)``.

    Currently coerces everything not natively supported by the standard JSON
    encoder to ``str(obj)``. Extend this function if you later need special
    handling (e.g. turn ``datetime`` into ISO‑8601 or ``ndarray`` into lists).
    """

    return str(obj)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_meta(
    run_dir: Path,
    *,
    video_props: Dict[str, Any],
    clips: List[Dict[str, Any]],
    filename: str = "metadata.json",
    **extra: Any,
) -> None:
    """Persist pipeline metadata as pretty‑printed JSON.

    Parameters
    ----------
    run_dir
        Directory allocated for the current pipeline run.
    video_props
        Basic video information (fps, width, height, duration, etc.).
    clips
        List describing each clip (start/end, representative frame, tags, …).
    filename
        Output filename; defaults to ``metadata.json``.
    **extra
        Any additional top‑level metadata sections (e.g. ``frame_rate``,
        ``umap_params``). They are merged into the JSON root so call‑sites can
        evolve without touching this writer.
    """

    run_dir.mkdir(parents=True, exist_ok=True)

    meta: Dict[str, Any] = {
        "run_dir": run_dir,
        "video_props": video_props,
        "clips": clips,
        **extra,  # e.g. frame_rate=…
    }

    json_path = run_dir / filename
    json_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=_json_fallback)
    )

    logger.info("Saved metadata → %s", json_path)


# ---------------------------------------------------------------------------
# Legacy alias expected by older code (e.g. video_pipeline/pipeline.py)
# ---------------------------------------------------------------------------

write = write_meta
