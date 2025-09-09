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
    # user = UserImplementation(persona_str=Performance_Driven_Adventurer)
    # recommender = RecommenderImplementation()
    # env = Environment(user, recommender)
    # env.run()

    conversation = [
        {"role": "user", "content": "Hey there, I'm looking for a new car that can deliver"
                                    " excellent performance and handling. Any recommendations?"},


        {"role": "assistant", "content": """
Hey! I'm excited to help you find the perfect car! Since you're looking for excellent performance and handling, we might want to consider some sporty options. 

Before we dive into specific recommendations, could you share a bit about your budget? This will help me narrow down the choices to fit your needs!
        """},


        {"role": "user", "content": "Absolutely! I'm willing to invest in high-performance and cutting-edge technology."
                                    " Performance is key for me!"},


        {"role": "assistant", "content": """
Got it! It sounds like you're ready to invest in something truly special. High-performance cars often come with a higher price tag, so let's set a budget that reflects that. 

How about we aim for a budget of around $50,000 and up? Does that sound good to you, or do you have a specific figure in mind?
        """},


        {"role": "user", "content": "A budget starting at $50,000 sounds reasonable, especially for top-notch"
                                    " performance. I'm open to exploring options that might be a bit above that"
                                    " if the car truly stands out in handling and speed."},


        {"role": "assistant", "content": """
Perfect! With a budget starting at $50,000 and a focus on performance and handling, we have some exciting options to explore. 

Here are a couple of standout cars that fit your criteria:

1. **Porsche Macan (2017)**
   - **Price:** $69,505
   - **Engine Size:** 3604.0
   - **Fuel Type:** Petrol
   - **Gas Emission:** 217.0
   - This compact SUV offers a sporty drive with excellent handling, making it a great choice for performance enthusiasts.

2. **Porsche 911 (2017)**
   - **Price:** $111,802
   - **Engine Size:** 3996.0
   - **Fuel Type:** Petrol
   - **Gas Emission:** 290.0
   - The 911 is a legendary sports car known for its incredible performance and handling. It’s a bit above your budget, but it’s hard to beat in terms of driving experience.

3. **Tesla Model S (2016)**
   - **Price:** $119,080
   - **Engine Size:** 0.0 (Electric)
   - **Gas Emission:** 0.0
   - If you're open to electric vehicles, the Model S offers mind-blowing acceleration and cutting-edge technology, making it a top contender for performance.

Which of these options catches your eye? Or would you like to explore more choices?
        """}
    ]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    judge = JudgeImplementation(llm)
    for msg in conversation[:2]:
        judge.add_interaction(msg)

    judge.evaluate_user_simulation(Performance_Driven_Adventurer, RAW_REVIEW)
