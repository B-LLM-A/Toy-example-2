from langchain_core.messages import HumanMessage
from recommender.recommender_interface import IRecommenderSystem
from recommender.basic_recommender.graph_builder import build_car_recommender_graph
from recommender.basic_recommender.main_agent import CarRecommendationState
from typing import Optional

class RecommenderImplementation(IRecommenderSystem):
    def __init__(self):
        self.state = CarRecommendationState(
            messages=[],
            budget=None,
            preferred_brands=None,
            fuel_type=None,
            location=None,
            zipcode=None,
        )
        self.compiled_graph = build_car_recommender_graph()

    def chat(self, text: Optional[str]) -> str:
        # Append the user's latest message
        self.state["messages"].append(HumanMessage(content=text))

        # Run through the graph (which executes each node in sequence)
        self.state = self.compiled_graph.invoke(self.state)

        # Return the final LLM output
        return self.state["messages"][-1].content
