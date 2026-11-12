# API 参考

## Agent

从 `skydoor.core.agent` 导入 `Agent`。构造时会初始化内存会话，把 `system_prompt` 加入历史，并按 `llm_api_type` 创建 Provider。

| 构造参数 | 默认值 | 用途 |
| --- | --- | --- |
| `system_prompt` | 必填 | 系统提示词 |
| `base_url` | `None` | 服务基础地址。传入 `None` 时交给相应 SDK 处理 |
| `api_key` | `None` | 服务密钥。传入 `None` 时交给相应 SDK 处理 |
| `model` | `None` | 请求使用的模型标识。实际调用时请提供服务支持的模型 |
| `llm_api_type` | `"chat_completion"` | 可选 `"chat_completion"`、`"messages"` 或 `"responses"` |
| `temperature` | `0.7` | 生成温度，取值范围由服务和模型决定 |
| `max_tokens` | `4096` | 生成长度上限，由 Provider 映射到对应参数 |
| `timeout` | `60.0` | 传给 SDK 的单次请求超时，单位为秒 |
| `max_retries` | `3` | 首次请求失败后最多重试的次数。设为 `0` 可关闭重试 |
| `base_backoff` | `1.0` | 首次重试前等待的秒数。后续每次等待时间翻倍 |

## Agent.run()

`await agent.run(user_input, *, temperature=None, max_tokens=None, timeout=None)` 接受用户文本，返回助手回复 `str`。

- `run()` 中的 `None` 表示沿用 Agent 的对应配置。显式传值只覆盖当前一轮，例如 `await agent.run("用一句话回答", max_tokens=128)`。
- 构造 Agent 时将这些生成参数设为 `None`，Provider 会省略对应 SDK 参数。Messages 的 `max_tokens` 是必填参数，因此仍会传入默认值 `4096`。
- 成功后，当前用户消息和助手回复都会留在历史中。失败或取消时，在调用期间未从外部修改会话的前提下，本轮追加的用户消息会被移除。

## 会话历史

`agent.conversation.get_messages()` 返回当前会话的消息列表。它引用内部列表，修改它会直接影响后续请求。请等 `run()` 完成后再访问和修改会话。

`agent.conversation.clear_messages()` 会清除所有消息，包括构造时加入的系统提示词。若要以相同配置开始一段带系统提示词的新对话，可以新建一个 `Agent`。

## 异常

从 `skydoor.errors.exception` 导入异常类型。需要分别处理两种异常时，应先捕获 `LLMError`，它是 `AgentError` 的子类。

| 异常 | 触发条件或用途 |
| --- | --- |
| `AgentError` | 同一个 Agent 已有一轮 `run()` 在执行时，后发调用立即失败 |
| `LLMError` | Provider 报告调用失败、响应无有效文本或响应未正常结束。通过 `retryable` 和 `status_code` 读取重试标记及可用的 HTTP 状态码 |
| `ValueError` | 构造 Agent 时传入未识别的 `llm_api_type` |

内置 Provider 在请求超时、连接失败或识别到临时限流等故障时会标记 `retryable=True`。Agent 默认最多尝试四次，包含首次调用。认证错误、可识别的配额不足和输出截断通常需要调整配置或请求。

[会话、请求和 Provider](provider.md) · [Agent 源码](https://github.com/Rectangle518/skydoor/blob/main/src/skydoor/core/agent.py)
