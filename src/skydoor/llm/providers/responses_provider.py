from typing import Any

from openai import AsyncOpenAI

from ...core.context import LLMRequest, LLMResponse
from ._common import split_system_prompt


# Responses API
class ResponsesProvider:
    """OpenAI Responses API。"""

    api_type = "responses"

    base_url: str
    api_key: str
    model: str
    client: AsyncOpenAI

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)

    async def complete(self, request: LLMRequest) -> LLMResponse:

        instructions, messages = split_system_prompt(request)

        # Responses API 用 instructions 接收 system prompt，
        # 用 input 接收对话消息，max_tokens 对应 max_output_tokens
        params: dict[str, Any] = {
            "model": request.model,
            "input": messages,
        }
        if instructions is not None:
            params["instructions"] = instructions
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.max_tokens is not None:
            params["max_output_tokens"] = request.max_tokens
        if request.timeout is not None:
            params["timeout"] = request.timeout

        resp = await self.client.responses.create(**params)

        # Responses API 的 status 取值是 completed / incomplete / failed 等，
        # 这里把 completed 归一化成和 Chat Completion 一致的 "stop"
        status = getattr(resp, "status", None)
        finish_reason = "stop" if status == "completed" else status

        return LLMResponse(
            content=resp.output_text or "",
            model=request.model,
            finish_reason=finish_reason,
            usage=resp.usage.total_tokens if resp.usage is not None else None,
        )
