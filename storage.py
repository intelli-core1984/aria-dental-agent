"""
ARIA — Local data storage
Saves captured + parsed Dentrix data as JSON.
No database needed — just flat files.
"""

import json
import time
from pathlib import Path
from paths import get_data_dir

DATA_DIR = get_data_dir() / "captures"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Storage:

    def save(self, key: str, data: dict):
        """Save a parsed data snapshot."""
        payload = {"timestamp": time.time(), "key": key, "data": data}
        path = DATA_DIR / f"{key}_{int(time.time())}.json"
        path.write_text(json.dumps(payload, indent=2))
        # Also overwrite the "latest" file for this key
        latest = DATA_DIR / f"{key}_latest.json"
        latest.write_text(json.dumps(payload, indent=2))

    def get_latest(self) -> dict:
        """Load all latest snapshots into one context dict."""
        context = {}
        for f in DATA_DIR.glob("*_latest.json"):
            try:
                payload = json.loads(f.read_text())
                context[payload["key"]] = payload["data"]
            except Exception:
                pass
        return context

    def get(self, key: str) -> dict | None:
        """Load the latest snapshot for a specific key."""
        path = DATA_DIR / f"{key}_latest.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())["data"]
        except Exception:
            return None

    def clear(self, key: str = None):
        """Clear stored data. Pass key to clear specific data only."""
        pattern = f"{key}_*.json" if key else "*.json"
        for f in DATA_DIR.glob(pattern):
            f.unlink()
