
from typing import Literal

from ..core.context import Conversation, LLMRequest, LLMResponse
from ..core.message import Message
from ..llm.provider import LLMProvider

class Agent:
    conversation: Conversation
    llm: LLMProvider
    llm_api_type: Literal["chat_completion", "messages", "responses"] = "chat_completion"
    system_prompt: str

    def __init__(self, llm: LLMProvider, system_prompt: str):

        self.conversation = Conversation()
        self.llm = llm
        self.llm_api_type = llm.api_type
        self.system_prompt = system_prompt

        self.conversation.add_message(Message(role="system", content=self.system_prompt))

    def __init__(self, base_url: str, api_key: str, model: str, system_prompt: str, llm_api_type: Literal["chat_completion", "messages", "responses"] = "chat_completion"):

        self.conversation = Conversation()

        if llm_api_type == "chat_completion":
            from ..llm.providers.chat_completion_provider import ChatCompletionProvider
            self.llm = ChatCompletionProvider(base_url=base_url, api_key=api_key, model=model)
        elif llm_api_type == "messages":
            from ..llm.providers.messages_provider import MessagesProvider
            self.llm = MessagesProvider(base_url=base_url, api_key=api_key, model=model)
        elif llm_api_type == "responses":
            from ..llm.providers.responses_provider import ResponsesProvider
            self.llm = ResponsesProvider(base_url=base_url, api_key=api_key, model=model)
        
        self.llm_api_type = llm_api_type
        self.system_prompt = system_prompt

        self.conversation.add_message(Message(role="system", content=self.system_prompt))

    async def run(self, user_input: str):

        # 1. 添加用户消息
        self.conversation.add_message(Message(role="user", content=user_input))

        # 2. 构建 LLMRequest
        llm_request = LLMRequest(
            conversation=self.conversation,
            model=self.llm.model,
        )

        # 3. 调用 Provider
        llm_response = await self.llm.complete(llm_request)


        # 4. 添加 assistant 消息
        self.conversation.add_message(Message(role="assistant", content=llm_response.content))

        # 调试：打印对话历史
        # print(self.conversation, end="\n\n")

        # 5. 返回响应
        return llm_response.content

        

