from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_question(role, round_type, context, asked_questions=None, language="English"):

    asked = "\n".join(asked_questions or [])

    prompt = f"""
    You are a professional interviewer.

    Role: {role}
    Round: {round_type}
    Language: {language}

    Candidate resume context:
    {context}

    Already asked questions:
    {asked}

    Instructions:
    - Ask ONLY ONE new question
    - Do NOT repeat previous questions
    - Keep it realistic and relevant
    - Default language is English unless specified

    Output:
    Only the question
    """

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content.strip()