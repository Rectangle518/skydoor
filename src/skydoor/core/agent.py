import asyncio
import logging
from typing import Literal

from ..errors.exception import AgentError, LLMError
from ..llm.provider import LLMProvider
from .context import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    Conversation,
    LLMRequest,
    LLMResponse,
)
from .message import Message

logger = logging.getLogger(__name__)

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
    max_retries: int
    base_backoff: float

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
        max_retries: int = 3,
        base_backoff: float = 1.0,
    ) -> None:

        self.conversation = Conversation()
        self.llm = self._build_llm(llm_api_type, base_url, api_key, model)
        self.model = model
        self.llm_api_type = llm_api_type
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries  # 重试次数上限（不含首次）
        self.base_backoff = base_backoff  # 指数退避基准秒数
        self._running = False

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
        同一实例已有调用正在执行时，抛出 AgentError。
        """
        if self._running:
            raise AgentError("同一 Agent 正在执行 run()，请等待本轮结束")

        conversation = self.conversation
        user_message = Message(role="user", content=user_input)
        succeeded = False
        self._running = True
        try:
            conversation.add_message(user_message)
            llm_request = LLMRequest(
                conversation=conversation,
                model=self.model,
                temperature=self.temperature if temperature is None else temperature,
                max_tokens=self.max_tokens if max_tokens is None else max_tokens,
                timeout=self.timeout if timeout is None else timeout,
            )

            try:
                llm_response = await self.llm.complete(llm_request)
            except LLMError as e:
                if not e.retryable:
                    raise
                # 重试；_retry 内部失败时会抛出最后一次的 LLMError
                llm_response = await self._retry(llm_request, last_error=e)

            conversation.add_message(
                Message(role="assistant", content=llm_response.content)
            )
            succeeded = True
            return llm_response.content
        finally:
            try:
                if not succeeded:
                    # 调用被取消时也执行回滚；仅弹出本轮添加的消息。
                    messages = conversation.get_messages()
                    if messages and messages[-1] is user_message:
                        conversation.pop_last_message()
            finally:
                self._running = False

    async def _retry(
        self, llm_request: LLMRequest, *, last_error: LLMError
    ) -> LLMResponse:
        """对可重试错误做指数退避重试，成功返回响应，耗尽则抛出最后的异常"""
        error = last_error

        for attempt in range(1, self.max_retries + 1):
            backoff = self.base_backoff * (2 ** (attempt - 1))  # 1s, 2s, 4s...
            logger.warning(
                "LLM 调用失败（%s，HTTP 状态码 %s），第 %d/%d 次重试，%.1fs 后开始",
                type(error.__cause__ or error).__name__,
                error.status_code,
                attempt,
                self.max_retries,
                backoff,
            )
            await asyncio.sleep(backoff)

            try:
                return await self.llm.complete(llm_request)
            except LLMError as e:
                if not e.retryable:
                    # 重试过程中变成不可重试错误，立即放弃
                    raise
                error = e
                # 继续下一轮

        # 重试耗尽：抛出最后一次异常，保留原始 cause 链
        logger.error("LLM 调用在 %d 次重试后仍失败", self.max_retries)
        raise error
