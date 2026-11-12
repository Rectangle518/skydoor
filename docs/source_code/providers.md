# Provider 参数映射

Skydoor 将统一请求转换成各协议所需的字段。

| 统一请求中的数据 | Chat Completion | Messages | Responses |
| --- | --- | --- | --- |
| 普通对话消息 | `messages` | `messages` | `input` |
| 系统消息 | 保留在 `messages` 中 | 拆到 `system` | 拆到 `instructions` |
| `max_tokens` | `max_tokens` | `max_tokens`，值为空时回退到 `4096` | `max_output_tokens` |
| `temperature` | `temperature` | 通过 SDK 的 `extra_body` 传入 | `temperature` |

Messages 和 Responses 共用系统消息拆分逻辑。遇到多条系统消息时，按原顺序用空行拼接，并保留其他消息的相对顺序。

参见 [Provider API](../api_ref/provider.md)。
