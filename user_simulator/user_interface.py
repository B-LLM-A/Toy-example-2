from abc import ABC, abstractmethod
from typing import Optional


class IUserSimulator(ABC):
    @abstractmethod
    def chat(self, text: Optional[str]) -> str:
        pass
