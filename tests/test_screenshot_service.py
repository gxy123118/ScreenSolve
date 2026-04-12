from datetime import datetime
from pathlib import Path

from quickshot.domain.screenshot_service import build_screenshot_name, ensure_output_dir


def test_build_screenshot_name_is_stable() -> None:
    fixed = datetime(2026, 4, 9, 10, 11, 12, 13000)
    assert build_screenshot_name(fixed) == "screenshot_20260409_101112_013000.png"


def test_ensure_output_dir_creates_folder(tmp_path: Path) -> None:
    target = tmp_path / "screens"
    result = ensure_output_dir(target)
    assert result.exists()
    assert result.is_dir()
