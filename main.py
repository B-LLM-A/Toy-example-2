from langchain_openai import ChatOpenAI
import logging
import argparse

from recommender.basic_recommender.implementation import RecommenderImplementation
from user_simulator.simulator.implementation import UserImplementation
from user_simulator.persona.GoalBased.persona_2 import PERSONA as GPERSONA, RAW_REVIEW as GRAW_REVIEW, GOALS
from user_simulator.persona.JsonPersona.persona_2 import PERSONA as PPERSONA, RAW_REVIEW as PRAW_REVIEW
from environment.environment import Environment
from judge.basic_judge.implementation import JudgeImplementation

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluate", action='store_true', help="Evaluate conversation after termination")
    parser.add_argument("--verbose", action='store_true', help="Print for debugging")
    parser.add_argument("--chat", action='store_true', help="Chat directly with the agent")

    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_args()

    logging.basicConfig(
        # level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    # judge = JudgeImplementation(llm)
    recommender = RecommenderImplementation()
    
    if args.chat:
        print("=== Direct Chat Mode ===")
        print("Type 'exit' to quit.\n")
        user = None
    else:
        user = UserImplementation(args, persona=PPERSONA, raw_review=PRAW_REVIEW, goal=GOALS["LOYAL"])
    env = Environment(args, user, recommender)
    env.run()
    # resp = recommender.chat("Find the availibility of 2024 Ford Mustang in Montgomery!")
    # print(resp)

if __name__ == "__main__":
    main()