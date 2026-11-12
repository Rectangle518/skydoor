from typing import Any

from openai import AsyncOpenAI
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    ContentFilterFinishReasonError,
    InternalServerError,
    LengthFinishReasonError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    APITimeoutError,
    UnprocessableEntityError
)

from ...errors.exception import LLMError
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

        try:
            resp = await self.client.chat.completions.create(**params)

        # ========== 可重试 ==========
        except APITimeoutError as e:
            raise LLMError("LLM 请求超时", retryable=True) from e

        except APIConnectionError as e:
            raise LLMError("LLM 网络连接失败", retryable=True) from e

        except RateLimitError as e:
            # 429 里混着"限流"(可重试) 和 "余额/配额耗尽"(不可重试)
            code = getattr(e, "code", None) or ""
            balance_exhausted = code in (
                "insufficient_quota",
                "credit_balance_exhausted",
                "billing_hard_limit_reached",
            )
            raise LLMError(
                f"LLM 限流或配额不足: {code or e.message}",
                retryable=not balance_exhausted,
            ) from e

        except InternalServerError as e:
            # 5xx，SDK 已重试过，仍失败说明服务端持续异常，可再退避重试
            raise LLMError(f"LLM 服务端错误 {e.status_code}", retryable=True) from e

        # ========== 不可重试 ==========
        except AuthenticationError as e:
            raise LLMError("LLM 认证失败：API Key 无效或缺失", retryable=False) from e

        except PermissionDeniedError as e:
            raise LLMError("LLM 权限不足：无权访问该模型/资源", retryable=False) from e

        except BadRequestError as e:
            # 参数错误：重试没意义，通常是代码 bug
            raise LLMError(f"LLM 请求参数错误: {e.message}", retryable=False) from e

        except NotFoundError as e:
            raise LLMError(f"LLM 资源不存在（模型名/文件 ID 是否正确）: {e.message}",
                        retryable=False) from e

        except UnprocessableEntityError as e:
            raise LLMError(f"LLM 无法处理该请求: {e.message}", retryable=False) from e

        except ConflictError as e:
            raise LLMError(f"LLM 资源冲突: {e.message}", retryable=False) from e

        except (LengthFinishReasonError, ContentFilterFinishReasonError) as e:
            # 输出被截断/被安全过滤：换个 prompt 或调大 max_tokens 才能解决，不算瞬时错误
            raise LLMError(f"LLM 输出被中断: {e}", retryable=False) from e

        # ========== 兜底 ==========
        except APIStatusError as e:
            # 其他未单独列出的状态码；5xx 视为可重试，4xx 视为不可重试
            retryable = e.status_code >= 500
            raise LLMError(f"LLM API 状态错误 {e.status_code}: {e.message}",
                        retryable=retryable) from e

        except APIError as e:
            # SDK 其他内部错误（含响应校验失败等），保守起见不可重试
            raise LLMError(f"LLM SDK 异常: {e}", retryable=False) from e

        choice = resp.choices[0]

        return LLMResponse(
            content=choice.message.content or "",
            model=request.model,
            finish_reason=choice.finish_reason,
            usage=resp.usage.total_tokens if resp.usage is not None else None,
        )
