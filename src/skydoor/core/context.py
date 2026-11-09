from .message import Message

# LLMRequest 的默认生成参数
# 这些值只是“框架层的建议默认值”，调用方可以在构造 Agent、创建 LLMRequest
# 或单次 run() 时覆盖；显式传 None 表示不发送该参数，交给服务端使用自己的默认值
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TIMEOUT = 60.0


class Conversation:
    messages: list[Message]

    def __init__(self):
        self.messages = []

    def add_message(self, message: Message):
        self.messages.append(message)

    def get_messages(self):
        return self.messages

    def clear_messages(self):
        self.messages.clear()

    def __str__(self):
        return "\n".join(str(message) for message in self.messages)


class LLMRequest:
    conversation: Conversation
    model: str
    temperature: float | None
    max_tokens: int | None
    timeout: float | None

    def __init__(
        self,
        conversation: Conversation,
        model: str,
        temperature: float | None = DEFAULT_TEMPERATURE,
        max_tokens: int | None = DEFAULT_MAX_TOKENS,
        timeout: float | None = DEFAULT_TIMEOUT,
    ):
        self.conversation = conversation
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout


class LLMResponse:
    content: str
    model: str
    finish_reason: str | None
    usage: int | None

    def __init__(
        self,
        content: str,
        model: str,
        finish_reason: str | None,
        usage: int | None = None,
    ):
        self.content = content
        self.model = model
        self.finish_reason = finish_reason
        self.usage = usage
