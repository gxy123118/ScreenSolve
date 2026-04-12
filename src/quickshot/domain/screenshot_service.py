from __future__ import annotations

from datetime import datetime
from pathlib import Path


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_screenshot_name(now: datetime | None = None) -> str:
    current = now or datetime.now()
    return f"screenshot_{current.strftime('%Y%m%d_%H%M%S_%f')}.png"
