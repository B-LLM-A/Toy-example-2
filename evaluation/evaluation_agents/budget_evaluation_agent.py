import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

LOGGER = logging.getLogger(__name__)

# Phrase → numeric range mapping (approximate USD, can be adjusted)
BUDGET_PHRASE_MAP = {
    "tight budget": (0, 25000),
    "affordable suv": (25000, 30000),
    "affordable sedan": (15000, 25000),
    "entry-level car": (15000, 25000),
    "entry-level suv": (20000, 30000),
    "mid-range car": (30000, 40000),
    "mid-range suv": (35000, 45000),
    "cheap": (0, 20000),
    "low price": (0, 20000),
}

AGENT_SYSTEM_PROMPT = """
You are a Budget Evaluation Specialist for vehicle recommendations.

Your task:
1. Read the ENTIRE conversation log.
2. Interpret user's budget constraints using:
   - Explicit numeric values (any currency, any format).
   - Numeric ranges ("under 30k", "20–25 thousand").
   - Currency-less phrases ("under 20 grand", "twenty grand", "less than 40k") → convert 'grand' to thousand USD.
   - Qualitative phrases ("tight budget", "affordable", "cheap", "entry-level").
   - Comparative statements ("cheaper than a Tacoma", "less than Highlander").

Phrase→numeric range hints (USD):
TIGHT BUDGET ≈ 0–25k
AFFORDABLE SUV ≈ 25–30k
AFFORDABLE SEDAN ≈ 15–25k
ENTRY-LEVEL CAR ≈ 15–25k
ENTRY-LEVEL SUV ≈ 20–30k
MID-RANGE CAR ≈ 30–40k
MID-RANGE SUV ≈ 35–45k
CHEAP ≈ 0–20k
LOW PRICE ≈ 0–20k

3. If currency is missing, infer numeric value from these hints or market norms for the mentioned vehicle category/year.
4. Identify all assistant vehicle recommendations:
   - Include year/make/model and stated price or price range.
   - If price is missing, estimate market value from typical pricing for that model/year.
5. Compare each recommendation price/range to the inferred budget limit:
   - If any recommendation is over budget → False
   - If all are within budget → True
   - If no reasonable budget exists → None
6. OUTPUT: Only 'True', 'False', or 'None'.
"""

class BudgetEvalInput(BaseModel):
    conversation_log: List[dict] = Field(..., description="List of {'role': 'user'/'assistant', 'content': str}")
    budget: Optional[int] = Field(..., description="User's budget.")

def run_budget_eval_agent(conversation_log, budget) -> str:
    LOGGER.info("BudgetEvalAgent start")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

    conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_log])

    # Pre-process budget for mapping table hints
    budget_hints = []
    if budget is not None:
        budget_hints.append(f"Explicit budget given: {budget} USD")
    else:
        lowered_conv = conv_text.lower()
        for phrase, (low, high) in BUDGET_PHRASE_MAP.items():
            if phrase in lowered_conv:
                budget_hints.append(f"Phrase '{phrase}' → inferred budget range: {low}-{high} USD")

    user_msg = f"Budget Info:\n" + "\n".join(budget_hints) + "\n\nConversation:\n" + conv_text

    try:
        result = llm.invoke([
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])
        content = result.content.strip()
        LOGGER.info("BudgetEvalAgent: Result=%s", content)
        return content or "None"
    except Exception:
        LOGGER.exception("BudgetEvalAgent failed")
        raise
