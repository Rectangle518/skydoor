from typing import Any

from openai import AsyncOpenAI, OpenAIError

from ...core.context import LLMRequest, LLMResponse
from ...errors.exception import LLMError
from ._common import require_text
from ._openai import openai_error


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
        self.client = AsyncOpenAI(
            base_url=self.base_url, api_key=self.api_key, max_retries=0
        )

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

        try:
            resp = await self.client.chat.completions.create(**params)
        except OpenAIError as e:
            raise openai_error(e) from e

        choices = getattr(resp, "choices", None)
        if not isinstance(choices, list) or not choices:
            raise LLMError("Chat Completion 未返回候选回复")
        choice = choices[0]
        reason = getattr(choice, "finish_reason", None)
        if reason != "stop":
            message = {
                "length": "LLM 输出达到长度上限",
                "content_filter": "LLM 输出被内容过滤",
                "tool_calls": "当前不支持 LLM 工具调用",
                "function_call": "当前不支持 LLM 工具调用",
            }.get(
                reason if isinstance(reason, str) else "", "Chat Completion 未正常结束"
            )
            raise LLMError(message)
        message = getattr(choice, "message", None)
        if getattr(message, "refusal", None):
            raise LLMError("LLM 拒绝生成回复")
        content = require_text(getattr(message, "content", None))
        usage = getattr(resp, "usage", None)

        return LLMResponse(
            content=content,
            model=request.model,
            finish_reason=reason,
            usage=usage.total_tokens if usage is not None else None,
        )
