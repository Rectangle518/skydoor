
from .message import Message

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

    def __init__(self, conversation: Conversation, model: str, temperature: float | None = None, max_tokens: int | None = None, timeout: float | None = None):
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

    def __init__(self, content: str, model: str, finish_reason: str | None, usage: int | None = None):
        self.content = content
        self.model = model
        self.finish_reason = finish_reason
        self.usage = usage