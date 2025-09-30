from typing import Optional
from pydantic import BaseModel, Field
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool

from tools.finance_tools import (
    calculate_financing,
    calculate_lease,
    get_maintenance_cost,
    get_depreciation_info
)

SYSTEM_PROMPT = """
You are a Finance & Ownership Analysis Agent.
Given a car's details (make, model, year, price, location, ownership period), 
use the provided tools to:
- Calculate financing options & monthly payments
- Calculate lease estimates
- Estimate maintenance & repair costs
- Calculate depreciation
Return the results in structured JSON.
"""

class FinanceCarQueryInput(BaseModel):
    query: Optional[str] = Field(None, description="Free-text car description")
    make: Optional[str] = Field(None, description="Car make")
    model: Optional[str] = Field(None, description="Car model")
    year: Optional[int] = Field(None, description="Model year")
    price: Optional[float] = Field(None, description="Price in USD")
    location: Optional[str] = Field(None, description="Location of purchase")
    ownership_period: Optional[int] = Field(None, description="Ownership period in years")

def run_finance_agent(
    query: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    price: Optional[float] = None,
    location: Optional[str] = None,
    ownership_period: Optional[int] = None
) -> str:
    """Run the finance agent with given car details."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
    tools = [
        calculate_financing,
        calculate_lease,
        get_maintenance_cost,
        get_depreciation_info
    ]

    agent = create_react_agent(model=llm, tools=tools)

    # Build user message from available parts
    user_parts = []
    if query: user_parts.append(f"Query: {query}")
    if make: user_parts.append(f"Make: {make}")
    if model: user_parts.append(f"Model: {model}")
    if year is not None: user_parts.append(f"Year: {year}")
    if price is not None: user_parts.append(f"Price: {price}")
    if location: user_parts.append(f"Location: {location}")
    if ownership_period is not None: user_parts.append(f"Ownership Period: {ownership_period}")
    if not user_parts: user_parts.append("No car details provided.")

    try:
        result = agent.invoke({
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=" | ".join(user_parts))
            ]
        })
        return result["messages"][-1].content
    except Exception as e:
        raise RuntimeError(f"Finance agent failed: {e}")

FINANCE_AGENT_TOOL = StructuredTool.from_function(
    name="finance_agent",
    description=(
        "Specialist sub-agent for calculating financing, leasing, maintenance, and depreciation"
    ),
    func=run_finance_agent,
    args_schema=FinanceCarQueryInput
)
