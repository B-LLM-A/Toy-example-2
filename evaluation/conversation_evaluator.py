import re
from tools.distance_checker import distance_check

class ConversationEvaluator:
    def __init__(self, conversation_log, user_info):
        """
        conversation_log: list of {"role": "user"/"assistant", "content": str}
        user_info: dict with keys like {"city": "...", "state": "..."}
        """
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

    def dealers_within_range(self, threshold_miles=100):
        # Fallback: try to parse from conversation if missing
        if not self.user_info or not self.user_info.get("city") or not self.user_info.get("state"):
            for m in self.conversation_log:
                if m['role'] == 'user':
                    match = re.search(r"\b(?:I'm in|located in)\s+([A-Za-z\s]+),\s*([A-Z]{2})", m['content'])
                    if match:
                        self.user_info = {"city": match.group(1).strip(), "state": match.group(2).strip()}
                        break

        if not self.user_info or not self.user_info.get("city") or not self.user_info.get("state"):
            return None  # can't compute

        # Normal dealer range check
        all_nearby = True
        for m in self.conversation_log:
            if m['role'] == 'assistant' and "dealer" in m['content'].lower():
                match = re.search(r"dealer\s*[:\-]\s*([a-zA-Z ]+),\s*([A-Z]{2})", m['content'])
                if match:
                    dist_result = distance_check(
                        user_city=self.user_info['city'],
                        user_state=self.user_info['state'],
                        dealer_city=match.group(1).strip(),
                        dealer_state=match.group(2).strip(),
                        threshold_miles=threshold_miles
                    )
                    if not (isinstance(dist_result, dict) and dist_result.get("nearby")):
                        all_nearby = False
        return all_nearby


    def evaluate_all(self):
        return {
            "asked_location": self.asked_location(),
            "dealers_within_100_miles": self.dealers_within_range(100),
            "included_safety_info": self.included_safety_info(),
            "recommendation_list_short": self.recommendation_list_short()
        }
