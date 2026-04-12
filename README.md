# QuickShot

处理流程：
`截图 -> 本地 OCR -> GLM-5.1 文本推理 -> 写入剪贴板`

## 运行方式

```powershell
cd E:\code\ScreenSolve
.\scripts\start_quickshot.ps1
```

## 配置说明

编辑 [quickshot.toml](/E:/code/ScreenSolve/quickshot.toml)：

```toml
hotkey = "<ctrl>+<alt>+s"
output_dir = "screenshots"
ai_enabled = true
ai_copy_to_clipboard = true
ai_provider = "glm"
ai_model = "glm-5.1"
ai_base_url = "https://open.bigmodel.cn/api/paas/v4"
ai_api_key = "your_glm_key"
ai_api_key_env = "ZHIPUAI_API_KEY"
```

## 说明

- 当前模式为本地 OCR 加 GLM 文本推理。
- OCR 引擎使用 `RapidOCR`。
- 目标输出格式为 `question.option:answer_text`。
- 终端或日志中会打印 `OCR chars: N`，可用于排查识别结果。
