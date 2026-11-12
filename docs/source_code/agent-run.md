# 调用流程与重试

## 一次 run() 如何执行

1. 检查当前实例是否已有一轮正在执行。有则抛出 `AgentError`，否则标记当前轮正在运行。
2. 把用户消息追加到现有会话。用该会话、模型和本轮有效的生成参数构造 `LLMRequest`。
3. 等待 `Provider.complete(request)`。Provider 把请求转换为对应的 SDK 参数，并把成功响应转换为 `LLMResponse`。
4. 追加助手消息并返回回复文本。若请求失败或任务取消，`finally` 会检查历史末尾是否仍为本轮追加的用户消息，是则将其弹出。最后释放运行标记。

请求引用同一个会话对象，因此 Provider 能读取系统提示词和此前完成的轮次。回滚依赖本轮消息仍位于列表末尾，这也是调用期间应避免从外部修改会话的原因。

## 重试与失败回滚

内置 Provider 关闭 SDK 自带的重试，由 Agent 统一决定重试。Provider 将识别到的 SDK 异常转换为 `LLMError`，并用异常链保留原始原因。只有带 `retryable=True` 的 `LLMError` 才会进入 Agent 的重试流程。

每次重试复用同一个 `LLMRequest`，本轮用户消息只追加一次。默认三次重试前分别等待 1、2、4 秒。重试期间遇到不可重试错误会立即退出，尝试耗尽则抛出最后一次异常。任务在请求或退避期间被取消，也会执行本轮回滚。

可以对照 [Agent 测试](https://github.com/Rectangle518/skydoor/blob/main/tests/test_agent.py) 阅读会话、重试与取消行为，再看 [Provider 测试](https://github.com/Rectangle518/skydoor/blob/main/tests/test_providers.py) 中的参数映射和响应解析用例。
