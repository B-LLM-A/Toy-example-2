from litellm import completion
from prompts.user_prompts import USER_SIMULATION_SYSTEM_PROMPT
from typing import Optional
from user_simulator.user_interface import IUserSimulator


class UserImplementation(IUserSimulator):
    def __init__(self, persona: str, raw_review: str):
        super().__init__(persona, raw_review)
        self.messages = [
            {"role": "system", "content": USER_SIMULATION_SYSTEM_PROMPT.format(
                persona=self.persona,
                context="You want to buy a new car, and need some guidance and recommendation"
            )}
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
