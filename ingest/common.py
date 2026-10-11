"""Helpers shared by every ingestion script (UK, India, ...)."""
import json
import time
from pathlib import Path

import httpx

# Project root = two folders up from this file (haq/ingest/common.py -> haq/)
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

USER_AGENT = "HaqBot/0.1 (hackathon project; benefits research)"


class PoliteClient:
    """HTTP client that waits between requests and retries on failure,
    so we never hammer government servers."""

    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self._last_request = 0.0
        self._http = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=30,
            follow_redirects=True,
        )

    def get_json(self, url: str, params: dict | None = None, retries: int = 3) -> dict:
        for attempt in range(1, retries + 1):
            wait = self.delay - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()
            try:
                response = self._http.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                if attempt == retries:
                    raise
                time.sleep(2**attempt)  # back off: 2s, 4s, ...

    def close(self) -> None:
        self._http.close()

    # These two methods let us write `with PoliteClient() as client:`,
    # which closes the connection automatically at the end of the block.
    def __enter__(self) -> "PoliteClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
