from typing import Optional, List
from pydantic import BaseModel, Field
import logging
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import StructuredTool
from tools.distance_checker import distance_check

AGENT_SYSTEM_PROMPT = """
You are a Dealer Range Evaluation Specialist.
Your job:
1. Scan the provided conversation log (assistant and user messages) for dealer mentions.
2. Extract each dealer’s city and state robustly, using flexible parsing rules.
3. For each city/state found, call the 'distance_check' tool to verify distance from user.
4. OUTPUT RULE: Return ONLY the word True, False, or None — in lowercase or uppercase — on a single line, with no explanation, no extra text, no markdown.

Rules:
- Do NOT estimate distances manually — always use tools for distance.
- If any dealer is too far or cannot be parsed to valid city/state, return "False".
- If no dealer mentions exist in the conversation, return "None".
- Ignore dealers with incomplete location info entirely — they must be parseable to city/state for checking.
- Do not alter user location — take it exactly as given in the input.
"""


LOGGER = logging.getLogger("dealer_eval.agent")

class DealerRangeQueryInput(BaseModel):
    conversation_log: List[dict] = Field(..., description="List of {'role': 'user'/'assistant', 'content': str}")
    user_city: str = Field(..., description="City of the user")
    user_state: str = Field(..., description="State of the user")
    threshold_miles: Optional[int] = Field(100, description="Maximum allowed distance in miles")

def run_dealer_eval_agent(conversation_log, user_city, user_state, threshold_miles=100) -> str:
    LOGGER.info("DealerEvalAgent start")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    tools = [DistanceCheckTool]
    
    agent = create_react_agent(model=llm, tools=tools)

    # Convert conversation log to readable text form
    conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_log])

    user_msg = (
        f"User location: {user_city}, {user_state} | Threshold: {threshold_miles} miles\n\n"
        f"Conversation:\n{conv_text}"
    )

    try:
        result = agent.invoke({
            "messages": [
                SystemMessage(content=AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_msg),
            ]
        })
        content = result.get("messages", [])[-1].content if result else None
        LOGGER.info("DealerEvalAgent: Result=%s", content)
        return content or "None"
    except Exception:
        LOGGER.exception("DealerEvalAgent failed")
        raise

# DistanceCheckTool = StructuredTool.from_function(
#     name="distance_check",
#     description="Check distance between user location and dealer location",
#     func=distance_check,
#     args_schema=None
# )

DistanceCheckTool = distance_check