from user_simulator.user_interface import IUserSimulator
from recommender.recommender_interface import IRecommenderSystem


class Environment:
    def __init__(self, user: IUserSimulator, recommender: IRecommenderSystem):
        self.user = user
        self.recommender = recommender

    def run(self):
        print("Environment is running ...")
        print("-" * 40)

        next_recommender_response = None
        while True:
            user_msg = self.user.chat(next_recommender_response)
            if "###STOP###" in user_msg:
                break

            print(f"User: {user_msg}")

            next_recommender_response = self.recommender.chat(user_msg)
            print(f"Recommender: {next_recommender_response}")
