# recommender/nodes/fueleconomy_node.py
from langgraph.graph import END
from recommender.basic_recommender.state import CarRecommendationState
from recommender.basic_recommender.specialist_agents.fueleconomy_agent import FUELECONOMY_AGENT_TOOL

def fueleconomy_node(state: CarRecommendationState):
    """
    Uses FuelEconomy.gov API to enrich recommendations with MPG, cost, etc.
    """
    user_brands = state.get("preferred_brands", [])
    fuel_type = state.get("fuel_type")

    # If the user has not provided enough info, skip gracefully
    if not user_brands or not fuel_type:
        print("[FuelEconomyNode] Insufficient data, skipping.")
        return state

    # Example call — adapt depending on how FUELECONOMY_AGENT_TOOL works
    try:
        result = FUELECONOMY_AGENT_TOOL.invoke(
            {"brand": user_brands[0], "fuel_type": str(fuel_type)}
        )
        # Assume the tool returns structured info like {"mpg": 35, "emission": "low"}
        state["messages"].append(
            {
                "role": "assistant",
                "content": f"FuelEconomy data for {user_brands[0]} ({fuel_type}): {result}",
            }
        )
    except Exception as e:
        state["messages"].append(
            {
                "role": "assistant",
                "content": f"[FuelEconomyNode] Error accessing API: {e}",
            }
        )

    return state
