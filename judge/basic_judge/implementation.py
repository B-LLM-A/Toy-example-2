from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field

from judge.judge_interface import IJudge
from judge.basic_judge.prompts import JUDGE_USER_PROMPT_TEMPLATE, JUDGE_RECOMMENDER_PROMPT_TEMPLATE


class UserEvaluationScoreSet(BaseModel):
    clarity_score: int = Field(5, description="Score for clarity (1-10)")
    engagement_score: int = Field(5, description="Score for engagement (1-10)")
    coherence_with_context_score: int = Field(5, description="Score for coherence with context (1-10)")
    persona_alignment_score: int = Field(5, description="Score for persona alignment (1-10)")


class RecommenderEvaluationScoreSet(BaseModel):
    relevance_score: int = Field(5, description="Score for relevance (1-10)")
    helpfulness_score: int = Field(5, description="Score for helpfulness (1-10)")
    coherence_with_context_score: int = Field(5, description="Score for coherence with context (1-10)")
    engagement_score: int = Field(5, description="Score for engagement (1-10)")


class JudgeImplementation(IJudge):
    def __init__(self, llm):
        super().__init__()

        self.user_evaluator = llm.with_structured_output(UserEvaluationScoreSet)
        self.recommender_evaluator = llm.with_structured_output(RecommenderEvaluationScoreSet)

    def _validate_interaction(self, interaction: dict) -> bool:
        if "role" not in interaction.keys():
            return False
        role = interaction.get("role")
        if role not in ["user", "assistant"]:
            return False

        if "content" not in interaction.keys():
            return False
        content = interaction.get("content")
        if not isinstance(content, str):
            return False

        return True

    def evaluate_user_simulation(self, persona: str, raw_review: str) -> dict:
        user_criteria = {
            "clarity": "Is the user's message clear and understandable within the context?",
            "engagement": "Does the user keep the conversation flowing and invite meaningful responses?",
            "coherence_with_context": "Is the user's message consistent with the earlier turns in conversation?",
            "persona_alignment": "Does the message reflect the user's stated persona, preferences, and writing style?"
        }
        conversation = self.get_conversation()
        scores_dict = {
            "clarity": [],
            "engagement": [],
            "coherence_with_context": [],
            "persona_alignment": []
        }
        for turn_idx, turn in enumerate(conversation):
            if turn["role"] != "user":
                continue

            # Build conversation context so far
            context_up_to_now = conversation[:turn_idx]  # all prior turns
            context_text = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in context_up_to_now)

            # This user's message
            user_message = turn["content"]

            # Evaluate using the chain
            evaluation_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
                persona=persona,
                review=raw_review,
                context=context_text,
                message=user_message,
                criteria=user_criteria
            )
            scores: UserEvaluationScoreSet = self.user_evaluator.invoke([SystemMessage(evaluation_prompt)])

            # Append scores to dict
            scores_dict["clarity"].append(scores.clarity_score)
            scores_dict["engagement"].append(scores.engagement_score)
            scores_dict["coherence_with_context"].append(scores.coherence_with_context_score)
            scores_dict["persona_alignment"].append(scores.persona_alignment_score)

        return scores_dict

    def evaluate_recommender(self) -> dict:
        recommender_criteria = {
            "relevance": "Is the assistant's response relevant to the user's message?",
            "helpfulness": "Does the response provide useful recommendations or information?",
            "coherence_with_context": "Is the response consistent with the earlier conversation?",
            "engagement": "Does the response encourage further interaction?"
        }
        conversation = self.get_conversation()
        scores_dict = {
            "relevance": [],
            "helpfulness": [],
            "coherence_with_context": [],
            "engagement": []
        }
        for turn_idx, turn in enumerate(conversation):
            if turn["role"] != "assistant":
                continue

            # Build conversation context so far
            context_up_to_now = conversation[:turn_idx]  # all prior turns
            context_text = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in context_up_to_now)

            # This recommender's message
            assistant_message = turn["content"]

            # Evaluate using the chain
            evaluation_prompt = JUDGE_RECOMMENDER_PROMPT_TEMPLATE.format(
                context=context_text,
                message=assistant_message,
                criteria=recommender_criteria
            )
            scores: RecommenderEvaluationScoreSet = self.recommender_evaluator.invoke([SystemMessage(evaluation_prompt)])

            # Append scores to dict
            scores_dict["relevance"].append(scores.relevance_score)
            scores_dict["helpfulness"].append(scores.helpfulness_score)
            scores_dict["coherence_with_context"].append(scores.coherence_with_context_score)
            scores_dict["engagement"].append(scores.engagement_score)

        return scores_dict
