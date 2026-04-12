from __future__ import annotations

import tomllib
from pathlib import Path

from quickshot.domain.models import AppConfig


def load_config(project_root: Path | None = None) -> AppConfig:
    root = project_root or Path.cwd()
    config_path = root / "quickshot.toml"

    if not config_path.exists():
        return AppConfig(
            hotkey="<ctrl>+<alt>+s",
            output_dir=root / "screenshots",
            ai_enabled=True,
            ai_copy_to_clipboard=True,
            ai_provider="glm",
            ai_model="glm-5.1",
            ai_base_url="https://open.bigmodel.cn/api/paas/v4",
            ai_api_key="",
            ai_api_key_env="ZHIPUAI_API_KEY",
            config_path=None,
        )

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    hotkey = str(data.get("hotkey", "<ctrl>+<alt>+s"))
    output_raw = str(data.get("output_dir", "screenshots"))
    ai_enabled = bool(data.get("ai_enabled", True))
    ai_copy_to_clipboard = bool(data.get("ai_copy_to_clipboard", True))
    ai_provider = str(data.get("ai_provider", "glm"))
    ai_model = str(data.get("ai_model", "glm-5.1"))
    ai_base_url = str(data.get("ai_base_url", "https://open.bigmodel.cn/api/paas/v4"))
    ai_api_key = str(data.get("ai_api_key", "")).strip()
    ai_api_key_env = str(data.get("ai_api_key_env", "ZHIPUAI_API_KEY"))
    output_dir = Path(output_raw)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    return AppConfig(
        hotkey=hotkey,
        output_dir=output_dir,
        ai_enabled=ai_enabled,
        ai_copy_to_clipboard=ai_copy_to_clipboard,
        ai_provider=ai_provider,
        ai_model=ai_model,
        ai_base_url=ai_base_url,
        ai_api_key=ai_api_key,
        ai_api_key_env=ai_api_key_env,
        config_path=config_path,
    )
