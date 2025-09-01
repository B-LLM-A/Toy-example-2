from abc import ABC, abstractmethod
from typing import Optional


class IRecommenderSystem(ABC):
    @abstractmethod
    def chat(self, text: Optional[str]) -> str:
        pass
