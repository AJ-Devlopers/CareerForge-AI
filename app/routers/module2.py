from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uuid

from app.modules.module2_rag.rag_pipeline import generate_next_question
from app.modules.module2_rag.smart_reply import generate_smart_reply
from app.modules.module2_rag.session_manager import (
    create_session,
    add_message,
    get_history
)
from app.modules.module2_rag.session_manager import create_session, add_message, get_history
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# =============================
# LOAD MODULE 2 PAGE
# =============================
@router.get("/module2", response_class=HTMLResponse)
def module2_page(request: Request, role: str = ""):

    # New session per page load
    session_id = str(uuid.uuid4())
    request.session["module2_session"] = session_id
    create_session(session_id)

    return templates.TemplateResponse(
        request=request,
        name="module2.html",
        context={"request": request, "role": role}
    )


# =============================
# GENERATE NEXT QUESTION
# Smart: first acknowledge user's answer, then ask next question
# Sessions are isolated per round (round key stored in session)
# =============================
@router.post("/module2/next-question")
async def next_question(request: Request):

    data        = await request.json()
    role        = data.get("role", "Software Engineer")
    round_type  = data.get("round", "technical")
    user_answer = data.get("answer", "").strip()

    # ── session key is role+round combo so each round is isolated ──
    base_session = request.session.get("module2_session", str(uuid.uuid4()))
    session_key  = f"{base_session}_{round_type}"

    # create if first message in this round
    create_session(session_key)

    history = get_history(session_key)

    # ── If user just said "start" or similar greeting, skip feedback ──
    starter_words = {"start", "hi", "hello", "hey", "begin", "go", "ok", "okay", "ready", "yes"}
    is_starter    = user_answer.lower().strip(".!?") in starter_words

    combined_response = ""

    if user_answer and not is_starter and history:
        # save user answer
        add_message(session_key, "user", user_answer)

        # generate smart acknowledgement / feedback
        smart_fb = generate_smart_reply(
            role=role,
            round_type=round_type,
            user_answer=user_answer,
            history=history
        )
        combined_response += smart_fb + "\n\n"
        add_message(session_key, "assistant", smart_fb)

    elif user_answer:
        add_message(session_key, "user", user_answer)

    # ── generate next question ──
    asked_questions = [
        msg["content"]
        for msg in get_history(session_key)
        if msg["role"] == "assistant"
    ]

    question = generate_next_question(
        role=role,
        round_type=round_type,
        asked_questions=asked_questions
    )

    add_message(session_key, "assistant", question)

    combined_response += question

    return JSONResponse({
        "question": combined_response,
        "history":  get_history(session_key)
    })


# =============================
# RESET (per round)
# =============================
@router.post("/module2/reset")
async def reset_session(request: Request):
    data       = await request.json()
    round_type = data.get("round", "technical")
    base       = request.session.get("module2_session", "")
    key        = f"{base}_{round_type}"
    create_session(key)
    return JSONResponse({"status": "reset"})



# =============================
# GENERAL DISCUSSION ENDPOINT
# Plain chatbot — no interview format, no question forcing
# =============================
@router.post("/module2/discuss")
async def discuss(request: Request):
 
    data        = await request.json()
    user_message = data.get("message", "").strip() or data.get("answer", "").strip()
    role         = data.get("role", "General")
 
    # isolated session for discussion
    base_session = request.session.get("module2_session", str(uuid.uuid4()))
    session_key  = f"{base_session}_discussion"
    create_session(session_key)
 
    if user_message:
        add_message(session_key, "user", user_message)
 
    history = get_history(session_key)
 
    # build history for groq
    history_msgs = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-12:]   # last 12 turns
    ]
 
    system_prompt = f"""You are CareerForge AI — a friendly, knowledgeable career assistant.
The user may be targeting the role: {role}.
 
Your personality:
- Warm, conversational, like a smart friend who knows tech and careers
- Reply naturally to casual messages, slangs, greetings ("yo", "hey", "wassup", "lol", "idk" etc.)
- Give real, actionable advice — not generic filler
- Use bullet points or short paragraphs when listing things
- Keep replies concise unless a detailed answer is needed
- Topics you help with: career advice, skill roadmaps, resume tips, interview prep, salary negotiation, tech stacks, job market, learning resources, project ideas, anything career/tech related
- If asked something completely off-topic (movies, cricket etc.) just give a brief fun reply and gently steer back
 
Never say you are an AI made by Anthropic or OpenAI. You are CareerForge AI.
"""
 
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                *history_msgs
            ],
            max_tokens=400
        )
        reply = res.choices[0].message.content.strip()
 
    except Exception as e:
        reply = "Hmm, something went wrong on my end. Try again?"
 
    add_message(session_key, "assistant", reply)
 
    return JSONResponse({
        "reply":   reply,
        "history": get_history(session_key)
    })