# QuickShot / ScreenSolve

一个用于快速截图、OCR 识别并调用 GLM 进行题目解析的桌面工具。

当前处理流程：

`截图 -> 本地 OCR -> GLM-5.1 文本推理 -> 写入剪贴板`

## 项目现状

- 包名：`quickshot`
- 当前版本：`0.1.0`
- Python 要求：`>=3.10`
- 当前实现更适合在 `Windows` 上运行

虽然截图和热键依赖库本身支持多平台，但当前项目里的剪贴板实现使用了 Windows `ctypes.windll` 接口，因此 README 需要明确把 Windows 作为当前主要运行平台。

## 环境要求

建议使用下面的环境：

- 操作系统：`Windows 10` 或 `Windows 11`
- Python：`3.10`、`3.11` 或 `3.12`
- `pip`：建议使用较新的版本
- 网络：需要能访问 GLM API

说明：

- `pyproject.toml` 中声明的是 `requires-python = ">=3.10"`。
- 从兼容性和稳定性角度，优先推荐 `Python 3.10` 或 `3.11`。
- 我在当前机器上只确认到本机 Python 是 `3.14.0`，但没有为这个仓库安装依赖，所以没有在这里完成完整运行验证。

## 依赖

项目核心依赖如下：

- `mss`：截图
- `pynput`：全局热键监听
- `rapidocr-onnxruntime`：本地 OCR
- `requests`：调用 GLM API

开发测试依赖：

- `pytest`

## 目录结构

```text
ScreenSolve/
├─ quickshot.toml
├─ pyproject.toml
├─ scripts/
│  ├─ start_quickshot.ps1
│  └─ start_quickshot.bat
├─ src/quickshot/
└─ tests/
```

## 安装

### 方式一：使用项目自带脚本启动（推荐，Windows）

项目已经提供了 PowerShell 启动脚本，会自动：

1. 创建 `.venv`
2. 安装项目依赖
3. 启动主程序

运行方式：

```powershell
cd <你的项目路径>\ScreenSolve
.\scripts\start_quickshot.ps1
```

如果你习惯双击，也可以使用：

```bat
scripts\start_quickshot.bat
```

### 方式二：手动创建虚拟环境并启动

```powershell
cd <你的项目路径>\ScreenSolve
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
python -m quickshot.api.cli
```

## 配置

项目默认从仓库根目录读取 `quickshot.toml`。

示例配置：

```toml
# Global hotkey format follows pynput.HotKey.parse syntax.
hotkey = "<ctrl>+<alt>+s"

# Relative paths are resolved from this project root.
output_dir = "screenshots"

# Pipeline: screenshot file -> local OCR -> GLM text reasoning -> clipboard text.
ai_enabled = true
ai_copy_to_clipboard = true
ai_provider = "glm"
ai_model = "glm-5.1"
ai_base_url = "https://open.bigmodel.cn/api/paas/v4"
ai_api_key = ""
ai_api_key_env = "ZHIPUAI_API_KEY"
```

### 配置项说明

- `hotkey`：全局快捷键，语法遵循 `pynput.HotKey.parse`
- `output_dir`：截图输出目录，支持相对路径
- `ai_enabled`：是否启用 AI 解题
- `ai_copy_to_clipboard`：是否自动把答案写入剪贴板
- `ai_provider`：当前仅实现了 `glm`
- `ai_model`：默认 `glm-5.1`
- `ai_base_url`：GLM API 地址
- `ai_api_key`：直接填写 API Key
- `ai_api_key_env`：当 `ai_api_key` 为空时，回退读取的环境变量名

## API Key 配置

二选一即可：

### 方式一：直接写在 `quickshot.toml`

```toml
ai_api_key = "your_glm_key"
```

### 方式二：通过环境变量提供

PowerShell：

```powershell
$env:ZHIPUAI_API_KEY="your_glm_key"
.\scripts\start_quickshot.ps1
```

如果 `ai_api_key` 不为空，程序会优先使用配置文件中的值。

## 运行后行为

程序启动后会在终端打印类似信息：

- 当前热键
- 截图输出目录
- AI 是否启用
- 使用的模型
- 配置文件位置

按下快捷键后会执行：

1. 截取主显示器画面
2. 保存到 `output_dir`
3. 调用 RapidOCR 提取文本
4. 把 OCR 文本发送给 GLM 推理
5. 将结果复制到剪贴板

默认目标输出格式：

```text
question.option:answer_text
```

例如：

```text
2.A:死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。
```

## 默认值

当根目录下没有 `quickshot.toml` 时，程序会使用以下默认配置：

```toml
hotkey = "<ctrl>+<alt>+s"
output_dir = "screenshots"
ai_enabled = true
ai_copy_to_clipboard = true
ai_provider = "glm"
ai_model = "glm-5.1"
ai_base_url = "https://open.bigmodel.cn/api/paas/v4"
ai_api_key = ""
ai_api_key_env = "ZHIPUAI_API_KEY"
```

## 测试

安装开发依赖后可运行：

```powershell
pip install -e .[dev]
pytest -q
```

说明：

- 我在当前环境里尝试执行 `pytest -q` 时，系统提示未安装 `pytest`，因此这次没有直接完成测试执行。
- 仓库内现有测试主要覆盖配置加载、截图文件名和答案规范化逻辑。

## 已知限制

- 当前剪贴板实现依赖 Windows API，因此不适合直接在 macOS / Linux 运行。
- 当前截图逻辑固定抓取主显示器：`sct.monitors[1]`
- 当前 AI provider 只实现了 `glm`
- 需要手动准备可用的 GLM API Key

## 常见问题

### 1. 启动时报权限或脚本执行错误

可尝试：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_quickshot.ps1
```

### 2. 按快捷键没有反应

建议检查：

- 快捷键是否与系统或其他软件冲突
- 当前程序是否仍在运行
- 是否已有旧进程未退出

项目自带脚本会尝试读取 `quickshot.pid` 并关闭之前的实例。

### 3. 能截图但没有答案

建议检查：

- `ai_enabled` 是否为 `true`
- `ai_api_key` 或环境变量是否正确
- 网络是否能访问 `https://open.bigmodel.cn/api/paas/v4`
- 终端中的 `OCR chars: N` 输出是否正常

### 4. 剪贴板写入失败

这是 Windows 剪贴板接口相关问题，通常与：

- 剪贴板被其他程序占用
- 当前进程权限不足
- 在非 Windows 环境运行

有关。

## 开发

如果你要继续扩展这个项目，建议优先补这些点：

- 明确跨平台支持范围
- 增加 macOS / Linux 剪贴板适配
- 为 README 增加完整的示例输出
- 增加依赖安装失败时的排障说明
- 增加 OCR 与 GLM 调试开关
