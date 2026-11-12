# 模块分工

| 模块 | 职责 |
| --- | --- |
| [core/agent.py](https://github.com/Rectangle518/skydoor/blob/main/src/skydoor/core/agent.py) | 选择 Provider、编排单轮调用、管理会话和重试 |
| [core/context.py](https://github.com/Rectangle518/skydoor/blob/main/src/skydoor/core/context.py) 与 [core/message.py](https://github.com/Rectangle518/skydoor/blob/main/src/skydoor/core/message.py) | 定义会话、消息及统一的请求和响应对象 |
| [llm/provider.py](https://github.com/Rectangle518/skydoor/blob/main/src/skydoor/llm/provider.py) | 定义 Provider 协议 |
| [llm/providers/](https://github.com/Rectangle518/skydoor/tree/main/src/skydoor/llm/providers) | 映射协议参数、调用异步 SDK、转换响应和异常 |
| [errors/exception.py](https://github.com/Rectangle518/skydoor/blob/main/src/skydoor/errors/exception.py) | 定义框架异常、重试标记和 HTTP 状态码 |

接下来可以阅读[调用流程与重试](agent-run.md)，或直接查看 [Provider 参数映射](providers.md)。
