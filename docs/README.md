# Skydoor 文档

Skydoor 是一个 Python 异步文本对话框架。它通过统一的 `Agent` 接口调用 Chat Completion、Anthropic Messages 或 OpenAI Responses，并在内存中保留多轮对话历史。

| 文档 | 内容 |
| --- | --- |
| [快速上手](guide/README.md) | 安装项目、配置模型服务、运行两轮对话和排查常见问题 |
| [API 参考](api_ref/README.md) | `Agent` 的构造参数、单次调用覆盖、会话管理和异常 |
| [会话、请求和 Provider](api_ref/provider.md) | 消息与请求/响应模型、Provider 协议和离线示例 |
| [源码解读](source_code/README.md) | 一次 `run()` 如何组装历史、调用 Provider、重试和回滚 |

当前版本支持非流式文本对话。工具调用和自主多步执行仍在规划中。

[项目仓库](https://github.com/Rectangle518/skydoor)
