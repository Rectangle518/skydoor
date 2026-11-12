from typing import Any

from anthropic import (
    AnthropicError,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncAnthropic,
    DeadlineExceededError,
)

from ...core.context import DEFAULT_MAX_TOKENS, LLMRequest, LLMResponse
from ...errors.exception import LLMError
from ._common import http_error, require_text, split_system_prompt


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
        self.client = AsyncAnthropic(
            base_url=self.base_url, api_key=self.api_key, max_retries=0
        )

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

        try:
            resp = await self.client.messages.create(**params)
        except (APITimeoutError, DeadlineExceededError) as e:
            raise LLMError("LLM 请求超时", retryable=True) from e
        except APIConnectionError as e:
            raise LLMError("LLM 网络连接失败", retryable=True) from e
        except APIStatusError as e:
            body = e.body
            details = body.get("error") if isinstance(body, dict) else None
            gateway_code = details.get("code") if isinstance(details, dict) else None
            raise http_error(e.status_code, e.error_code, e.type, gateway_code) from e
        except AnthropicError as e:
            raise LLMError("LLM SDK 调用失败") from e

        reason = getattr(resp, "stop_reason", None)
        if reason not in ("end_turn", "stop_sequence"):
            message = {
                "max_tokens": "LLM 输出达到长度上限",
                "model_context_window_exceeded": "LLM 输出达到上下文长度上限",
                "refusal": "LLM 拒绝生成回复",
                "tool_use": "当前不支持 LLM 工具调用",
            }.get(reason if isinstance(reason, str) else "", "Messages 未正常结束")
            raise LLMError(message)
        blocks = getattr(resp, "content", None)
        if not isinstance(blocks, list):
            raise LLMError("Messages 响应缺少有效的内容块")
        text_parts: list[str] = []
        for block in blocks:
            if getattr(block, "type", None) == "text":
                text = getattr(block, "text", None)
                if not isinstance(text, str):
                    raise LLMError("Messages 文本块格式错误")
                text_parts.append(text)
        content = require_text("".join(text_parts))
        token_usage = getattr(resp, "usage", None)
        usage = (
            token_usage.input_tokens + token_usage.output_tokens
            if token_usage is not None
            else None
        )

        return LLMResponse(
            content=content,
            model=request.model,
            finish_reason=reason,
            usage=usage,
        )
