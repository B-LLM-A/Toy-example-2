from abc import ABC, abstractmethod
from typing import Optional


class IUserSimulator(ABC):
    def __init__(self, persona: str, raw_review: str):
        self.persona = persona
        self.raw_review = raw_review

    @abstractmethod
    def chat(self, text: Optional[str]) -> str:
        pass

    def get_persona(self) -> str:
        return self.persona

    def get_raw_review(self) -> str:
        return self.raw_review
