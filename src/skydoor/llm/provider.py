from typing import Protocol
from ..core.context import LLMRequest, LLMResponse

class LLMProvider(Protocol):

    async def complete(
        self,
        request: LLMRequest
    ) -> LLMResponse:
        pass