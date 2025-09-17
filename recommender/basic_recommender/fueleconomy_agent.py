from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool
import logging

from tools.fueleconomy import FE_TOOLS


AGENT_SYSTEM_PROMPT = """
You are a specialist assistant for retrieving authoritative vehicle information
from FuelEconomy.gov. Your job:
- Given a car suggestion (free text and/or year/make/model), determine the best
  matching vehicles using the FuelEconomy tools, and return clear, concise info.

This resource has a menu in which we have to iterate and find our desired model, This process includes:
1. use fe_menu_years to find available years
2. use fe_menu_makes to find available Brands (e.g. Toyota, Honda)
3. use fe_menu_models to find model name (e.g. '4Runner 2WD')
4. use fe_menu_options to retrieve trims and their corresponding id {year: exact matching option from fe_menu_years, make: exact matching option from fe_menu_makes, model: exact matching option from fe_menu_models}
5. use fe_vehicle_details to retrieve the exact information and details about that vehicle

If the user query is too ambiguous in any of the steps, you can pause and ask for more details
"""


LOGGER = logging.getLogger("fueleconomy.agent")
_MAX_LOG_BODY = 1500


def _truncate(text: Optional[str], limit: int = _MAX_LOG_BODY) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + f"... [truncated {len(text) - limit} chars]"


class FECarQueryInput(BaseModel):
    query: Optional[str] = Field(None, description="Free-text car description/suggestion")
    year: Optional[int] = Field(None, description="Model year if known")
    make: Optional[str] = Field(None, description="Make if known")
    model: Optional[str] = Field(None, description="Model if known")


def run_fueleconomy_agent(query: Optional[str] = None,
                          year: Optional[int] = None,
                          make: Optional[str] = None,
                          model: Optional[str] = None) -> str:
    print("###### running FE agent #######")
    """Run the FuelEconomy sub-agent to fetch details for a suggested car."""
    LOGGER.info(
        f"run_fueleconomy_agent: start query={query!r} year={year} make={make!r} model={model!r}"
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    tools = FE_TOOLS
    LOGGER.info(f"run_fueleconomy_agent: tools={[t.name for t in tools]}")
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
    LOGGER.info(
        f"run_fueleconomy_agent: sending system_prompt_len={len(AGENT_SYSTEM_PROMPT)} user_msg={_truncate(user_msg)}"
    )

    try:
        result = agent.invoke({
            "messages": [
                SystemMessage(content=AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_msg),
            ]
        })
        content = result.get("messages", [])[-1].content if result else None
        LOGGER.info(
            f"run_fueleconomy_agent: success content_len={len(content) if content else 0} content_preview={_truncate(content)}"
        )
        return content or "No result produced by FuelEconomy agent."
    except Exception:
        LOGGER.exception("run_fueleconomy_agent: failed")
        raise


FUELECONOMY_AGENT_TOOL = StructuredTool.from_function(
    name="fueleconomy_agent",
    description=(
        "Specialist sub-agent that uses FuelEconomy.gov tools to fetch "
        "reliable vehicle information for a provided car suggestion."
    ),
    func=run_fueleconomy_agent,
    args_schema=FECarQueryInput,
)
