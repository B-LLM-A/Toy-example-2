from user_simulator.user_interface import IUserSimulator
from recommender.recommender_interface import IRecommenderSystem
from judge.judge_interface import IJudge


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

            print("\n" + "="*30 + "\n" + f"User: {user_msg}")

            next_recommender_response = self.recommender.chat(user_msg)
            print("\n" + "="*30 + "\n" + f"Recommender: {next_recommender_response}")

    def evaluate(self, judge: IJudge):
        print("Evaluation is running ...")
        print("-" * 40)

        next_recommender_response = None
        while True:
            user_msg = self.user.chat(next_recommender_response)
            if "###STOP###" in user_msg:
                break

            print("\n" + "="*30 + "\n" + f"User: {user_msg}")
            judge.add_interaction({
                "role": "user",
                "content": user_msg
            })

            next_recommender_response = self.recommender.chat(user_msg)
            print("\n" + "="*30 + "\n" + f"Recommender: {next_recommender_response}")
            judge.add_interaction({
                "role": "assistant",
                "content": next_recommender_response
            })

        user_simulation_evaluation = judge.evaluate_user_simulation(
            persona=self.user.persona,
            raw_review=self.user.raw_review
        )
        print("\n" + "="*30 + "\n" + f"User Simulation Evaluation:\n {user_simulation_evaluation}")

        recommender_evaluation = judge.evaluate_recommender()
        print("\n" + "="*30 + "\n" + f"Recommender Evaluation:\n {recommender_evaluation}")
