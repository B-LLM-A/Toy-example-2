from langchain.evaluation import CriteriaEvalChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from recommender.basic_recommender.implementation import RecommenderImplementation
from user_simulator.basic_simulator.implementation import UserImplementation
from user_simulator.persona.persona_1 import PERSONA
from user_simulator.persona.persona_2 import PERFORMANCE_DRIVEN_URBAN_EXPLORER
from user_simulator.persona.Q5_adveturer import Performance_Driven_Adventurer, RAW_REVIEW
from environment.environment import Environment
from judge.basic_judge.implementation import JudgeImplementation

if __name__ == "__main__":
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    judge = JudgeImplementation(llm)
    user = UserImplementation(persona=Performance_Driven_Adventurer, raw_review=RAW_REVIEW)
    recommender = RecommenderImplementation()
    print(recommender.chat("Hi! search for new Lamborghini cars and give me the newest car model name."))
    print()
    # env = Environment(user, recommender)
    # env.evaluate(judge)
