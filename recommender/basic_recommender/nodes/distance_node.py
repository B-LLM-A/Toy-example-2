# recommender/nodes/distance_node.py
from tools.distance_checker import distance_check
from recommender.basic_recommender.state import CarRecommendationState

def distance_node(state: CarRecommendationState):
    """Ensures recommended dealers are within 100 miles."""
    zipcode = state.get("zipcode")
    if not zipcode:
        print("[Distance Node] No user zipcode, skipping.")
        return state

    try:
        result = distance_check.invoke({"zipcode": zipcode})
        state["messages"].append(
            {"role": "assistant", "content": f"Nearby dealers found: {result}"}
        )
    except Exception as e:
        state["messages"].append(
            {"role": "assistant", "content": f"[Distance Node] Error: {e}"}
        )

    return state
