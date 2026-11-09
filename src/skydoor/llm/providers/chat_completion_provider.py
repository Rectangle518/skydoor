from typing import Any

from openai import AsyncOpenAI

from ...core.context import LLMRequest, LLMResponse


# Chat Completion API
class ChatCompletionProvider:
    api_type = "chat_completion"

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

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation.get_messages()
        ]

        # 只把调用方明确给出的参数发给服务端；None 表示使用服务端默认值
        params: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
        }
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens
        if request.timeout is not None:
            params["timeout"] = request.timeout

        resp = await self.client.chat.completions.create(**params)

        choice = resp.choices[0]

        return LLMResponse(
            content=choice.message.content or "",
            model=request.model,
            finish_reason=choice.finish_reason,
            usage=resp.usage.total_tokens if resp.usage is not None else None,
        )
