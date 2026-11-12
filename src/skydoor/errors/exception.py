class AgentError(Exception):
    """应用异常基类"""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMError(AgentError):
    """所有 LLM 相关错误的类"""

    def __init__(
        self,
        message: str = "LLM 调用失败",
        *,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, retryable=retryable)
        self.status_code = status_code
