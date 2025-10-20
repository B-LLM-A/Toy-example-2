# basic_recommender/state.py
from langgraph.graph import MessagesState
from typing import Optional, List
from enum import Enum

class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"

class CarRecommendationState(MessagesState):
    budget: Optional[int] = None
    preferred_brands: Optional[List[str]] = None
    fuel_type: Optional[FuelType] = None
    location: Optional[List[str]] = None  # [Country, State, City]
    zipcode: Optional[int] = None
