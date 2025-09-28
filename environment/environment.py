from user_simulator.user_interface import IUserSimulator
from recommender.recommender_interface import IRecommenderSystem
from judge.judge_interface import IJudge
from evaluation.conversation_evaluator import ConversationEvaluator
import re


class Environment:
    def __init__(self, args, user: IUserSimulator, recommender: IRecommenderSystem):
        self.args = args
        self.user = user
        self.recommender = recommender
        self.conversation_log = []
        self.outcome = None  # store outcome as dict

    # def run(self):
    #     print("Environment is running ...")
    #     print("-" * 40)

    #     next_recommender_response = None
    #     while True:
    #         user_msg = self.user.chat(next_recommender_response)
    #         if "###BUY###" in user_msg or "###ABORT###" in user_msg:
    #             print("\n" + "*"*90 + "\n" + f"User: {user_msg}")
    #             break

    #         print("\n" + "="*90 + "\n" + f"User: {user_msg}")

    #         next_recommender_response = self.recommender.chat(user_msg)
    #         print("\n" + "="*90 + "\n" + f"Recommender: {next_recommender_response}")

    def run(self):
        print("Environment is running ...")
        print("-" * 40)

        next_recommender_response = None
        self.conversation_log = []
        self.outcome = None

        while True:
            # user simulation
            user_msg = self.user.chat(next_recommender_response)
            self.conversation_log.append({"role": "user", "content": user_msg})

            if "###BUY###" in user_msg or "###ABORT###" in user_msg:
                if self.args.verbose:
                    print("\n" + "*"*90 + "\n" + f"User: {user_msg}")

                if "###BUY###" in user_msg and self.args.evaluate:
                    match = re.search(r"^(.*?)###BUY###", user_msg.strip(), re.IGNORECASE)
                    car_name = match.group(1).strip() if match and match.group(1).strip() else None
                    self.outcome = {"score": 1, "decision": "BUY", "car_name": car_name}

                elif "###ABORT###" in user_msg and self.args.evaluate:
                    self.outcome = {"score": 0, "decision": "ABORT", "car_name": None}

                break  # terminate loop

            # recommender simulation
            print("\n" + "="*90 + "\n" + f"User: {user_msg}")
            next_recommender_response = self.recommender.chat(user_msg)
            self.conversation_log.append({"role": "assistant", "content": next_recommender_response})
            print("\n" + "="*90 + "\n" + f"Recommender: {next_recommender_response}")

        # ---- run evaluator AFTER loop ends ----
        if self.outcome and self.args.evaluate:
            evaluator = ConversationEvaluator(self.conversation_log, getattr(self.user, "location", None))
            extra_metrics = evaluator.evaluate_all()
            self.outcome.update(extra_metrics)

            print(f"\nConversation Outcome: {self.outcome}")


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
