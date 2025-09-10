from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from enum import Enum
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing import Optional, List
from recommender.basic_recommender.prompts import PROFILE_EXTRACTOR_PROMPT
from recommender.item_set import item_set
from tools.websearch import tavily_tool
from langgraph.prebuilt import create_react_agent


class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class CarRecommendationState(MessagesState):
    budget: Optional[int]
    preferred_brands: Optional[List[str]]
    fuel_type: Optional[FuelType]


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

    # Set of all tools to be bind
    tools = [tavily_tool]
    
    react_agent = create_react_agent(model=llm, tools=tools)

    llm_input = {"messages": [SystemMessage(PROFILE_EXTRACTOR_PROMPT.format(profile=profile_summary, item_set=item_set))]
                        + updates["messages"]}
    result = react_agent.invoke(llm_input)

    if result["messages"][-1].content:
        updates["messages"].append(AIMessage(result["messages"][-1].content))
    else:
        print(f"[no content!] result = {result}")

    # Return updates to be merged into state
    return updates
