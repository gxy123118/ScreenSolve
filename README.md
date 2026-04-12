# QuickShot

Pipeline:
`screenshot -> local OCR -> GLM-5.1 text reasoning -> clipboard`

## Run

```powershell
cd E:\code\demo1
.\scripts\start_quickshot.ps1
```

## Config

Edit [quickshot.toml](/E:/code/demo1/quickshot.toml):

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

Notes:
- Current mode is local OCR plus GLM text reasoning.
- OCR engine: `RapidOCR`.
- Output format target: `question.option:answer_text`.
- The terminal/log will print `OCR chars: N` for diagnosis.
