from recommender.basic_recommender.implementation import RecommenderImplementation
from user_simulator.basic_simulator.implementation import UserImplementation
from user_simulator.persona.persona_1 import PERSONA
from environment.environment import Environment

if __name__ == "__main__":
    user = UserImplementation(persona_str=PERSONA)
    recommender = RecommenderImplementation()
    env = Environment(user, recommender)
    env.run()
