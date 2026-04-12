from __future__ import annotations

from pathlib import Path

from rapidocr_onnxruntime import RapidOCR


class OcrEngine:
    def __init__(self) -> None:
        self._engine = RapidOCR()

    def extract_text(self, image_path: Path) -> str:
        result, _ = self._engine(str(image_path))
        if not result:
            return ""

        lines: list[str] = []
        for item in result:
            if not item or len(item) < 2:
                continue
            text = str(item[1]).strip()
            if text:
                lines.append(text)
        return "\n".join(lines)
