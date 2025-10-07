from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool
import logging

from tools.nhtsa import NHTSA_TOOLS


AGENT_SYSTEM_PROMPT = """
You are a specialist assistant for retrieving vehicle safety ratings from
NHTSA SafetyRatings. Your task:
- Given a car suggestion (free text and/or year/make/model), first determine the
  best matching variant and its VehicleId via the SafetyRatings menus, then fetch
  the safety ratings for that VehicleId.

Process to follow strictly (no guessing):
1) If year is missing, list available years and ask for one (stop and wait).
2) With year, list makes (nhtsa_makes). If make is missing or ambiguous, present
   the top likely makes, ask for a selection (stop and wait).
3) With year+make, list models (nhtsa_models). If model is missing or ambiguous,
   present top candidates, ask for selection (stop and wait).
4) With year+make+model, list variants (nhtsa_variants) and select the most relevant
   variants based on the user hint; return the top 3 with VehicleId and descriptions.
5) Fetch and present the safety ratings via nhtsa_ratings for the selected VehicleId(s).

Rules:
- Do not call the same tool with the same arguments repeatedly.
- If a field is missing and cannot be resolved from the provided hint, ask once
  for that field and stop.
- Be concise and factual; include VehicleId, variant description, and key ratings.
"""


LOGGER = logging.getLogger("nhtsa.agent")


class NHTSACarQueryInput(BaseModel):
    query: Optional[str] = Field(None, description="Free-text car description/suggestion")
    year: Optional[int] = Field(None, description="Model year if known")
    make: Optional[str] = Field(None, description="Make if known")
    model: Optional[str] = Field(None, description="Model if known")


def run_nhtsa_agent(query: Optional[str] = None,
                    year: Optional[int] = None,
                    make: Optional[str] = None,
                    model: Optional[str] = None) -> str:
    LOGGER.info(
        f"run_nhtsa_agent: start query={query!r} year={year} make={make!r} model={model!r}"
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    tools = NHTSA_TOOLS
    LOGGER.info(f"run_nhtsa_agent: tools={[t.name for t in tools]}")
    agent = create_react_agent(model=llm, tools=tools)

    user_text_parts: List[str] = []
    if query:
        user_text_parts.append(f"Suggestion: {query}")
    if year is not None:
        user_text_parts.append(f"Year: {year}")
    if make:
        user_text_parts.append(f"Make: {make}")
    if model:
        user_text_parts.append(f"Model: {model}")
    if not user_text_parts:
        user_text_parts.append("No explicit hint provided; start from year menu.")
    user_msg = " | ".join(user_text_parts)

    try:
        result = agent.invoke({
            "messages": [
                SystemMessage(content=AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_msg),
            ]
        })
        content = result.get("messages", [])[-1].content if result else None
        LOGGER.info(
            f"run_nhtsa_agent: success content_len={len(content) if content else 0}"
        )
        return content or "No result produced by NHTSA agent."
    except Exception:
        LOGGER.exception("run_nhtsa_agent: failed")
        raise


NHTSA_AGENT_TOOL = StructuredTool.from_function(
    name="nhtsa_agent",
    description=(
        "Specialist sub-agent that uses NHTSA SafetyRatings to find VehicleId and fetch ratings"
    ),
    func=run_nhtsa_agent,
    args_schema=NHTSACarQueryInput,
)

