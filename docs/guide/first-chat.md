# 运行两轮对话

先完成[安装与配置](README.md)，然后在项目根目录运行示例。

```powershell
uv run ./examples/basic_chat.py
```

示例先在第一轮告诉模型一个名字，再在第二轮询问这个名字。两次 `await agent.run(...)` 使用同一个 `Agent`，第二次请求会携带上一轮对话。命令会向配置的服务发起真实请求。

同一个 `Agent` 的调用需要逐轮等待。开始新对话时，可以新建一个 `Agent`，让它拥有独立的会话历史。详情见 [Agent API](../api_ref/README.md)。

## 离线验证

以下测试使用 Mock Provider 或 SDK 模拟对象，可以在没有模型密钥时运行。

```powershell
uv run pytest
```

如果只想调用一次本地 Provider，可以运行 [MockProvider 示例](../api_ref/provider.md)。

遇到错误时，见[常见问题](troubleshooting.md)。
