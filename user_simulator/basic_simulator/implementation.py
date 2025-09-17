from litellm import completion
from prompts.user_prompts import USER_SIMULATION_SYSTEM_PROMPT, CarState
from typing import Optional
from user_simulator.user_interface import IUserSimulator
from user_simulator.persona.GoalBased.persona_1 import RAW_REVIEW


class UserImplementation(IUserSimulator):
    def __init__(self, persona: str, raw_review: str, goal: str):
        super().__init__(persona, raw_review)
        system_prompt_format = USER_SIMULATION_SYSTEM_PROMPT.format(
            persona=self.persona,
            car_state=CarState.NEW_CAR,
            review=RAW_REVIEW,
            goal=goal,
            location="Paris, France"
        )
        # print(f"\nUSER_SYSTEM_PROMPT:\n {system_prompt_format}\n")
        self.messages = [
            {"role": "system", "content": system_prompt_format}
        ]

    def chat(self, new_message: Optional[str] = None) -> str:
        if new_message:
            self.messages.append({"role": "user", "content": new_message})
        response = completion(
            model="openai/gpt-4o",
            messages=self.messages
        )
        self.messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })
        return response.choices[0].message.content
