from typing import Protocol
from ...core.message import Message
from ...core.context import LLMRequest, LLMResponse

# Responses API
class ResponsesProvider:

    base_url: str
    api_key: str
    model: str
    api_type: str = "responses"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model