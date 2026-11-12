from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import anthropic
import httpx2
import openai
import pytest

from skydoor.core.agent import Agent
from skydoor.errors.exception import LLMError


@pytest.fixture
def make_agent(monkeypatch):
    def build(api_type, *, response=None, error=None, **options):
        create = AsyncMock(return_value=response, side_effect=error)
        if api_type == "messages":
            sdk_name = "AsyncAnthropic"
            client = NS(messages=NS(create=create))
        else:
            sdk_name = "AsyncOpenAI"
            client = NS(
                chat=NS(completions=NS(create=create)), responses=NS(create=create)
            )
        factory = Mock(return_value=client)
        monkeypatch.setattr(
            f"skydoor.llm.providers.{api_type}_provider.{sdk_name}", factory
        )
        agent = Agent(
            "系统指令",
            base_url="https://example.invalid",
            api_key="test-key",
            model="mock-model",
            llm_api_type=api_type,
            base_backoff=0,
            **options,
        )
        factory.assert_called_once_with(
            base_url="https://example.invalid", api_key="test-key", max_retries=0
        )
        return agent, create

    return build


def chat_reply(text, *, finish="stop", refusal=None):
    return NS(
        choices=[NS(finish_reason=finish, message=NS(content=text, refusal=refusal))],
        usage=NS(total_tokens=9),
    )


def messages_reply(*blocks, stop="end_turn"):
    return NS(
        stop_reason=stop,
        content=list(blocks),
        usage=NS(input_tokens=7, output_tokens=2),
    )


def responses_reply(text, *, status="completed", reason=None, code=None):
    return NS(
        status=status,
        output_text=text,
        incomplete_details=NS(reason=reason) if reason else None,
        error=NS(code=code) if code else None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("api_type", "response", "history_key", "system_key", "tokens_key"),
    [
        ("chat_completion", chat_reply(" 回复 "), "messages", None, "max_tokens"),
        (
            "messages",
            messages_reply(
                NS(type="thinking"),
                NS(type="text", text=" 回"),
                NS(type="text", text="复 "),
                stop="stop_sequence",
            ),
            "messages",
            "system",
            "max_tokens",
        ),
        (
            "responses",
            responses_reply(" 回复 "),
            "input",
            "instructions",
            "max_output_tokens",
        ),
    ],
)
async def test_params_and_success(
    make_agent, api_type, response, history_key, system_key, tokens_key
):
    agent, create = make_agent(
        api_type, response=response, temperature=None, max_tokens=None, timeout=None
    )
    assert await agent.run("第一个问题") == " 回复 "
    assert (
        await agent.run("第二个问题", temperature=0, max_tokens=12, timeout=3)
        == " 回复 "
    )
    first, second = [call.kwargs for call in create.await_args_list]
    system = {"role": "system", "content": "系统指令"}
    first_user = {"role": "user", "content": "第一个问题"}
    first_history = [first_user] if system_key else [system, first_user]
    expected = {"model": "mock-model"}
    if system_key:
        expected[system_key] = "系统指令"
    assert first == {
        **expected,
        history_key: first_history,
        **({"max_tokens": 4096} if api_type == "messages" else {}),
    }
    assert second == {
        **expected,
        history_key: [
            *first_history,
            {"role": "assistant", "content": " 回复 "},
            {"role": "user", "content": "第二个问题"},
        ],
        tokens_key: 12,
        "timeout": 3,
        **(
            {"extra_body": {"temperature": 0}}
            if api_type == "messages"
            else {"temperature": 0}
        ),
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("api_type", "response", "message"),
    [
        pytest.param("chat_completion", NS(choices=[]), "候选", id="no-choices"),
        pytest.param(
            "chat_completion", chat_reply(None), "有效文本", id="chat-null-text"
        ),
        pytest.param(
            "chat_completion",
            chat_reply("部分", finish="length"),
            "长度",
            id="chat-truncated",
        ),
        pytest.param(
            "chat_completion",
            chat_reply("部分", finish="content_filter"),
            "过滤",
            id="chat-filter",
        ),
        pytest.param(
            "chat_completion",
            chat_reply("部分", refusal="reason"),
            "拒绝",
            id="chat-refusal",
        ),
        pytest.param(
            "chat_completion",
            chat_reply("部分", finish="tool_calls"),
            "工具",
            id="chat-tool",
        ),
        pytest.param(
            "messages",
            messages_reply(NS(type="thinking")),
            "有效文本",
            id="messages-no-text",
        ),
        pytest.param(
            "messages",
            messages_reply(NS(type="text", text="部分"), stop="max_tokens"),
            "长度",
            id="messages-truncated",
        ),
        pytest.param(
            "messages",
            messages_reply(NS(type="tool_use"), stop="tool_use"),
            "工具",
            id="messages-tool",
        ),
        pytest.param(
            "messages",
            messages_reply(NS(type="text", text="部分"), stop="pause_turn"),
            "未正常结束",
            id="messages-paused",
        ),
        pytest.param(
            "responses", responses_reply(" \t"), "有效文本", id="responses-blank"
        ),
        pytest.param(
            "responses",
            responses_reply("部分", status="incomplete", reason="max_output_tokens"),
            "长度",
            id="responses-truncated",
        ),
        pytest.param(
            "responses",
            responses_reply("", status="failed", code="invalid_prompt"),
            "失败",
            id="responses-failed",
        ),
        pytest.param(
            "responses",
            responses_reply("部分", status="in_progress"),
            "未正常结束",
            id="responses-in-progress",
        ),
        pytest.param(
            "responses",
            responses_reply("部分", status="cancelled"),
            "未正常结束",
            id="responses-cancelled",
        ),
    ],
)
async def test_rejected_response_rolls_back_without_retry(
    make_agent, api_type, response, message
):
    agent, create = make_agent(api_type, response=response)
    with pytest.raises(LLMError, match=message) as caught:
        await agent.run("测试")
    assert not caught.value.retryable
    assert create.await_count == 1
    assert [msg.role for msg in agent.conversation.get_messages()] == ["system"]


