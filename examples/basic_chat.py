from skydoor.core.agent import Agent

from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

# 用法一：已废弃

# from skydoor.llm.providers.chat_completion_provider import ChatCompletionProvider

# llm_1 = ChatCompletionProvider(
#     base_url="",
#     api_key="",
#     model="",
# )

# agent_1 = Agent(
#     llm=llm_1,
#     system_prompt="You are a helpful assistant.",
# )

# response_1 = agent_1.run("Hello, how are you?")

# print(response_1)


# 用法二：目前支持的用法

agent_2 = Agent(
    base_url=os.getenv("AGNES_BASE_URL"),
    api_key=os.getenv("AGNES_API_KEY"),
    model=os.getenv("AGNES_MODEL"),
    system_prompt="You are a helpful assistant.",
    llm_api_type="chat_completion",
    temperature=0.9,
    max_tokens=1024,
    timeout=60
)

async def run_agent():

    response_2 = await agent_2.run("Hello, I am Yuyang. My friend is Kanghao.")
    print(response_2, end="\n\n")

    response_2 = await agent_2.run("Who is my friend?")
    print(response_2, end="\n\n")

if __name__ == "__main__":
    asyncio.run(run_agent())