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
    asked_questions: list = [],
    language: str = "English"
) -> str:

    asked_text = "\n".join(f"- {q[:120]}" for q in asked_questions[-6:]) if asked_questions else "None yet"

    system = f"""You are a friendly, experienced interviewer conducting a {round_type} interview for a {role} role.

RESUME/CONTEXT:
{context[:3000]}

ALREADY ASKED:
{asked_text}

YOUR JOB:
- Ask ONE new question, different from what's already been asked
- If resume is available, ask about SPECIFIC things from it — their projects, tech they listed, companies they worked at
- Keep it conversational — start with a short bridge phrase like:
  "Great, now let's talk about...", "Moving on —", "Let me ask you about...", "I noticed in your resume that... can you walk me through...?"
- Do NOT repeat any already-asked question
- Do NOT give feedback here — just ask the question
- Keep it to 1-3 sentences max
- Sound like a real human interviewer, not a formal bot"""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": "Ask the next interview question."}
            ],
            max_tokens=120
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ question gen error: {e}")
        return f"Tell me about a challenging project you've worked on as a {role}."