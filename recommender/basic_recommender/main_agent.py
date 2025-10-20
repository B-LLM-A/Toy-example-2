from langgraph.graph import StateGraph, END
from recommender.basic_recommender.state import CarRecommendationState
from recommender.basic_recommender.nodes.profile_extractor import profile_extractor_node
from recommender.basic_recommender.nodes.fueleconomy_node import fueleconomy_node
from recommender.basic_recommender.nodes.nhtsa_node import nhtsa_node
from recommender.basic_recommender.nodes.distance_node import distance_node
from recommender.basic_recommender.nodes.reasoning_node import reasoning_node

graph = StateGraph(CarRecommendationState)

# Register nodes
graph.add_node("extract_profile", profile_extractor_node)
graph.add_node("fueleconomy", fueleconomy_node)
graph.add_node("nhtsa", nhtsa_node)
graph.add_node("distance_check", distance_node)
graph.add_node("reason_and_recommend", reasoning_node)

# Define edges (pipeline)
graph.add_edge("extract_profile", "fueleconomy")
graph.add_edge("fueleconomy", "nhtsa")
graph.add_edge("nhtsa", "distance_check")
graph.add_edge("distance_check", "reason_and_recommend")
graph.add_edge("reason_and_recommend", END)

# Set entry point
graph.set_entry_point("extract_profile")

# Compile
car_recommender_app = graph.compile()
