import json
from pathlib import Path


def load_keyword_pack(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"target_keywords": [], "target_phrases": [], "stop_phrases": []}

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    return {
        "target_keywords": payload.get("target_keywords", []),
        "target_phrases": payload.get("target_phrases", []),
        "stop_phrases": payload.get("stop_phrases", []),
    }
