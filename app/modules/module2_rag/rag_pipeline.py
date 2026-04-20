from app.modules.module2_rag.retriever import retrieve_context
from app.modules.module2_rag.question_generator import generate_question


def generate_next_question(
    role: str,
    round_type: str,
    asked_questions: list = [],
    resume_text: str = "",
    language: str = "English"
) -> str:

    query             = f"{role} interview {round_type}"
    retrieved_context = retrieve_context(query)

    if resume_text:
        full_context = (
            f"CANDIDATE RESUME (use this to ask SPECIFIC questions about their projects, "
            f"skills, and experience — not generic questions):\n{resume_text[:3000]}"
            f"\n\nADDITIONAL CONTEXT:\n{retrieved_context}"
        )
    else:
        full_context = retrieved_context

    question = generate_question(
        role=role,
        round_type=round_type,
        context=full_context,
        asked_questions=asked_questions,
        language=language
    )

    return question


def generate_answer(question: str, chat_history: list = []) -> str:
    """Used by other modules (e.g. module3 question engine)"""
    from groq import Groq
    import os
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": question}
            ],
            max_tokens=500
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return "{}"