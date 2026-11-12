# Skydoor

Skydoor 是一个 Python 异步文本对话框架。它维护内存中的会话历史，并通过统一接口调用 Chat Completion、Anthropic Messages 或 OpenAI Responses。要求 Python 3.11 或更高版本。

在项目根目录运行 `uv sync` 安装项目及开发依赖。运行 [对话示例](examples/basic_chat.py) 前，在本地 `.env` 或环境变量中配置服务地址、密钥和模型：

```dotenv
AGNES_BASE_URL=https://your-provider.example/v1
AGNES_API_KEY=your-api-key
AGNES_MODEL=your-model
```

将 `llm_api_type` 设为服务所用的协议：`chat_completion`、`messages` 或 `responses`。运行 `uv run ./examples/basic_chat.py` 会向配置的服务发送两轮请求。

- 同一个 Agent 的 `run()` 应按顺序调用。已有一轮运行时，另一次调用会立即抛出 `AgentError`。请在请求进行期间避免直接修改会话历史。
- `run()` 返回完整的非空文本。失败、空响应、截断或当前不支持的响应形式会抛出 `LLMError`。调用失败或取消时，Agent 会回滚本轮追加的用户消息。
- 重试由 Agent 负责。默认只对超时、连接故障、临时限流和可识别的服务端瞬时错误等情况重试，最多重试 3 次，含首次共 4 次尝试。设置 `max_retries=0` 可关闭重试。`timeout` 传给 SDK 的单次请求，整轮耗时还包括其余尝试和指数退避。
- 单次调用的 `temperature`、`max_tokens` 和 `timeout` 为 `None` 时沿用 Agent 配置。构造 Agent 时将这些参数设为 `None` 可省略对应 SDK 参数，Messages 的必填 `max_tokens` 仍会回退到框架默认值。

运行 `uv run pytest` 可执行离线测试。
