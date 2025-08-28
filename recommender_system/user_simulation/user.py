from litellm import completion
from recommender_system.prompts.user_simulator import USER_SIMULATION_SYSTEM_PROMPT, USER_SIMULATOR_USER_PROMPT
from langchain_core.messages import BaseMessage, AIMessage
from typing import List


class User:
    def __init__(self, persona_str):
        self.persona_str = persona_str

    def chat(self, old_messages: List[BaseMessage]) -> str:
        system_message = {"role": "system", "content": USER_SIMULATION_SYSTEM_PROMPT.format(
            persona=self.persona_str,
            context="You want to buy a new car, and need some guidance and recommendation"
        )}
        first_user_message = {"role": "user", "content": USER_SIMULATOR_USER_PROMPT}
        converted_old_messages = []
        for msg in old_messages:
            if hasattr(msg, 'content') and hasattr(msg, 'type'):
                # Handle LangChain BaseMessage objects
                role = "user" if msg.type == "human" else "assistant" if msg.type == "ai" else "system"
                converted_old_messages.append({"role": role, "content": str(msg.content)})
            elif isinstance(msg, dict):
                # Already in dict format
                converted_old_messages.append(msg)
            else:
                # Fallback - convert to string
                converted_old_messages.append({"role": "user", "content": str(msg)})
        messages = [system_message, first_user_message] + converted_old_messages
        response = completion(
            model="openai/gpt-4o",
            messages=messages
        )
        return response.choices[0].message.content

