from langchain_core.messages import HumanMessage
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from recommender.basic_recommender.main_agent import CarRecommendationState, agent_node
from recommender.recommender_interface import IRecommenderSystem
from typing import Optional


class RecommenderImplementation(IRecommenderSystem):
    def __init__(self):
        self.state: CarRecommendationState = CarRecommendationState(
            messages=[],
            budget=None,
            preferred_brands=None,
            fuel_type=None
        )
        graph = StateGraph(CarRecommendationState)
        graph.add_node("agent", agent_node)
        graph.add_edge(START, "agent")
        graph.add_edge("agent", END)
        self.compiled_graph = graph.compile()

    def chat(self, text: Optional[str]) -> str:
        self.state["messages"].append(HumanMessage(content=text))
        self.state = self.compiled_graph.invoke(self.state)
        return self.state["messages"][-1].content
