from typing import Optional, List
from enum import Enum
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel, Field

from recommender_system.prompts.profile_extractor import PROFILE_EXTRACTOR_PROMPT
from recommender_system.user_simulation.user import User


class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class CarRecommendationState(MessagesState):
    budget: Optional[int] = None
    preferred_brands: Optional[List[str]] = None
    fuel_type: Optional[FuelType] = None


class UpdateCarProfileSchema(BaseModel):
    budget: Optional[int] = Field(None, description="Maximum budget in USD")
    preferred_brands: Optional[List[str]] = Field(None, description="Preferred brands")
    fuel_type: Optional[FuelType] = Field(None, description="Fuel type")


def merge_partial_update(state: CarRecommendationState, update: UpdateCarProfileSchema) -> dict:
    """Merge updates into state and return the changes as a dict"""
    updates = {}

    for field_name, value in update.model_dump(exclude_unset=True).items():
        if value is None:
            continue

        # Special handling for lists: extend instead of replace
        if isinstance(value, list) and field_name == "preferred_brands":
            existing = state.get(field_name, []) or []
            # Avoid duplicates
            new_brands = [brand for brand in value if brand not in existing]
            if new_brands:
                updates[field_name] = existing + new_brands
        else:
            updates[field_name] = value
    updates["messages"] = state["messages"]
    return updates


def agent_node(state: CarRecommendationState):
    # Get the last user message
    last_message = state["messages"][-1]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    structured_llm = llm.with_structured_output(UpdateCarProfileSchema)

    # Extract information from user input
    result = structured_llm.invoke([
        SystemMessage(content="""Extract only the fields the user explicitly mentioned. 
        If not specified, leave it as null. Do NOT guess or infer.

        Examples:
        - "I want a Toyota under $25000" -> budget: 25000, preferred_brands: ["Toyota"]
        - "I prefer electric cars" -> fuel_type: "electric"
        - "My budget is 30k" -> budget: 30000"""),
        last_message
    ])

    # Merge updates
    updates = merge_partial_update(state, result)

    # Create profile summary
    profile_summary = {
        "budget": updates.get("budget", state.get("budget")),
        "preferred_brands": updates.get("preferred_brands", state.get("preferred_brands", [])),
        "fuel_type": updates.get("fuel_type", state.get("fuel_type"))
    }

    result = llm.invoke([SystemMessage(PROFILE_EXTRACTOR_PROMPT.format(profile=profile_summary))] + updates["messages"])
    if result.content:
        updates["messages"].append(AIMessage(result.content))
        print(f"Recommender: {result.content}")
    else:
        print(f"[no content!] result = {result}")

    # Return updates to be merged into state
    return updates


# ------------------------------
# Graph
# ------------------------------

graph = StateGraph(CarRecommendationState)
graph.add_node("agent", agent_node)
graph.add_edge(START, "agent")
graph.add_edge("agent", END)
app = graph.compile()

# ------------------------------
# Test Loop
# ------------------------------

if __name__ == "__main__":
    # Initialize state
    initial_state: CarRecommendationState = CarRecommendationState(
        messages=[],
        budget=None,
        preferred_brands=None,
        fuel_type=None
    )

    print("Car Recommendation Assistant")
    print("Type 'exit' or 'quit' to stop")
    print("-" * 40)

    current_state = initial_state
    user = User(persona_str="""
{
  "persona_name": "Practical Value Seeker",
  "personality_traits": [
    "practical",
    "budget-conscious",
    "value-oriented",
    "detail-oriented"
  ],
  "decision_making_style": "budget-first with practical focus",
  "primary_motivations": [
    "long-term value",
    "financial security",
    "reliability"
  ],
  "lifestyle_patterns": {
    "usage_type": "daily commuting and occasional road trips",
    "budget_approach": "cost-effective with focus on maximizing value",
    "risk_tolerance": "conservative",
    "time_horizon": "long-term focused"
  },
  "communication_preferences": {
    "information_depth": "high-detail",
    "tone": "technical",
    "focus_areas": [
      "value for money",
      "practicality",
      "warranty and safety features"
    ]
  },
  "behavioral_patterns": {
    "research_depth": "extensive",
    "feature_priorities": [
      "versatility",
      "warranty coverage",
      "safety ratings",
      "cost efficiency"
    ],
    "deal_breakers": [
      "lack of value",
      "poor warranty",
      "high maintenance costs"
    ],
    "compromise_willingness": "willing to compromise on performance and luxury for better value and practicality"
  },
  "simulation_keywords": [
    "excellent value",
    "versatility",
    "budget-minded",
    "practicality",
    "warranty protection"
  ]
}
""")

    while True:
        user_input = user.chat(current_state["messages"])
        if "###STOP###" in user_input:
            break

        # Add user message to state
        current_state["messages"].append(HumanMessage(content=user_input))
        print(f"User: {user_input}")

        try:
            # Invoke the graph
            result_state = app.invoke(current_state)
            current_state = result_state

            print("--- Current Profile ---")
            print(f"Budget: ${current_state.get('budget', 'Not specified')}")
            print(f"Preferred Brands: {current_state.get('preferred_brands', 'Not specified')}")
            print(f"Fuel Type: {current_state.get('fuel_type', 'Not specified')}")
            print("-" * 25)

        except Exception as e:
            print(f"Error: {e}")
            continue
