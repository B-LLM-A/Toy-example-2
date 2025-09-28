from litellm import completion
from prompts.user_prompts import USER_SIMULATION_SYSTEM_PROMPT, CarState
from typing import Optional
from user_simulator.user_interface import IUserSimulator
from user_simulator.persona.GoalBased.persona_1 import RAW_REVIEW
import json
import random
from pathlib import Path
import logging


class UserImplementation(IUserSimulator):
    def __init__(self, args, persona: str, raw_review: str, goal: str):
        super().__init__(persona, raw_review)
        self.args = args
        # Sample a location and store both structured & text versions
        location_str, location_struct = self._sample_location()
        self.location = location_struct  # <<<< structured form

        system_prompt_format = USER_SIMULATION_SYSTEM_PROMPT.format(
            persona=self.persona,
            car_state=CarState.NEW_CAR,
            review=RAW_REVIEW,
            goal=goal,
            location=location_str
        )
        if self.args.verbose:
            print(f"\nUSER_SYSTEM_PROMPT:\n {system_prompt_format}\n")
        self.messages = [{"role": "system", "content": system_prompt_format}]


    def _sample_location(self):
        """Return location as (string, dict)."""
        try:
            data_path = Path(__file__).resolve().parent.parent / "user_data" / "zipcodes.json"
            with data_path.open("r", encoding="utf-8") as f:
                zips = json.load(f)
            rec = random.choice(zips)
            city = rec.get("city") or ""
            state_full = rec.get("state_full") or ""
            state_abbr = rec.get("state_id") or ""
            country = rec.get("country") or "United States"
            zipcode = rec.get("zip_code") or "11111"

            location_str = ", ".join([p for p in [city, state_full, zipcode, country] if p])
            location_struct = {"city": city, "state": state_abbr or state_full, "zip": zipcode}

            return location_str, location_struct
        except Exception as e:
            logging.getLogger("user_simulator").warning(
                f"Falling back to default location due to error: {e}"
            )
            return "Fischer, Texas, United States", {"city": "Fischer", "state": "TX", "zip": "78623"}

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
