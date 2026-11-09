from typing import Any

from anthropic import AsyncAnthropic

from ...core.context import DEFAULT_MAX_TOKENS, LLMRequest, LLMResponse
from ._common import split_system_prompt


# Messages API
class MessagesProvider:
    """Anthropic Messages API（也兼容实现同一协议的服务）"""

    api_type = "messages"

    base_url: str
    api_key: str
    model: str
    client: AsyncAnthropic

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(base_url=self.base_url, api_key=self.api_key)

    async def complete(self, request: LLMRequest) -> LLMResponse:

        system, messages = split_system_prompt(request)

        params: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            # Messages API 的 max_tokens 是必填项，所以这里必须兜底一个默认值
            "max_tokens": (
                request.max_tokens
                if request.max_tokens is not None
                else DEFAULT_MAX_TOKENS
            ),
        }
        if system is not None:
            params["system"] = system
        if request.timeout is not None:
            params["timeout"] = request.timeout
        if request.temperature is not None:
            # 当前 SDK 的 messages.create 签名没有声明 temperature，
            # 但 Messages API 接受该字段，因此通过 extra_body 原样透传
            params["extra_body"] = {"temperature": request.temperature}

        resp = await self.client.messages.create(**params)

        content = "".join(block.text for block in resp.content if block.type == "text")
        usage = None
        if resp.usage is not None:
            usage = resp.usage.input_tokens + resp.usage.output_tokens

        return LLMResponse(
            content=content,
            model=request.model,
            finish_reason=resp.stop_reason,
            usage=usage,
        )
