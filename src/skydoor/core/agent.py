from typing import Literal

from ..core.context import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    Conversation,
    LLMRequest,
)
from ..core.message import Message
from ..llm.provider import LLMProvider

ApiType = Literal["chat_completion", "messages", "responses"]


class Agent:
    conversation: Conversation
    llm: LLMProvider
    model: str
    llm_api_type: ApiType
    system_prompt: str
    temperature: float | None
    max_tokens: int | None
    timeout: float | None

    def __init__(
        self,
        system_prompt: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        llm_api_type: ApiType = "chat_completion",
        temperature: float | None = DEFAULT_TEMPERATURE,
        max_tokens: int | None = DEFAULT_MAX_TOKENS,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> None:

        self.conversation = Conversation()
        self.llm = self._build_llm(llm_api_type, base_url, api_key, model)
        self.model = model
        self.llm_api_type = llm_api_type
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        self.conversation.add_message(
            Message(role="system", content=self.system_prompt)
        )

    @staticmethod
    def _build_llm(
        llm_api_type: ApiType,
        base_url: str,
        api_key: str,
        model: str,
    ) -> LLMProvider:
        if llm_api_type == "chat_completion":
            from ..llm.providers.chat_completion_provider import ChatCompletionProvider

            return ChatCompletionProvider(
                base_url=base_url, api_key=api_key, model=model
            )
        if llm_api_type == "messages":
            from ..llm.providers.messages_provider import MessagesProvider

            return MessagesProvider(base_url=base_url, api_key=api_key, model=model)
        if llm_api_type == "responses":
            from ..llm.providers.responses_provider import ResponsesProvider

            return ResponsesProvider(base_url=base_url, api_key=api_key, model=model)

        raise ValueError(f"Unsupported llm_api_type: {llm_api_type!r}")

    async def run(
        self,
        user_input: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> str:
        """发送一条用户消息并返回助手回复

        三个参数传 None 时沿用 Agent 构造时的默认值；显式传值则只影响本次调用
        """

        # 1. 添加用户消息
        self.conversation.add_message(Message(role="user", content=user_input))

        # 2. 构建 LLMRequest
        llm_request = LLMRequest(
            conversation=self.conversation,
            model=self.model,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
            timeout=self.timeout if timeout is None else timeout,
        )

        # 3. 调用 Provider
        llm_response = await self.llm.complete(llm_request)

        # 4. 添加 assistant 消息
        self.conversation.add_message(
            Message(role="assistant", content=llm_response.content)
        )

        # 5. 返回响应
        return llm_response.content
