from typing import Optional, List
from pydantic import BaseModel, Field
import logging
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage

LOGGER = logging.getLogger("shortlist_eval.agent")

AGENT_SYSTEM_PROMPT = """
You are a Shortlist Evaluation Specialist.

Your task:
1. Scan the ENTIRE conversation log (all messages) for any recommendation sections, not just the final assistant reply.
2. Identify individual recommended items — they may appear in:
   - Bullet points (-, •, *, etc.)
   - Numbered lists (1., 2., etc.)
   - Headings followed by item details (car name, price, dealer, etc.)
   - Items separated by blank lines
3. Count how many UNIQUE recommended items appear across ALL sections combined.
   - Merge counts from separate headings or categories (e.g., "Tacoma Options" + "4Runner Options").
4. Apply the maximum allowed number (max_items) to the total count.
5. OUTPUT RULE: Return ONLY one word — True, False, or None — on a single line, lowercase or uppercase. 
   - True = total unique count ≤ max_items.
   - False = total unique count > max_items.
   - None = no recommendations found.

Rules:
- Treat each vehicle or product description listing as one recommendation, even if it spans multiple lines or includes images/links.
- Ignore duplicates (same model/year should count once).
- Recognize markdown styles with numbers followed by bold names, bullets, or headings.
- Ignore unrelated text, chatter, or specifications unless tied to a distinct recommendation item.
"""

class ShortlistEvalInput(BaseModel):
    conversation_log: List[dict] = Field(..., description="List of {'role': 'user'/'assistant', 'content': str}")
    max_items: Optional[int] = Field(5, description="Maximum allowed shortlist recommendations")

def run_shortlist_eval_agent(conversation_log, max_items=5) -> str:
    LOGGER.info("ShortlistEvalAgent start")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

    conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_log])

    user_msg = f"Max allowed items: {max_items}\n\nConversation:\n{conv_text}"

    try:
        result = llm.invoke([
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])
        content = result.content.strip()
        LOGGER.info("ShortlistEvalAgent: Result=%s", content)
        return content or "None"
    except Exception:
        LOGGER.exception("ShortlistEvalAgent failed")
        raise