"""Reads settings from the .env file in the project root."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def require(name: str) -> str:
    """Return an environment variable, or stop with a clear message if it's missing."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set. Add it to {ROOT / '.env'} (see .env.example).")
    return value


NEBIUS_API_KEY = require("NEBIUS_API_KEY")
NEBIUS_BASE_URL = os.environ.get("NEBIUS_BASE_URL", "").strip() or "https://api.tokenfactory.nebius.com/v1/"


def database_url() -> str:
    # A function, not a constant: scripts that don't touch the database
    # shouldn't fail just because DATABASE_URL isn't set yet.
    return require("DATABASE_URL")
