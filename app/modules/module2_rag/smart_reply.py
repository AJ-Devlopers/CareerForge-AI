"""
smart_reply.py
Generates a brief, human acknowledgement of the candidate's answer
before the next question is asked. Makes the bot feel like a real interviewer.
"""

from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_smart_reply(role: str, round_type: str, user_answer: str, history: list) -> str:
    """
    Given the candidate's latest answer, produce a short interviewer-style
    response: acknowledge, give brief feedback, then naturally transition
    to the next question (the next question is appended by rag_pipeline separately).
    """

    # build a compact history string (last 6 turns max)
    recent = history[-6:] if len(history) > 6 else history
    history_text = "\n".join(
        f"{'Interviewer' if m['role'] == 'assistant' else 'Candidate'}: {m['content']}"
        for m in recent
    )

    prompt = f"""You are an expert interviewer conducting a {round_type} interview for a {role} position.

Conversation so far:
{history_text}

Candidate just said:
\"{user_answer}\"

Your task: Write a SHORT (2-4 sentences) natural interviewer response that:
1. Briefly acknowledges what they said (don't just repeat it)
2. Gives ONE line of constructive feedback or positive reinforcement
3. Ends with a soft transition phrase like "Let me ask you something else..." or "Building on that..."

Do NOT ask the next question yet — just the acknowledgement and transition.
Keep it conversational and human. No bullet points. No headers.
"""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )

    return res.choices[0].message.content.strip()