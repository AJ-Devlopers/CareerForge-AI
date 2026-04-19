"""
question_generator.py
Generates ONE new interview question using Groq LLaMA.
Uses resume context from RAG retriever to make questions personal.
"""

from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))



def generate_question(
    role: str,
    round_type: str,
    context: str,
    asked_questions: list = None,
    language: str = "English"
) -> str:

    asked_list = asked_questions or []
    asked_text = "\n".join(f"- {q}" for q in asked_list[-10:]) if asked_list else "None yet."

    prompt = f"""You are a professional {round_type} interviewer for a {role} position.

Candidate's resume context (use this to make questions specific and relevant):
{context}

Questions already asked (DO NOT repeat these or ask anything similar):
{asked_text}

Instructions:
- Ask EXACTLY ONE new question
- Make it specific to the candidate's resume context above when possible
- Match the difficulty and style of a real {round_type} interview
- Keep it concise — one clear question only
- Language: {language}
- Do NOT include any preamble, numbering, or prefix like "Question:"

Output: Only the question itself.
"""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )

    return res.choices[0].message.content.strip()