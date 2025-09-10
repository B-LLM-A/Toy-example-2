JUDGE_RECOMMENDER_MESSAGE_PROMPT_TEMPLATE = """
You are an impartial judge, evaluate the LAST MESSAGE based on the context.
The system you are judging is a car recommender agent, which has to infer the user's preferences and decision making
and suggest cars based on those

=== CONTEXT ===
{context}

=== LAST MESSAGE ===
{message}

=== CRITERIA ===
{criteria}

Instructions:
- before assigning output think thoroughly and make logical reasoning 
- Score each criterion from 1 (worst) to 10 (best).
"""


JUDGE_RECOMMENDER_CONVERSATION_PROMPT_TEMPLATE = """
You are an impartial judge, evaluate the CONVERSATION based on the context.
The system you are judging is a car recommender agent, which has to infer the user's preferences and decision making
and suggest cars based on those

=== CONVERSATION ===
{conversation}

=== CRITERIA ===
{criteria}

Instructions:
- before assigning output think thoroughly and make logical reasoning 
- Score each criterion from 1 (worst) to 10 (best).
"""


JUDGE_USER_MESSAGE_PROMPT_TEMPLATE = """
You are an impartial judge, evaluate the LAST MESSAGE based on the context.
The system you are judging is a user simulator agent, which is responsible for mimicking the user aligned with the 
following persona:
==== PERSONA =====
{persona}

this user commented this review on an online platform:
==== REVIEW =====
{review}

=== CONTEXT ===
{context}

=== LAST MESSAGE ===
{message}

=== CRITERIA ===
{criteria}

Instructions:
- before assigning output think thoroughly and make logical reasoning 
- Score each criterion from 1 (worst) to 10 (best).
"""


JUDGE_USER_CONVERSATION_PROMPT_TEMPLATE = """
You are an impartial judge, evaluate the CONVERSATION based on the context.
The system you are judging is a user simulator agent, which is responsible for mimicking the user aligned with the 
following persona:
==== PERSONA =====
{persona}

this user commented this review on an online car platform:
==== REVIEW =====
{review}

=== CONVERSATION ===
{conversation}

=== CRITERIA ===
{criteria}

Instructions:
- before assigning output think thoroughly and make logical reasoning 
- Score each criterion from 1 (worst) to 10 (best).
"""
