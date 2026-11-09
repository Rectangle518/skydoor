from ...core.context import LLMRequest


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
