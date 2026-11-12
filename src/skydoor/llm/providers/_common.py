from ...core.context import LLMRequest
from ...errors.exception import LLMError


def require_text(content: object) -> str:
    if not isinstance(content, str) or not content.strip():
        raise LLMError("LLM 未返回有效文本")
    return content


def http_error(status_code: int, *codes: str | None) -> LLMError:
    # 兼容网关可能用 429 表示配额耗尽；以机器可读的代码区分。
    quota_codes = (
        "insufficient_quota",
        "credit_balance_exhausted",
        "billing_hard_limit_reached",
        "billing_error",
        "billing_frozen",
    )
    if status_code == 402 or any(code in quota_codes for code in codes):
        message = "LLM 余额或配额不足"
        retryable = False
    elif status_code == 429:
        message = "LLM 请求频率受限"
        retryable = True
    elif status_code == 408:
        message = "LLM 请求超时"
        retryable = True
    elif status_code in (500, 502, 503, 504, 529):
        message = "LLM 服务暂时不可用"
        retryable = True
    else:
        message = {
            400: "LLM 请求参数错误",
            401: "LLM 认证失败",
            403: "LLM 权限不足",
            404: "LLM 资源不存在",
            409: "LLM 资源冲突",
            422: "LLM 无法处理该请求",
        }.get(status_code, "LLM API 状态错误")
        retryable = False

    return LLMError(
        f"{message}（HTTP {status_code}）",
        retryable=retryable,
        status_code=status_code,
    )


def split_system_prompt(
    request: LLMRequest,
) -> tuple[str | None, list[dict[str, str]]]:
    """把 system 消息单独拆出来

    Messages / Responses API 不把 system 当作普通对话消息，而是用独立参数接收，
    因此这里返回 (system 文本, 其余消息列表)。如果有多条 system 消息，按顺序拼接
    """
    system_parts: list[str] = []
    messages: list[dict[str, str]] = []

    for message in request.conversation.get_messages():
        if message.role == "system":
            system_parts.append(message.content)
        else:
            messages.append({"role": message.role, "content": message.content})

    system = "\n\n".join(system_parts) if system_parts else None
    return system, messages
