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

    # ── Pull from report_store (not session cookie) ──
    from app.routers.module1 import report_store
    session_id  = request.session.get("session_id")
    stored      = report_store.get(session_id, {})

    candidate_name = stored.get("name", "")
    ats_score      = stored.get("ats_score", None)
    skills_found   = stored.get("skills_found", [])
    resume_text    = stored.get("resume_text", "")
    has_resume     = bool(resume_text)
    roles          = stored.get("roles", [])

    # Role match % for the selected role
    final_role  = role or request.session.get("selected_role", "")
    role_match  = 0
    if final_role and roles:
        for r in roles:
            if r.get("role", "").lower() == final_role.lower():
                role_match = r.get("match", 0)
                break
        if not role_match and roles:
            role_match = roles[0].get("match", 0)

    print("📦 MODULE2 session_id:", session_id)
    print("📦 MODULE2 has_resume:", has_resume)
    print("📦 MODULE2 skills count:", len(skills_found))

    module2_session = str(uuid.uuid4())
    request.session["module2_session"] = module2_session
    create_session(module2_session)

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
            "role_match":     role_match,
            "roles":          roles[:3],
        }
    )


# ── INTERVIEW QUESTION ───────────────────────────────────────
@router.post("/module2/next-question")
async def next_question(request: Request):

    from app.routers.module1 import report_store

    data        = await request.json()
    role        = data.get("role", "Software Engineer")
    round_type  = data.get("round", "technical")
    user_answer = data.get("answer", "").strip()

    # Always pull resume from report_store
    session_id  = request.session.get("session_id")
    stored      = report_store.get(session_id, {})
    resume_text = stored.get("resume_text", "") or data.get("resume_text", "")

    candidate_name = stored.get("name", "")
    skills_found   = stored.get("skills_found", [])

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


# ── CONVERSATIONAL FEEDBACK ──────────────────────────────────
def generate_conversational_feedback(
    role, round_type, user_answer, history,
    candidate_name="", skills_found=[], resume_text=""
):
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

YOUR STYLE:
- Be warm and conversational, like a real human interviewer
- Give SHORT reactions first: "Nice!", "Good thinking!", "That's solid!", "Love that!"
- Then give BRIEF, specific feedback (2-3 sentences max)
- Reference their actual resume/skills when relevant
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

    from app.routers.module1 import report_store

    data         = await request.json()
    user_message = (data.get("message") or data.get("answer") or "").strip()
    role         = data.get("role", "General")

    session_id     = request.session.get("session_id")
    stored         = report_store.get(session_id, {})
    candidate_name = stored.get("name", "") or data.get("candidate_name", "")
    skills_found   = stored.get("skills_found", [])
    resume_text    = stored.get("resume_text", "")

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


# ── END INTERVIEW + SCORE ────────────────────────────────────
@router.post("/module2/end-interview")
async def end_interview(request: Request):
    """
    Score the completed interview out of 100.
    Store result in session for module3.
    """
    from app.routers.module1 import report_store

    data       = await request.json()
    role       = data.get("role", "Software Engineer")
    round_type = data.get("round", "technical")

    session_id   = request.session.get("session_id")
    stored       = report_store.get(session_id, {})
    resume_text  = stored.get("resume_text", "")
    skills_found = stored.get("skills_found", [])

    base_session = request.session.get("module2_session", "")
    session_key  = f"{base_session}_{round_type}"
    history      = get_history(session_key)

    if not history:
        return JSONResponse({"score": 0, "feedback": "No interview data found.", "breakdown": {}})

    # Build transcript
    transcript = "\n".join(
        f"{'Interviewer' if m['role'] == 'assistant' else 'Candidate'}: {m['content']}"
        for m in history
    )

    skills_part = ", ".join(skills_found[:10]) if skills_found else "not provided"

    prompt = f"""You are an expert technical interviewer evaluating a candidate's performance.

Role: {role}
Round: {round_type}
Candidate skills: {skills_part}

Interview transcript:
{transcript[:4000]}

Evaluate the candidate's performance and return ONLY valid JSON (no markdown, no explanation):

{{
  "score": <integer 0-100>,
  "grade": "<Excellent|Good|Average|Below Average|Poor>",
  "summary": "<2-3 sentence overall summary>",
  "breakdown": {{
    "technical_knowledge": {{"score": <0-25>, "max": 25, "comment": "<brief comment>"}},
    "communication": {{"score": <0-20>, "max": 20, "comment": "<brief comment>"}},
    "problem_solving": {{"score": <0-20>, "max": 20, "comment": "<brief comment>"}},
    "depth_of_answers": {{"score": <0-20>, "max": 20, "comment": "<brief comment>"}},
    "confidence": {{"score": <0-15>, "max": 15, "comment": "<brief comment>"}}
  }},
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<area 1>", "<area 2>", "<area 3>"]
}}"""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2
        )
        raw = res.choices[0].message.content.strip()

        # Strip markdown fences if present
        import re, json
        raw = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)

    except Exception as e:
        print(f"❌ scoring error: {e}")
        result = {
            "score": 50,
            "grade": "Average",
            "summary": "Could not fully evaluate the interview.",
            "breakdown": {},
            "strengths": [],
            "improvements": []
        }

    # ── Store in session for module3 ──
    interview_results = request.session.get("interview_results", [])
    interview_results.append({
        "role":      role,
        "round":     round_type,
        "score":     result.get("score", 0),
        "grade":     result.get("grade", ""),
        "summary":   result.get("summary", ""),
        "breakdown": result.get("breakdown", {}),
        "strengths":     result.get("strengths", []),
        "improvements":  result.get("improvements", []),
    })
    # Keep only last 5 interviews to stay within cookie size
    request.session["interview_results"] = interview_results[-5:]
    request.session["last_interview_score"] = result.get("score", 0)

    print(f"✅ Interview scored: {result.get('score')}/100 for {role} - {round_type}")

    return JSONResponse(result)


# ── ENSURE SCORE EXISTS (called before module3 if no attempts) ──
@router.post("/module2/ensure-score")
async def ensure_score(request: Request):
    """
    If user navigates to module3 without completing any interview,
    store a 0-score placeholder so module3 always has something to work with.
    """
    existing = request.session.get("interview_results", [])
    if not existing:
        request.session["interview_results"] = [{
            "role":      request.session.get("selected_role", "General"),
            "round":     "none",
            "score":     0,
            "grade":     "Not Attempted",
            "summary":   "No interview was completed.",
            "breakdown": {},
            "strengths":    [],
            "improvements": [],
        }]
        request.session["last_interview_score"] = 0
    return JSONResponse({"status": "ok", "score": request.session.get("last_interview_score", 0)})


# ── RESET ────────────────────────────────────────────────────
@router.post("/module2/reset")
async def reset_session(request: Request):
    data       = await request.json()
    round_type = data.get("round", "technical")
    base       = request.session.get("module2_session", "")
    create_session(f"{base}_{round_type}", force_reset=True)
    return JSONResponse({"status": "reset"})