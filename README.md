# SCSE Requirements Engineering Agent

本项目用于完成 SCSE Requirements Engineering 练习。

项目目标是：使用本地 Ollama 中的 Qwen 模型，把 `brief.txt` 中的自然语言机器人导航需求，转换成明确的软件需求，并保存为经过验证的 JSON 文件。

## 项目结构

```text
agentic_se/
  artifacts/
    requirements.json
  analyst_agent.py
  brief.txt
  brief_to_req.py
  README.md
  robot_requirements.txt
  run_analyst.py
```

## 文件说明

### `brief.txt`

这是老师提供的原始需求文本。

它描述了一个移动机器人导航组件需要满足的行为：

- 机器人会收到前方、左侧、右侧是否被阻挡的信息
- 机器人可能会收到目标方向信息
- 如果安全，机器人应该优先朝目标方向移动
- 机器人绝不能移动到被阻挡的方向
- 如果没有任何安全方向，机器人必须停止
- 导航组件之后会在多个模拟环境中测试

### `brief_to_req.py`

这是第一阶段实验脚本。

它会读取 `brief.txt`，调用本地 Ollama 中的 `qwen3:8b` 模型，让 Qwen 把自然语言 brief 转换成人类可读的软件需求说明。

这个文件对应作业中“先让 Qwen 阅读 brief 并生成软件需求”的要求。

### `robot_requirements.txt`

这个文件保存了一次运行 `brief_to_req.py` 后得到的 Qwen 输出。

它是第一阶段需求分析实验的文本记录。

### `analyst_agent.py`

这是正式的 Analyst Agent 实现文件。

它包含两个主要函数：

- `run_analyst(brief_text)`：接收 brief 文本，调用 Qwen，获取 JSON 文本，解析 JSON，验证结果，并返回验证后的需求
- `validate_requirements(result)`：检查 Qwen 生成的需求是否符合老师要求的固定结构

Analyst Agent 要求 Qwen 最终只输出 JSON，并且 JSON 必须包含以下 4 个 key：

- `goal`
- `allowed_actions`
- `safe_stop`
- `avoid_obstacles`

其中机器人允许的动作只能是：

- `FORWARD`
- `LEFT`
- `RIGHT`
- `STOP`

### `run_analyst.py`

这是正式运行入口。

它负责：

1. 读取 `brief.txt`
2. 调用 `run_analyst()`
3. 创建 `artifacts` 文件夹
4. 把验证后的需求保存到 `artifacts/requirements.json`

### `artifacts/requirements.json`

这是最终输出文件。

它保存了由 Qwen 生成、并通过 Python 验证函数检查后的结构化软件需求。

### `.gitignore`

这个文件用于避免把本地开发环境文件上传到 GitHub。

它会忽略：

- `.venv/`
- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`

## 环境要求

本项目使用：

- Python 3.12
- uv
- Ollama
- Ollama 模型 `qwen3:8b`

程序会调用本地 Ollama API：

```text
http://localhost:11434/api/generate
```

## 如何运行

在项目根目录中创建虚拟环境：

```powershell
uv venv --python "C:\Program Files\Python312\python.exe" .venv
```

运行第一阶段实验脚本：

```powershell
.\.venv\Scripts\python.exe brief_to_req.py
```

运行正式 Analyst Agent：

```powershell
.\.venv\Scripts\python.exe run_analyst.py
```

运行成功后，最终结果会保存在：

```text
artifacts/requirements.json
```

## 最终 JSON 格式

最终输出应符合以下结构：

```json
{
  "goal": "Navigate toward the goal location",
  "allowed_actions": ["FORWARD", "LEFT", "RIGHT", "STOP"],
  "safe_stop": true,
  "avoid_obstacles": true
}
```

其中 `goal` 的具体英文表述可能会因为 Qwen 的生成结果略有不同，但 JSON 的 key、数据类型、以及 `allowed_actions` 的动作列表必须符合要求。

## 本地检查方法

可以用以下命令确认正式程序是否能运行：

```powershell
.\.venv\Scripts\python.exe run_analyst.py
```

如果终端输出类似下面内容，说明运行成功：

```text
Saved validated requirements to D:\agentic_se\artifacts\requirements.json
```

然后打开 `artifacts/requirements.json`，确认里面是合法 JSON，并且只包含老师要求的 4 个字段。
