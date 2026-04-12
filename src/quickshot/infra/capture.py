from __future__ import annotations

from pathlib import Path

from mss import mss, tools


class ScreenCapture:
    def capture_primary_display(self, output_path: Path) -> Path:
        with mss() as sct:
            monitor = sct.monitors[1]
            shot = sct.grab(monitor)
            tools.to_png(shot.rgb, shot.size, output=str(output_path))
        return output_path
