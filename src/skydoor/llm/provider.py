from typing import Protocol

from ..core.context import LLMRequest, LLMResponse


class LLMProvider(Protocol):
    """所有 Provider 需要满足的接口"""

    model: str
    api_type: str

    async def complete(self, request: LLMRequest) -> LLMResponse: ...
