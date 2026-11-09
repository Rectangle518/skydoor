from typing import Literal


class Message:
    role: Literal["system", "user", "assistant"]
    content: str

    def __init__(self, role: Literal["system", "user", "assistant"], content: str):
        self.role = role
        self.content = content

    def __str__(self):
        return f"{self.role}: {self.content}"
