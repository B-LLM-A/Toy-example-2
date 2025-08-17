import time
from abc import ABC, abstractmethod
from typing import Optional


class Task(ABC):
    def __init__(self, desc: str, deps=None):
        if deps is None:
            deps = []
        self.deps = deps
        self.desc = desc
        self.exception: Optional[Exception] = None
        self.result: Optional[str] = None

    @abstractmethod
    def run(self):
        pass


class LLMCall(Task):
    def __init__(self, desc, deps):
        super().__init__(desc, deps)
        self.interaction_text: Optional[str] = None

    def run(self):
        print("calling LLM ...")
        time.sleep(1)
        self.interaction_text = "What type of car do you want?"
        return "LLM Result"


class WebSearch(Task):
    def run(self):
        print("searching Web ...")
        time.sleep(1)
        return "Web Result"

