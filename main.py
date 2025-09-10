from langchain_openai import ChatOpenAI

from recommender.basic_recommender.implementation import RecommenderImplementation
from user_simulator.basic_simulator.implementation import UserImplementation
from user_simulator.persona.GoalBased.persona_1 import PERSONA, RAW_REVIEW
from environment.environment import Environment
from judge.basic_judge.implementation import JudgeImplementation

if __name__ == "__main__":
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    judge = JudgeImplementation(llm)
    user = UserImplementation(persona=PERSONA, raw_review=RAW_REVIEW)
    recommender = RecommenderImplementation()
    env = Environment(user, recommender)
    env.evaluate(judge)
