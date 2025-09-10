from langchain_openai import ChatOpenAI

from recommender.basic_recommender.implementation import RecommenderImplementation
from user_simulator.basic_simulator.implementation import UserImplementation
from user_simulator.persona.GoalBased.persona_1 import PERSONA as GPERSONA, RAW_REVIEW as GRAW_REVIEW
from user_simulator.persona.JsonPersona.persona_1 import PERSONA as PPERSONA, RAW_REVIEW as PRAW_REVIEW
from environment.environment import Environment
from judge.basic_judge.implementation import JudgeImplementation

if __name__ == "__main__":
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    judge = JudgeImplementation(llm)
    user = UserImplementation(persona=PPERSONA, raw_review=PRAW_REVIEW)
    recommender = RecommenderImplementation()
    env = Environment(user, recommender)
    env.evaluate(judge)
