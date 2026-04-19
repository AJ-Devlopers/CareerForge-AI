from app.modules.module2_rag.retriever import retrieve_context
from app.modules.module2_rag.question_generator import generate_question


def generate_next_question(role, round_type, asked_questions=[], language="English"):

    query = f"{role} interview {round_type}"
    context = retrieve_context(query)

    question = generate_question(
        role=role,
        round_type=round_type,
        context=context,
        language=language,
        asked_questions=asked_questions
    )

    return question