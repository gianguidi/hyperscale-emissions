from __future__ import annotations

from pathlib import Path


def ensure_dir(path: str | Path) -> None:
    """Create directory if it does not exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
