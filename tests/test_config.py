from pathlib import Path

from quickshot.infra.config import load_config


def test_load_config_defaults_when_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    assert config.hotkey == "<ctrl>+<alt>+s"
    assert config.output_dir == tmp_path / "screenshots"
    assert config.ai_enabled is True
    assert config.ai_copy_to_clipboard is True
    assert config.ai_provider == "glm"
    assert config.ai_model == "glm-5.1"
    assert config.ai_base_url == "https://open.bigmodel.cn/api/paas/v4"
    assert config.ai_api_key == ""
    assert config.ai_api_key_env == "ZHIPUAI_API_KEY"
    assert config.config_path is None


def test_load_config_from_toml(tmp_path: Path) -> None:
    content = (
        'hotkey = "<ctrl>+<shift>+q"\n'
        'output_dir = "shots"\n'
        "ai_enabled = false\n"
        'ai_provider = "glm"\n'
        'ai_model = "glm-5.1"\n'
        'ai_base_url = "https://open.bigmodel.cn/api/paas/v4"\n'
        'ai_api_key = "abc123"\n'
        'ai_api_key_env = "MY_GLM_KEY"\n'
    )
    (tmp_path / "quickshot.toml").write_text(content, encoding="utf-8")
    config = load_config(tmp_path)
    assert config.hotkey == "<ctrl>+<shift>+q"
    assert config.output_dir == tmp_path / "shots"
    assert config.ai_enabled is False
    assert config.ai_provider == "glm"
    assert config.ai_model == "glm-5.1"
    assert config.ai_base_url == "https://open.bigmodel.cn/api/paas/v4"
    assert config.ai_api_key == "abc123"
    assert config.ai_api_key_env == "MY_GLM_KEY"
    assert config.config_path == tmp_path / "quickshot.toml"
