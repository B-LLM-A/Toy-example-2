from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from enum import Enum
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing import Optional, List
from prompts.recommender_prompts import PROFILE_EXTRACTOR_PROMPT
from recommender.item_set import item_set
from recommender.basic_recommender.fueleconomy_agent import FUELECONOMY_AGENT_TOOL
from recommender.basic_recommender.nhtsa_agent import NHTSA_AGENT_TOOL
from recommender.basic_recommender.car_detail_agent import CAR_DETAIL_AGENT_TOOL
from tools.websearch import tavily_tool
# from tools.NHTSA import get_car_safety_details
from tools.distance_checker import distance_check
from tools.autodev import auto_dev_inventory_tool
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchResults



class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class CarRecommendationState(MessagesState):
    budget: Optional[int]
    preferred_brands: Optional[List[str]]
    fuel_type: Optional[FuelType]
    location: Optional[List[str]] # Country, State, City
    zipcode: Optional[int]


class UpdateCarProfileSchema(BaseModel):
    budget: Optional[int] = Field(None, description="Maximum budget in USD")
    preferred_brands: Optional[List[str]] = Field(None, description="Preferred brands")
    fuel_type: Optional[FuelType] = Field(None, description="Fuel type")
    location: Optional[List[str]] = Field(
        None, 
        description="User location as [Country, State, City]"
    )
    zipcode: Optional[int] = Field(None, description="User Zipcode")


def merge_partial_update(state: CarRecommendationState, update: UpdateCarProfileSchema) -> dict:
    """Merge updates into state and return the changes as a dict"""
    updates = {}

    for field_name, value in update.model_dump(exclude_unset=True).items():
        if value is None:
            continue

        # Special handling for lists: extend instead of replace
        if field_name == "preferred_brands" and isinstance(value, list):
            existing = state.get(field_name, []) or []
            # Avoid duplicates
            new_brands = [brand for brand in value if brand not in existing]
            if new_brands:
                updates[field_name] = existing + new_brands

        # Special handling for location: set only if not already in state
        elif field_name == "location":
            if state.get("location") is None:
                updates["location"] = value
        
        elif field_name == "zipcode":
            if state.get("zipcode") is None:
                updates["zipcode"] = value

        # Regular assignment for all other fields
        else:
            updates[field_name] = value

    updates["messages"] = state["messages"]
    return updates


def agent_node(state: CarRecommendationState):
    last_message = state["messages"][-1]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


    structured_llm = llm.with_structured_output(UpdateCarProfileSchema)

    result = structured_llm.invoke([
        SystemMessage(content="""Extract only the fields the user explicitly mentioned. 
    If not specified, leave it as null. Do NOT guess or infer.

    Fields to extract:
    - budget: integer (USD)
    - preferred_brands: list of brand names
    - fuel_type: one of ["petrol", "diesel", "electric", "hybrid"]
    - location: list in the format [Country, State, City] — only extract if the user clearly mentions it.
    - zipcode: integer — only extract if the user clearly mentions it.

    Examples:
    - "I want a Toyota under $25000" -> budget: 25000, preferred_brands: ["Toyota"]
    - "I prefer electric cars" -> fuel_type: "electric"
    - "My budget is 30k" -> budget: 30000
    - "I'm in Readyville, TN 37149" -> location: ["USA", "TN", "Readyville"] and -> zipcode: 37149
    """),
        last_message
    ])

    # Merge updates
    updates = merge_partial_update(state, result)

    # Create profile summary
    profile_summary = {
    "budget": updates.get("budget", state.get("budget")),
    "preferred_brands": updates.get("preferred_brands", state.get("preferred_brands", [])),
    "fuel_type": updates.get("fuel_type", state.get("fuel_type")),
    "location": updates.get("location", state.get("location")),
    "zipcode": updates.get("zipcode", state.get("zipcode"))
    }

    # Set of all tools to be bound
    # Supervisor pattern: main agent can call sub-agents (e.g., fueleconomy_agent)
    tools = [
        # DuckDuckGoSearchResults(num_results=5),
        FUELECONOMY_AGENT_TOOL,
        NHTSA_AGENT_TOOL,
        # auto_dev_inventory_tool,
        distance_check,
        CAR_DETAIL_AGENT_TOOL
    ]

    react_agent = create_react_agent(model=llm, tools=tools)

    llm_input = {"messages": [SystemMessage(PROFILE_EXTRACTOR_PROMPT.format(profile=profile_summary))]
                        + updates["messages"]}
    result = react_agent.invoke(llm_input)

    # for action, observation in result.get("intermediate_steps", []):
    #     if isinstance(observation, Exception):
    #         print("Tool error:", observation)

    if result["messages"][-1].content:
        updates["messages"].append(AIMessage(result["messages"][-1].content))
    else:
        print(f"[no content!] result = {result}")

    # Return updates to be merged into state
    return updates
