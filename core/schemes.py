"""Load every scheme Haq knows about, from all sources, in the common format."""
import json

from core.config import ROOT

PROCESSED_DIR = ROOT / "data" / "processed"
MANUAL_DIR = ROOT / "data" / "manual"

SOURCE_FILES = ["uk.json", "india.json"]


def load_all() -> list[dict]:
    """Processed (downloaded) schemes first, then manual ones.
    A manual record replaces a downloaded record with the same id."""
    schemes: dict[str, dict] = {}
    for folder in (PROCESSED_DIR, MANUAL_DIR):
        for name in SOURCE_FILES:
            path = folder / name
            if path.exists():
                for scheme in json.loads(path.read_text(encoding="utf-8")):
                    schemes[scheme["id"]] = scheme
    return list(schemes.values())
