import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_role_explanation(role):

    prompt = f"""
    You are a career advisor.

    Explain the role "{role}" in 2-3 simple lines for a student.
    Keep it clear and practical.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # 🔥 UPDATED HERE
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return "Description not available"