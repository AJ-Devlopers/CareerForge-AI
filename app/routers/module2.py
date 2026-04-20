# app/routers/module2.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uuid, os
from groq import Groq

from app.modules.module2_rag.rag_pipeline    import generate_next_question
from app.modules.module2_rag.smart_reply     import generate_smart_reply
from app.modules.module2_rag.session_manager import (
    create_session, add_message, get_history
)
from dotenv import load_dotenv
load_dotenv()

router    = APIRouter()
templates = Jinja2Templates(directory="app/templates")
client    = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── PAGE ─────────────────────────────────────────────────────
@router.get("/module2", response_class=HTMLResponse)
def module2_page(request: Request, role: str = ""):

    resume_data = request.session.get("resume_data", {})
    
    # ── ADD THIS DEBUG PRINT ──
    print("📦 MODULE2 SESSION:", resume_data)
    print("📦 SESSION KEYS:", list(request.session.keys()))

    candidate_name = resume_data.get("name", "")
    ats_score      = resume_data.get("ats_score", None)
    skills_found   = resume_data.get("skills_found", [])
    resume_text    = resume_data.get("resume_text", "")
    has_resume     = bool(resume_text)

    session_id = str(uuid.uuid4())
    request.session["module2_session"] = session_id
    create_session(session_id)

    final_role = role or resume_data.get("selected_role", "")

    return templates.TemplateResponse(
    request=request,
    name="module2.html",
    context={
        "request":        request,
        "role":           final_role    or "",
        "candidate_name": candidate_name or "",
        "ats_score":      ats_score     or "",
        "skills_found":   skills_found  or [],
        "resume_text":    resume_text   or "",
        "has_resume":     has_resume,
    }
)
# ── INTERVIEW QUESTION ───────────────────────────────────────
@router.post("/module2/next-question")
async def next_question(request: Request):

    data        = await request.json()
    role        = data.get("role", "Software Engineer")
    round_type  = data.get("round", "technical")
    user_answer = data.get("answer", "").strip()
    resume_text = data.get("resume_text", "")

    # Always fallback to server session for resume
    resume_data = request.session.get("resume_data", {})
    if not resume_text:
        resume_text = resume_data.get("resume_text", "")

    candidate_name = resume_data.get("name", "")
    skills_found   = resume_data.get("skills_found", [])

    base_session = request.session.get("module2_session", str(uuid.uuid4()))
    session_key  = f"{base_session}_{round_type}"
    create_session(session_key)

    history = get_history(session_key)

    starters = {
        "start", "hi", "hello", "hey", "begin", "go",
        "ok", "okay", "ready", "yes", "sure", "yep",
        "let's go", "yeah", "lets go"
    }
    is_starter = user_answer.lower().strip(".!?") in starters

    combined = ""

    if user_answer and not is_starter and history:
        add_message(session_key, "user", user_answer)
        # ── CONVERSATIONAL FEEDBACK ──
        fb = generate_conversational_feedback(
            role, round_type, user_answer, history,
            candidate_name, skills_found, resume_text
        )
        combined += fb + "\n\n"
        add_message(session_key, "assistant", fb)
    elif user_answer:
        add_message(session_key, "user", user_answer)

    asked = [
        m["content"]
        for m in get_history(session_key)
        if m["role"] == "assistant"
    ]

    question = generate_next_question(
        role=role,
        round_type=round_type,
        asked_questions=asked,
        resume_text=resume_text
    )

    add_message(session_key, "assistant", question)
    combined += question

    return JSONResponse({
        "question": combined,
        "history":  get_history(session_key)
    })


# ── CONVERSATIONAL FEEDBACK (replaces generate_smart_reply) ──
def generate_conversational_feedback(
    role, round_type, user_answer, history,
    candidate_name="", skills_found=[], resume_text=""
):
    name_part   = f" {candidate_name.split()[0]}" if candidate_name else ""
    skills_part = ", ".join(skills_found[:8]) if skills_found else ""
    resume_part = f"\nResume excerpt:\n{resume_text[:1500]}" if resume_text else ""

    history_msgs = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-10:]
    ]

    system = f"""You are an experienced, friendly interviewer conducting a {round_type} interview for a {role} role.

Candidate name: {candidate_name or "the candidate"}
Their skills from resume: {skills_part}
{resume_part}

YOUR STYLE — this is critical:
- Be warm and conversational, like a real human interviewer
- Give SHORT reactions first: "Nice!", "Good thinking!", "Hmm, interesting approach!", "That's solid!", "Love that answer!", "Good, but let me push back a bit..."
- Then give BRIEF, specific feedback (2-3 sentences max)
- Reference their actual resume/skills when relevant
- If answer is weak: be kind but honest — "That's a decent start, though I'd love to hear more about..."
- If answer is strong: be genuinely enthusiastic — "That's exactly the kind of thinking we look for!"
- Keep it under 80 words total
- DO NOT ask the next question here — just react + feedback
- Sound like a real person, not a bot"""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                *history_msgs,
                {"role": "user", "content": user_answer}
            ],
            max_tokens=150
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ feedback error: {e}")
        return "Got it! Let me ask you another one."


# ── GENERAL DISCUSSION ───────────────────────────────────────
@router.post("/module2/discuss")
async def discuss(request: Request):

    data           = await request.json()
    user_message   = (data.get("message") or data.get("answer") or "").strip()
    role           = data.get("role", "General")

    resume_data    = request.session.get("resume_data", {})
    candidate_name = resume_data.get("name", "") or data.get("candidate_name", "")
    skills_found   = resume_data.get("skills_found", [])
    resume_text    = resume_data.get("resume_text", "")

    base_session = request.session.get("module2_session", str(uuid.uuid4()))
    session_key  = f"{base_session}_discussion"
    create_session(session_key)

    if user_message:
        add_message(session_key, "user", user_message)

    history      = get_history(session_key)
    history_msgs = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-14:]
    ]

    first_name  = candidate_name.split()[0] if candidate_name else ""
    skills_part = ", ".join(skills_found[:10]) if skills_found else ""
    resume_part = f"\nTheir resume:\n{resume_text[:1500]}" if resume_text else ""
    name_line   = f"The candidate's name is {candidate_name} (call them {first_name})." if candidate_name else ""

    system_prompt = f"""You are CareerForge AI — a friendly, sharp career assistant. {name_line}
Their skills: {skills_part}
{resume_part}
Targeting: {role}.

Style:
- Warm, conversational, like a smart friend who knows tech and careers
- Reference their actual resume/skills/projects when giving advice — be SPECIFIC
- Handle slangs naturally: "yo", "hey", "wassup", "lol" — reply in kind
- Give real actionable advice, no filler
- Brief fun reply if off-topic, then steer back
- If you know their skills, give personalized roadmap/advice based on them

This is FREE-FORM CHAT. Be a helpful friend, not a formal bot."""

    try:
        res   = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                *history_msgs
            ],
            max_tokens=500
        )
        reply = res.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ /discuss error: {e}")
        reply = "Oops, something broke. Try again!"

    add_message(session_key, "assistant", reply)
    return JSONResponse({
        "reply":   reply,
        "history": get_history(session_key)
    })


# ── RESET ────────────────────────────────────────────────────
@router.post("/module2/reset")
async def reset_session(request: Request):
    data       = await request.json()
    round_type = data.get("round", "technical")
    base       = request.session.get("module2_session", "")
    create_session(f"{base}_{round_type}", force_reset=True)
    return JSONResponse({"status": "reset"})