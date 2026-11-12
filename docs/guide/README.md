# 安装与配置

## 安装

准备 Git 和 uv。项目要求 Python 3.11 或更高版本，仓库的 `.python-version` 指定开发环境使用 Python 3.11。

```powershell
git clone https://github.com/Rectangle518/skydoor.git
cd skydoor
uv sync
```

## 配置模型服务

在项目根目录创建 `.env`，把下面的占位值换成服务实际提供的配置。

```dotenv
AGNES_BASE_URL=https://your-provider.example/v1
AGNES_API_KEY=your-api-key
AGNES_MODEL=your-model
```

也可以在 shell 中设置这三个环境变量。示例通过 `python-dotenv` 读取配置，再把值传给 `Agent`。业务代码自行创建 `Agent` 时，需要负责读取并传入配置。请将实际密钥保存在本地，避免提交到仓库。

在 [examples/basic_chat.py](https://github.com/Rectangle518/skydoor/blob/main/examples/basic_chat.py) 中，让 `llm_api_type` 与服务提供的接口匹配。

| 服务接口 | `llm_api_type` |
| --- | --- |
| OpenAI 兼容的 Chat Completions | `chat_completion`（示例默认值） |
| Anthropic Messages 或兼容接口 | `messages` |
| OpenAI Responses 或兼容接口 | `responses` |

`base_url` 填服务商提供给对应 SDK 的基础地址。路径前缀以服务商文档为准。

[下一步：运行两轮对话](first-chat.md)
