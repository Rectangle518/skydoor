# 会话、请求和 Provider

## 消息与会话

| 类型 | 导入位置 | 接口 |
| --- | --- | --- |
| `Message` | `skydoor.core.message` | `Message(role, content)`。角色为 `system`、`user` 或 `assistant`，内容为字符串 |
| `Conversation` | `skydoor.core.context` | `add_message(message)` 追加消息，`get_messages()` 读取内部列表，`pop_last_message()` 弹出末条消息（空列表时返回 `None`），`clear_messages()` 清空会话 |

## LLMRequest 与 LLMResponse

两者均从 `skydoor.core.context` 导入。

- `LLMRequest(conversation, model, temperature=0.7, max_tokens=4096, timeout=60.0)` 保存会话、模型和生成参数。它直接引用传入的会话对象。
- `LLMResponse(content, model, finish_reason, usage=None)` 保存回复文本、模型、结束原因和可用的 token 用量。结束原因随 Provider 而异，`usage` 是 Provider 填入的 token 计数，缺失时为 `None`。

`Agent.run()` 返回 `LLMResponse.content`。直接调用 Provider 可以读取完整的 `LLMResponse`。

## LLMProvider

`skydoor.llm.provider.LLMProvider` 是一个结构化类型协议。实现需要提供 `model: str`、`api_type: str`，以及 `async def complete(self, request: LLMRequest) -> LLMResponse`。

| 实现 | 模块 | 协议 |
| --- | --- | --- |
| `ChatCompletionProvider` | `skydoor.llm.providers.chat_completion_provider` | `chat_completion` |
| `MessagesProvider` | `skydoor.llm.providers.messages_provider` | `messages` |
| `ResponsesProvider` | `skydoor.llm.providers.responses_provider` | `responses` |
| `MockProvider` | `skydoor.llm.providers.mock_provider` | 返回固定文本的本地测试实现 |

三个真实 Provider 都接受 `base_url`、`api_key` 和 `model` 作为构造参数，并使用 `request.model` 组装请求。接入自定义实现时，可以通过统一协议直接调用它。目前 `Agent` 的构造函数按固定的 `llm_api_type` 列表选择 Provider。

## MockProvider 示例

把下面代码保存为项目根目录下的 `mock_chat.py`，然后执行 `uv run ./mock_chat.py`。它会在本地输出 `你好，Skydoor！`。

```python
import asyncio

from skydoor.core.context import Conversation, LLMRequest
from skydoor.core.message import Message
from skydoor.llm.providers.mock_provider import MockProvider


async def main() -> None:
    provider = MockProvider(content="你好，Skydoor！")
    conversation = Conversation()
    conversation.add_message(Message(role="user", content="打个招呼"))
    response = await provider.complete(
        LLMRequest(conversation=conversation, model=provider.model)
    )
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
```

[返回 Agent API](README.md) · [查看 Provider 的参数映射](../source_code/providers.md)
