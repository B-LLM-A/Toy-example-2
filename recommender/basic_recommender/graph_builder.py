# recommender/graph_builder.py
from langgraph.graph import StateGraph, END
from recommender.basic_recommender.main_agent import CarRecommendationState
from recommender.basic_recommender.nodes.profile_extractor import profile_extractor_node
from recommender.basic_recommender.nodes.fueleconomy_node import fueleconomy_node
from recommender.basic_recommender.nodes.nhtsa_node import nhtsa_node
from recommender.basic_recommender.nodes.distance_node import distance_node
from recommender.basic_recommender.nodes.reasoning_node import reasoning_node  # this will finalize recommendations

def build_car_recommender_graph():
    graph = StateGraph(CarRecommendationState)

    # --- register nodes ---
    graph.add_node("extract_profile", profile_extractor_node)
    graph.add_node("distance_check", distance_node)
    graph.add_node("fueleconomy", fueleconomy_node)
    graph.add_node("nhtsa", nhtsa_node)
    graph.add_node("reason_and_recommend", reasoning_node)

    # --- define edges ---
    graph.add_edge("extract_profile", "distance_check")
    graph.add_edge("distance_check", "nhtsa")
    graph.add_edge("nhtsa", "fueleconomy")
    graph.add_edge("fueleconomy", "reason_and_recommend")
    graph.add_edge("reason_and_recommend", END)

    graph.set_entry_point("extract_profile")
    return graph.compile()
