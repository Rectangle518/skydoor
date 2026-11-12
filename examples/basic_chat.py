import asyncio
import os
import sys

from dotenv import load_dotenv

from skydoor.core.agent import Agent
from skydoor.errors.exception import LLMError


async def run_agent() -> None:
    load_dotenv()
    agent = Agent(
        base_url=os.getenv("AGNES_BASE_URL"),
        api_key=os.getenv("AGNES_API_KEY"),
        model=os.getenv("AGNES_MODEL"),
        system_prompt="You are a helpful assistant.",
        llm_api_type="chat_completion",
        temperature=0.9,
        max_tokens=1024,
        timeout=60,
    )

    # 同一 Agent 需要等待上一轮完成后再开始下一轮。
    print(await agent.run("Hello, I am Yuyang. My friend is Kanghao."), end="\n\n")
    print(await agent.run("Who is my friend?"), end="\n\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except LLMError as error:
        print(f"对话失败：{error}", file=sys.stderr)
        raise SystemExit(1) from None
