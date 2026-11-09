
from ...core.context import LLMResponse

class MockProvider:

    async def complete(self, request):
        return LLMResponse(
            content="Hello!",
            model="mock-model",
            finish_reason="stop",
            usage=None
        )