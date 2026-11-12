from typing import Any

from openai import AsyncOpenAI, OpenAIError

from ...core.context import LLMRequest, LLMResponse
from ...errors.exception import LLMError
from ._common import require_text, split_system_prompt
from ._openai import openai_error


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
        self.client = AsyncOpenAI(
            base_url=self.base_url, api_key=self.api_key, max_retries=0
        )

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

        try:
            resp = await self.client.responses.create(**params)
        except OpenAIError as e:
            raise openai_error(e) from e

        status = getattr(resp, "status", None)
        if status == "incomplete":
            details = getattr(resp, "incomplete_details", None)
            reason = getattr(details, "reason", None)
            if reason in ("max_output_tokens", "max_messages"):
                raise LLMError("LLM 输出达到长度上限")
            if reason == "content_filter":
                raise LLMError("LLM 输出被内容过滤")
            raise LLMError("Responses 输出未完成")
        if status == "failed":
            error = getattr(resp, "error", None)
            code = getattr(error, "code", None)
            if code == "rate_limit_exceeded":
                raise LLMError("LLM 请求频率受限", retryable=True)
            if code in ("server_error", "vector_store_timeout"):
                raise LLMError("LLM 服务暂时不可用", retryable=True)
            raise LLMError("Responses 生成回复失败")
        if status != "completed":
            raise LLMError("Responses 未正常结束")

        try:
            output_text = resp.output_text
        except (AttributeError, TypeError) as e:
            raise LLMError("Responses 输出格式错误") from e
        content = require_text(output_text)
        usage = getattr(resp, "usage", None)

        return LLMResponse(
            content=content,
            model=request.model,
            finish_reason="stop",
            usage=usage.total_tokens if usage is not None else None,
        )
