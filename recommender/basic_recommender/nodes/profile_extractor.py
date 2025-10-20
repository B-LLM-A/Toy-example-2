# basic_recommender/nodes/profile_extractor.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from recommender.basic_recommender.state import CarRecommendationState, FuelType
from typing import Optional, List

class UpdateCarProfileSchema(BaseModel):
    budget: Optional[int] = Field(None)
    preferred_brands: Optional[List[str]] = Field(None)
    fuel_type: Optional[FuelType] = Field(None)
    location: Optional[List[str]] = Field(None)
    zipcode: Optional[int] = Field(None)

def merge_partial_update(state: CarRecommendationState, update: UpdateCarProfileSchema):
    updates = {}
    for field, value in update.model_dump(exclude_unset=True).items():
        if value is not None:
            updates[field] = value
    updates["messages"] = state["messages"]
    return updates

def profile_extractor_node(state: CarRecommendationState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    structured_llm = llm.with_structured_output(UpdateCarProfileSchema)

    result = structured_llm.invoke([
        SystemMessage(content="""Extract explicitly mentioned fields only:
        - budget (USD)
        - preferred brands
        - fuel type
        - location [Country, State, City]
        - zipcode"""),
        state["messages"][-1]
    ])
    return merge_partial_update(state, result)