@pytest.mark.asyncio
async def test_responses_transient_failure_can_retry(make_agent):
    agent, create = make_agent(
        "responses",
        error=[
            responses_reply("部分", status="failed", code="server_error"),
            responses_reply("最终回复"),
        ],
    )
    assert await agent.run("测试") == "最终回复"
    assert create.await_count == 2
    assert [msg.content for msg in agent.conversation.get_messages()] == [
        "系统指令",
        "测试",
        "最终回复",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("api_type", ["chat_completion", "messages", "responses"])
@pytest.mark.parametrize(
    ("status", "code", "attempts"),
    [
        (None, None, 4),
        (400, None, 1),
        (401, None, 1),
        (403, None, 1),
        (429, "rate_limit_error", 4),
        (429, "insufficient_quota", 1),
        (503, None, 4),
    ],
)
async def test_sdk_errors_have_consistent_retry_budget(
    make_agent, api_type, status, code, attempts
):
    sdk = anthropic if api_type == "messages" else openai
    request = httpx2.Request("POST", "https://example.invalid")
    if status is None:
        upstream = sdk.APITimeoutError(request=request)
    else:
        response = httpx2.Response(status, request=request)
        body = {"error": {"type": "rate_limit_error", "code": code}}
        if sdk is openai:
            body = body["error"]
        upstream = sdk.APIStatusError(
            "raw upstream detail", response=response, body=body
        )
    agent, create = make_agent(api_type, error=upstream)

    with pytest.raises(LLMError) as caught:
        await agent.run("测试")
    assert caught.value.__cause__ is upstream
    assert caught.value.status_code == status
    assert caught.value.retryable is (attempts > 1)
    assert "raw upstream detail" not in str(caught.value)
    assert create.await_count == attempts
    assert [msg.role for msg in agent.conversation.get_messages()] == ["system"]
