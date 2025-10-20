# recommender/chat_interface.py
from recommender.basic_recommender.main_agent import car_recommender_app
from recommender.basic_recommender.state import CarRecommendationState

def chat(user_input: str):
    initial_state = CarRecommendationState(messages=[{"role": "user", "content": user_input}])
    result = car_recommender_app.invoke(initial_state)
    return result["messages"][-1].content
