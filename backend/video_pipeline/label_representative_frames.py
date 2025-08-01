"""
label_representative_frames.py
==============================

Labels representative frames via a HF multimodal endpoint using the OpenAI
client. Adds a "labels" dict to each rep and writes labels.json.
"""

from __future__ import annotations
import base64, json
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from backend.video_pipeline import config

# -------------------------------------------------- #
# Client initialisation
# -------------------------------------------------- #
if config.HF_API_TOKEN:
    client = OpenAI(
        base_url=config.HF_API_URL.rstrip("/"),
        api_key=config.HF_API_TOKEN,
    )
else:
    client = None

PROMPT = """You are labeling an adult pornographic image for use in a searchable content database.
You ONLY speak in JSON. You MUST NEVER use square brackets. You MUST NEVER use nested quotation marks. 
There will be DIRE CONSEQUENCES if instructions are not followed exactly.

You MUST return a valid JSON object with these 8 keys and plain text values:
{
  "title": "Short title of the scene based on what's happening visually. Be specific.",
  "actors": "Brief descriptions of body types, physical features, number of people. No names.",
  "positions": "Arrangement of people - e.g., one on top, side-by-side, standing, etc.",
  "acts": "Sexual acts being performed or implied.",
  "roles": "Passive, active, dominant, submissive, voyeur, etc.",
  "props": "Any visible objects or sex toys.",
  "kinks": "Recognizable themes/fetishes - e.g., BDSM, foot fetish, public, etc.",
  "environment": "Scene location - e.g., bedroom, kitchen, outdoor, studio, etc."
}
RETURN JSON ONLY. No square brackets. No nested quotation marks. YOU MUST FOLLOW INSTRUCTIONS WITH EXTREME DETAIL.

Example Output:
{
  "title": "Reverse cowgirl on leather couch",
  "actors": "Curvy brunette woman with large breasts, athletic bald man",
  "positions": "Woman on top facing away, man seated",
  "acts": "Vaginal sex, kissing",
  "roles": "Woman dominant, man passive",
  "props": "Black leather couch, white towel",
  "kinks": "Power play, close-up focus",
  "environment": "Living room with dim lighting"
}
Now generate the JSON labels for this image:"""

def _encode_image(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/jpeg;base64,{b64}"

def run(representatives: List[Dict], run_dir: Path) -> List[Dict]:
    enriched = []
    
    if not client:
        print("WARNING: No HF API token available, skipping frame labeling")
        # Return representatives without labels
        for rep in representatives:
            enriched.append({**rep, "labels": {"error": "No API token available"}})
        (run_dir / "labels.json").write_text(json.dumps(enriched, indent=2))
        return enriched
    
    for rep in representatives:
        img_path = run_dir / rep["path"]
        data_uri = _encode_image(img_path)

        try:
            chat = client.chat.completions.create(
                model="fancyfeast/llama-joycaption-beta-one-hf-llava",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                        {"type": "text", "text": PROMPT}
                    ]}],
                temperature=0.6,
                max_tokens=500,
                top_p=0.9,
                stream=False,
            )

            raw = chat.choices[0].message.content.strip()
            try:
                labels = json.loads(raw)
            except json.JSONDecodeError:
                labels = {"raw": raw}

            enriched.append({**rep, "labels": labels})
        except Exception as e:
            print(f"Error labeling frame {rep['path']}: {e}")
            enriched.append({**rep, "labels": {"error": str(e)}})

    (run_dir / "labels.json").write_text(json.dumps(enriched, indent=2))
    return enriched
