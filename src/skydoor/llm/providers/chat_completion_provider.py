from typing import Protocol
from openai import AsyncOpenAI

from ...core.message import Message
from ...core.context import LLMRequest, LLMResponse

# Chat Completion API
class ChatCompletionProvider:

    base_url: str
    api_key: str
    model: str
    api_type: str = "chat_completion"
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

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        choice = resp.choices[0]

        return LLMResponse(
            content=choice.message.content or "",
            model=self.model,
            finish_reason=choice.finish_reason
        )