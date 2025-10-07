import re
from evaluation.evaluation_agents.dealer_evaluation_agent import run_dealer_eval_agent
from evaluation.evaluation_agents.shortlist_evaluation_agent import run_shortlist_eval_agent
from evaluation.evaluation_agents.budget_evaluation_agent import run_budget_eval_agent

class ConversationEvaluator:
    def __init__(self, args,  conversation_log, user_info):
        self.args = args
        self.conversation_log = conversation_log
        self.user_info = user_info

    def asked_location(self):
        return any(
            "where are you located" in m['content'].lower()
            or ("city" in m['content'].lower() and "state" in m['content'].lower())
            for m in self.conversation_log if m['role'] == 'assistant'
        )

    def included_safety_info(self):
        return any(
            "safety" in m['content'].lower() or "nhtsa" in m['content'].lower()
            for m in self.conversation_log if m['role'] == 'assistant'
        )

    def recommendation_list_short(self, max_items=5):
        rec_list_lengths = [
            sum(1 for line in m['content'].splitlines()
                if line.strip().startswith(("-", "•", "1.")))
            for m in self.conversation_log if m['role'] == 'assistant'
        ]
        return all(length <= max_items for length in rec_list_lengths if length)
    
    def recommendation_within_budget(self):
        pass

    def dealers_within_range(self, threshold_miles=100):
        # Ensure user_info from conversation if missing
        if not self.user_info or not self.user_info.get("city") or not self.user_info.get("state"):
            for m in self.conversation_log:
                if m['role'] == 'user':
                    match = re.search(
                        r"\b(?:I'm in|located in)\s+([A-Za-z\s]+),\s*([A-Za-z]{2,})",
                        m['content'], flags=re.IGNORECASE
                    )
                    if match:
                        self.user_info = {
                            "city": match.group(1).strip(),
                            "state": match.group(2).strip()
                        }
                        break

        if not self.user_info or not self.user_info.get("city") or not self.user_info.get("state"):
            print("Evaluator Failed to catch users location.")
            return None

        agent_result = run_dealer_eval_agent(
            conversation_log=self.conversation_log,
            user_city=self.user_info['city'],
            user_state=self.user_info['state'],
            threshold_miles=threshold_miles
        )
        print(f"Dealer Evaluator Agent: {agent_result}")
        
        clean_result = agent_result.strip().lower()

        if "true" in clean_result:
            return True
        elif "false" in clean_result:
            return False
        elif "none" in clean_result:
            return None
        return None


    def evaluate_all(self):
        return {
            "asked_location": self.asked_location(),
            "dealers_within_100_miles": self.dealers_within_range(100),
            "recommendations_within_budget": self.recommendation_within_budget(),
            "included_safety_info": self.included_safety_info(),
            # "recommendation_list_short": self.recommendation_list_short()
            "recommendation_list_short": run_shortlist_eval_agent(
                self.conversation_log,
                max_items=3
            )
        }
