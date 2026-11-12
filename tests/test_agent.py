import asyncio
import logging
from unittest.mock import AsyncMock

import pytest

from skydoor.core.agent import Agent
from skydoor.core.context import LLMRequest, LLMResponse
from skydoor.core.message import Message
from skydoor.errors.exception import AgentError, LLMError
from skydoor.llm.providers.mock_provider import MockProvider


@pytest.fixture
def agent(monkeypatch: pytest.MonkeyPatch) -> Agent:
    monkeypatch.setattr(Agent, "_build_llm", lambda *args: MockProvider())
    return Agent("系统提示", model="mock-model", base_backoff=0)


def history(agent: Agent) -> list[tuple[str, str]]:
    return [(msg.role, msg.content) for msg in agent.conversation.get_messages()]


@pytest.mark.asyncio
async def test_history_and_single_call_overrides(agent: Agent, monkeypatch):
    calls = []
    complete = agent.llm.complete

    async def capture(request: LLMRequest) -> LLMResponse:
        calls.append(
            (
                [
                    (msg.role, msg.content)
                    for msg in request.conversation.get_messages()
                ],
                request.temperature,
                request.max_tokens,
                request.timeout,
            )
        )
        return await complete(request)

    monkeypatch.setattr(agent.llm, "complete", capture)
    assert (
        await agent.run("第一轮", temperature=0, max_tokens=12, timeout=3) == "Hello!"
    )
    assert await agent.run("第二轮") == "Hello!"
    assert calls == [
        ([("system", "系统提示"), ("user", "第一轮")], 0, 12, 3),
        (
            [
                ("system", "系统提示"),
                ("user", "第一轮"),
                ("assistant", "Hello!"),
                ("user", "第二轮"),
            ],
            agent.temperature,
            agent.max_tokens,
            agent.timeout,
        ),
    ]
    assert history(agent)[-2:] == [("user", "第二轮"), ("assistant", "Hello!")]


@pytest.mark.asyncio
@pytest.mark.parametrize("during_backoff", [False, True], ids=["request", "backoff"])
async def test_concurrent_run_is_rejected_and_cancelled_turn_rolls_back(
    agent: Agent, monkeypatch, during_backoff: bool
):
    started = asyncio.Event()
    release = asyncio.Event()
    await agent.run("已完成")
    original = history(agent)

    async def wait_here() -> None:
        started.set()
        await release.wait()

    async def block(request: LLMRequest) -> LLMResponse:
        if during_backoff:
            raise LLMError("临时失败", retryable=True)
        await wait_here()
        pytest.fail("等待响应的调用应被取消")

    async def backoff(delay: float) -> None:
        await wait_here()

    with monkeypatch.context() as patch:
        patch.setattr(agent.llm, "complete", block)
        if during_backoff:
            patch.setattr("skydoor.core.agent.asyncio.sleep", backoff)
        task = asyncio.create_task(agent.run("待取消"))
        try:
            await asyncio.wait_for(started.wait(), timeout=2)
            with pytest.raises(AgentError, match="正在执行") as caught:
                await agent.run("并发调用")
            assert not caught.value.retryable
            assert history(agent) == [*original, ("user", "待取消")]
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    assert history(agent) == original
    assert await agent.run("取消后继续") == "Hello!"


@pytest.mark.asyncio
async def test_rollback_does_not_pop_another_message(agent: Agent, monkeypatch):
    other_message = Message(role="user", content="外部加入")

    async def fail(request: LLMRequest) -> LLMResponse:
        request.conversation.add_message(other_message)
        raise RuntimeError("调用失败")

    with monkeypatch.context() as patch:
        patch.setattr(agent.llm, "complete", fail)
        with pytest.raises(RuntimeError, match="调用失败"):
            await agent.run("本轮输入")
    assert agent.conversation.get_messages()[-1] is other_message
    assert await agent.run("仍可调用") == "Hello!"


@pytest.mark.asyncio
async def test_retry_reuses_one_turn_and_logs_no_raw_error(
    agent: Agent, monkeypatch, caplog: pytest.LogCaptureFixture
):
    original_complete = agent.llm.complete
    attempts = []
    backoffs = []
    agent.base_backoff = 0.5

    async def sleep(delay: float) -> None:
        backoffs.append(delay)

    async def complete(request: LLMRequest) -> LLMResponse:
        attempts.append(history(agent))
        if len(attempts) < 3:
            raise LLMError("raw upstream detail", retryable=True, status_code=503)
        return await original_complete(request)

    monkeypatch.setattr("skydoor.core.agent.asyncio.sleep", sleep)
    monkeypatch.setattr(agent.llm, "complete", complete)
    with caplog.at_level(logging.WARNING):
        assert await agent.run("重试") == "Hello!"
    assert attempts == [[("system", "系统提示"), ("user", "重试")]] * 3
    assert backoffs == [0.5, 1.0]
    assert history(agent) == [
        ("system", "系统提示"),
        ("user", "重试"),
        ("assistant", "Hello!"),
    ]
    assert "503" in caplog.text
    assert "raw upstream detail" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("retryable", "max_retries", "expected_attempts"),
    [
        pytest.param([False], 3, 1, id="permanent"),
        pytest.param([True, False], 3, 2, id="permanent-after-retry"),
        pytest.param([True] * 4, 3, 4, id="exhausted"),
        pytest.param([True], 0, 1, id="retries-disabled"),
    ],
)
async def test_failed_turn_rolls_back(
    agent: Agent,
    monkeypatch,
    retryable: list[bool],
    max_retries: int,
    expected_attempts: int,
):
    agent.max_retries = max_retries
    await agent.run("已完成")
    original = history(agent)
    errors = [LLMError(f"失败 {i}", retryable=flag) for i, flag in enumerate(retryable)]
    complete = AsyncMock(side_effect=errors)

    with monkeypatch.context() as patch:
        patch.setattr(agent.llm, "complete", complete)
        with pytest.raises(LLMError) as caught:
            await agent.run("失败的调用")
    assert complete.await_count == expected_attempts
    assert caught.value is errors[-1]
    assert history(agent) == original
    assert await agent.run("失败后继续") == "Hello!"
