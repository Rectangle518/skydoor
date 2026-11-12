
class AgentError(Exception):
    """应用异常基类"""
    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable   # 标记是否值得重试

class LLMError(AgentError):
    """所有 LLM 相关错误的类"""
    def __init__(self, message: str = "LLM 调用失败", *, retryable: bool = False):
        super().__init__(message, retryable=retryable)