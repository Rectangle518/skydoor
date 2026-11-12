from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    ContentFilterFinishReasonError,
    LengthFinishReasonError,
    OpenAIError,
)

from ...errors.exception import LLMError
from ._common import http_error


def openai_error(error: OpenAIError) -> LLMError:
    if isinstance(error, APITimeoutError):
        return LLMError("LLM 请求超时", retryable=True)
    if isinstance(error, APIConnectionError):
        return LLMError("LLM 网络连接失败", retryable=True)
    if isinstance(error, APIStatusError):
        return http_error(error.status_code, error.code, error.type)
    if isinstance(error, LengthFinishReasonError):
        return LLMError("LLM 输出达到长度上限")
    if isinstance(error, ContentFilterFinishReasonError):
        return LLMError("LLM 输出被内容过滤")
    return LLMError("LLM SDK 调用失败")
