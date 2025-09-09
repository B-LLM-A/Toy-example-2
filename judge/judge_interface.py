from abc import ABC, abstractmethod
from typing import List


class IJudge(ABC):
    def __init__(self):
        self.conversation = []

    @abstractmethod
    def _validate_interaction(self, interaction: dict) -> bool:
        """
        :param interaction: dict
        :return: boolean of validity
        """
        pass

    def add_interaction(self, interaction: dict):
        """
        :param interaction:
        :return:
        """
        if not self._validate_interaction(interaction):
            raise TypeError(f"Bad argument: interaction not supported {interaction}")
        self.conversation.append(interaction)

    def get_conversation(self) -> List[dict]:
        return self.conversation

    @abstractmethod
    def evaluate_user_simulation(self, persona: str, raw_review: str) -> dict:
        """
        :return: the score of the user_simulator from 0 to 100
        """
        pass

    @abstractmethod
    def evaluate_recommender(self) -> dict:
        """
        :return: the score of the recommender from 0 to 100
        """
        pass
