from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    hotkey: str
    output_dir: Path
    ai_enabled: bool = True
    ai_copy_to_clipboard: bool = True
    ai_provider: str = "glm"
    ai_model: str = "glm-5.1"
    ai_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    ai_api_key: str = ""
    ai_api_key_env: str = "ZHIPUAI_API_KEY"
    config_path: Path | None = None
