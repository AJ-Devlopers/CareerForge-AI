from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_question(role, round_type, context):

    prompt = f"""
    You are an interviewer.

    Role: {role}
    Round: {round_type}

    Candidate resume context:
    {context}

    Ask ONE realistic interview question.

    Rules:
    - No explanation
    - Only question
    - Keep it relevant to resume
    """

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content.strip()