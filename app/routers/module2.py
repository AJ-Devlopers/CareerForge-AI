from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uuid

# 🔥 RAG PIPELINE
from app.modules.module2_rag.rag_pipeline import generate_next_question

# 🔥 SESSION MANAGER
from app.modules.module2_rag.session_manager import (
    create_session,
    add_message,
    get_history
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# 🔥 In-memory session store (simple)
active_sessions = {}


# =============================
# LOAD MODULE 2 PAGE
# =============================
@router.get("/module2", response_class=HTMLResponse)
def module2_page(request: Request, role: str = ""):

    # 🔹 Create new session
    session_id = str(uuid.uuid4())
    request.session["module2_session"] = session_id

    # 🔹 Initialize session memory
    create_session(session_id)

    return templates.TemplateResponse(
        request=request,
        name="module2.html",
        context={
            "request": request,
            "role": role
        }
    )


# =============================
# GENERATE NEXT QUESTION
# =============================
@router.post("/module2/next-question")
async def next_question(request: Request):

    data = await request.json()

    role = data.get("role", "Software Engineer")
    round_type = data.get("round", "technical")
    user_answer = data.get("answer", "")

    # 🔹 Get session
    session_id = request.session.get("module2_session")

    if not session_id:
        return JSONResponse({"error": "Session expired"}, status_code=400)

    # 🔹 Save user answer (if exists)
    if user_answer:
        add_message(session_id, "user", user_answer)

    # 🔹 Get full history
    history = get_history(session_id)

    # 🔥 Extract already asked questions (assistant messages)
    asked_questions = [
        msg["content"]
        for msg in history
        if msg["role"] == "assistant"
    ]

    # 🔥 Generate next question (NO REPEATS)
    question = generate_next_question(
        role=role,
        round_type=round_type,
        asked_questions=asked_questions
    )

    # 🔹 Save AI question
    add_message(session_id, "assistant", question)

    return JSONResponse({
        "question": question,
        "history": history
    })

# =============================
# RESET SESSION (OPTIONAL)
# =============================
@router.post("/module2/reset")
async def reset_session(request: Request):

    session_id = request.session.get("module2_session")

    if session_id:
        create_session(session_id)

    return JSONResponse({"status": "reset"})
