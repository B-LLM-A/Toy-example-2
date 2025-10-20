# basic_recommender/nodes/reasoning_agent.py
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from recommender.basic_recommender.state import CarRecommendationState
from prompts.recommender_prompts import PROFILE_EXTRACTOR_PROMPT
from recommender.basic_recommender.specialist_agents.fueleconomy_agent import FUELECONOMY_AGENT_TOOL
from recommender.basic_recommender.specialist_agents.nhtsa_agent import NHTSA_AGENT_TOOL
from recommender.basic_recommender.specialist_agents.car_detail_agent import CAR_DETAIL_AGENT_TOOL
from tools.distance_checker import distance_check

def reasoning_node(state: CarRecommendationState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    tools = [
        FUELECONOMY_AGENT_TOOL,
        NHTSA_AGENT_TOOL,
        distance_check,
        CAR_DETAIL_AGENT_TOOL,
    ]
    react_agent = create_react_agent(model=llm, tools=tools)

    profile_summary = {
        "budget": state.get("budget"),
        "preferred_brands": state.get("preferred_brands", []),
        "fuel_type": state.get("fuel_type"),
        "location": state.get("location"),
        "zipcode": state.get("zipcode"),
    }

    messages = [SystemMessage(PROFILE_EXTRACTOR_PROMPT.format(profile=profile_summary))] + state["messages"]
    result = react_agent.invoke({"messages": messages})

    updates = {"messages": state["messages"] + [AIMessage(result["messages"][-1].content)]}
    return updates
