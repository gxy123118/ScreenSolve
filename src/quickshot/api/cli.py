from __future__ import annotations

import atexit
import os
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Thread

from quickshot.domain.answer_rules import NO_ANSWER
from quickshot.domain.screenshot_service import build_screenshot_name, ensure_output_dir
from quickshot.infra.capture import ScreenCapture
from quickshot.infra.clipboard import set_text
from quickshot.infra.config import load_config
from quickshot.infra.glm_client import GLMClient, RateLimitError
from quickshot.infra.hotkey import GlobalHotkeyListener
from quickshot.infra.ocr import OcrEngine


def _register_pid_file(pid_path: Path) -> None:
    pid_path.write_text(str(os.getpid()), encoding="utf-8")

    def cleanup() -> None:
        try:
            if pid_path.exists() and pid_path.read_text(encoding="utf-8").strip() == str(
                os.getpid()
            ):
                pid_path.unlink()
        except OSError:
            pass

    atexit.register(cleanup)


def main() -> None:
    config = load_config()
    pid_path = Path.cwd() / "quickshot.pid"
    _register_pid_file(pid_path)
    capture = ScreenCapture()
    ocr = OcrEngine()
    glm = GLMClient(
        base_url=config.ai_base_url,
        model=config.ai_model,
        api_key=config.ai_api_key,
        api_key_env=config.ai_api_key_env,
    )
    output_dir = ensure_output_dir(config.output_dir)
    job_queue: Queue[Path] = Queue(maxsize=1)

    def ai_worker() -> None:
        while True:
            image_path = job_queue.get()
            try:
                if config.ai_enabled and config.ai_provider.lower() == "glm":
                    ocr_text = ocr.extract_text(image_path)
                    print(f"OCR chars: {len(ocr_text)}", flush=True)
                    answer = glm.solve_from_ocr(ocr_text)
                    if config.ai_copy_to_clipboard:
                        set_text(answer)
                        print("AI answer copied to clipboard.", flush=True)
                    if answer == NO_ANSWER:
                        print("AI parser failed. Retry or switch model.", flush=True)
                    print(f"AI Answer:\n{answer}", flush=True)
                else:
                    print(f"AI provider not supported: {config.ai_provider}", flush=True)
            except RateLimitError as err:
                print(f"AI rate-limited: {err}", flush=True)
            except Exception as err:
                print(f"AI step skipped: {err}", flush=True)
            finally:
                job_queue.task_done()

    Thread(target=ai_worker, daemon=True).start()

    def take_shot() -> None:
        filename = build_screenshot_name()
        output_path = output_dir / filename
        saved_path = capture.capture_primary_display(output_path=output_path)
        print(f"Saved: {saved_path}", flush=True)

        try:
            while True:
                stale = job_queue.get_nowait()
                job_queue.task_done()
                print(f"Dropped stale job: {stale.name}", flush=True)
        except Empty:
            pass

        try:
            job_queue.put_nowait(saved_path)
            print("Queued screenshot for AI solving.", flush=True)
        except Full:
            print("AI queue is busy, skipped this screenshot.", flush=True)

    print("QuickShot is running...", flush=True)
    print(f"Hotkey: {config.hotkey}", flush=True)
    print(f"Output: {output_dir}", flush=True)
    print(f"AI Enabled: {config.ai_enabled} ({config.ai_provider})", flush=True)
    print(f"AI Model: {config.ai_model}", flush=True)
    print("OCR Engine: RapidOCR", flush=True)
    print(f"AI Answer Clipboard: {config.ai_copy_to_clipboard}", flush=True)
    if config.config_path is not None:
        print(f"Config: {config.config_path}", flush=True)
    else:
        print("Config: quickshot.toml not found, using defaults.", flush=True)
    print("Press Ctrl+C in this terminal to stop.", flush=True)

    listener = GlobalHotkeyListener(config.hotkey, take_shot)
    listener.run()


if __name__ == "__main__":
    main()
