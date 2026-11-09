from skydoor.core.agent import Agent
import asyncio

# 用法一
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


# 用法二：主流用法，推荐
agent_2 = Agent(
    base_url="https://api.agnes-ai.cn/v1",
    api_key="sk-xYln9a5uknt3GxwgKawmzdsoRTOR4SM9TGqT4XLWMvIYI5Mv",
    model="agnes-3.0-flash",
    system_prompt="You are a helpful assistant.",
    llm_api_type="chat_completion",
)

async def run_agent():

    response_2 = await agent_2.run("Hello, I am Yuyang. My friend is Kanghao.")
    print(response_2, end="\n\n")

    response_2 = await agent_2.run("Who is my friend?")
    print(response_2, end="\n\n")

if __name__ == "__main__":
    asyncio.run(run_agent())