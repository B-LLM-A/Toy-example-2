# recommender/nodes/nhtsa_node.py
from recommender.basic_recommender.state import CarRecommendationState
from recommender.basic_recommender.specialist_agents.nhtsa_agent import NHTSA_AGENT_TOOL

def nhtsa_node(state: CarRecommendationState):
    """Fetches official car safety data."""
    user_brands = state.get("preferred_brands", [])
    if not user_brands:
        print("[NHTSA Node] No brand info, skipping.")
        return state

    try:
        result = NHTSA_AGENT_TOOL.invoke({"brand": user_brands[0]})
        state["messages"].append(
            {"role": "assistant", "content": f"NHTSA safety info: {result}"}
        )
    except Exception as e:
        state["messages"].append(
            {"role": "assistant", "content": f"[NHTSA Node] Error: {e}"}
        )

    return state
