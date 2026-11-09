from ...core.context import LLMRequest, LLMResponse


class MockProvider:
    """本地测试用的假 Provider，不发起任何网络请求"""

    api_type = "chat_completion"

    def __init__(self, model: str = "mock-model", content: str = "Hello!"):
        self.model = model
        self.content = content

    async def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=self.content,
            model=request.model,
            finish_reason="stop",
            usage=None,
        )
