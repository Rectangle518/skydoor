
# git commits 记录


## v0.1.0

feat: 实现基本的 LLM 调用和对话历史组装

```
src/skydoor/
├── core/
│   ├── message.py      Message(role, content)，role 限 system/user/assistant
│   ├── context.py      Conversation / LLMRequest / LLMResponse
│   └── agent.py        Agent：组装对话、调 provider、回写 assistant
├── llm/
│   ├── provider.py     LLMProvider Protocol（complete(request) -> response）
│   └── providers/
│       ├── chat_completion_provider.py   唯一可用实现（OpenAI Chat Completion API）
│       ├── messages_provider.py          空壳（Anthropic Messages API 预留）
│       ├── responses_provider.py         空壳（OpenAI Responses API 预留）
│       └── mock_provider.py              返回固定 "Hello!"
├── errors/             空 __init__
├── utils/              空 __init__
└── py.typed

examples/basic_chat.py  两段用法示例
```


## v0.1.1

fix: 修复 `Agent` 的 `__init__` 方法，同时完善了 `temperature`、`max_tokens`、`timeout` 参数

feat: 实现了 messages_provider 和 responses_provider


## v0.1.2

feat: 完善了异常处理机制

在 `chat_completion_provider.py` 中，捕获了 openai 客户端可能抛出的各种异常，区分是否可重试，然后包装成当前项目的 `LLMError` 抛出。

在 `Agent` 中，捕获了 `LLMError`，并记录了错误日志，针对可重试的异常进行“指数退避重试”，同时返回了错误信息给用户。