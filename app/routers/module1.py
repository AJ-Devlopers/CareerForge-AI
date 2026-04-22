# app/routers/module1.py

from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.modules.module1_genai.pipeline import run_module1_pipeline
from app.modules.module1_genai.llm_service import generate_role_skills
import uuid

router    = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ── In-memory store (holds full result including resume_text) ──
report_store = {}


# =============================
# GET PAGE
# =============================
@router.get("/", response_class=HTMLResponse)
def module1_page(request: Request):
    session_id = request.session.get("session_id")
    result     = report_store.get(session_id) if session_id else None
    return templates.TemplateResponse(
        request=request,
        name="module1.html",
        context={"request": request, "result": result}
    )


# =============================
# UPLOAD + PROCESS
# =============================
@router.post("/upload")
async def upload_resume(request: Request, file: UploadFile = File(...)):

    # Clear old session data
    old_id = request.session.get("session_id")
    if old_id and old_id in report_store:
        del report_store[old_id]

    # Run full pipeline
    result = run_module1_pipeline(file)

    # Store everything in report_store (server-side, no size limit)
    session_id = str(uuid.uuid4())
    report_store[session_id] = result

    # Session cookie ONLY stores the session_id — tiny, never overflows
    request.session["session_id"] = session_id

    print(f"✅ UPLOAD done — session_id: {session_id}")
    print(f"✅ Name: {result.get('name', '')}")
    print(f"✅ Skills: {result.get('skills_found', [])[:5]}")
    print(f"✅ ATS: {result.get('ats_score', 0)}")

    return JSONResponse(content=result)


# =============================
# CLEAR SESSION
# =============================
@router.post("/clear-session")
async def clear_session(request: Request):
    session_id = request.session.get("session_id")
    if session_id and session_id in report_store:
        del report_store[session_id]
    request.session.clear()
    return RedirectResponse(url="/module1", status_code=303)


# =============================
# CUSTOM ROLE ANALYSIS
# Full path: /module1/analyze-custom-role
# =============================
@router.post("/analyze-custom-role")
async def analyze_custom_role(request: Request):
    try:
        data = await request.json()
        role = data.get("role", "").strip()

        if not role:
            return JSONResponse({"error": "Role required"}, status_code=400)

        # Pull user skills from report_store
        session_id  = request.session.get("session_id")
        stored      = report_store.get(session_id, {})
        user_skills = [s.lower().strip() for s in stored.get("skills_found", [])]

        print(f"🔍 Custom role — session_id: {session_id}")
        print(f"🔍 report_store has session: {session_id in report_store}")
        print(f"🔍 user skills count: {len(user_skills)}, role: {role}")

        # AI call to get required skills for this role
        role_skills_raw = generate_role_skills(role)

        if not role_skills_raw:
            raise Exception("Empty skills from LLM")

        # Normalize
        role_skills = list(set(
            s.lower().strip().strip(".,;:")
            for s in role_skills_raw
            if s.strip()
        ))

        print(f"🔍 Role skills fetched: {role_skills[:8]}")
        print(f"🔍 User skills sample:  {user_skills[:8]}")

        # Fuzzy match — handles "python" vs "python 3" etc.
        matched = []
        for us in user_skills:
            for rs in role_skills:
                if us == rs or us in rs or rs in us:
                    if rs not in matched:
                        matched.append(rs)
                    break

        match_pct = 0
        if role_skills:
            match_pct = int((len(matched) / len(role_skills)) * 100)
            if len(matched) >= 3:
                match_pct += 10
            match_pct = min(match_pct, 100)

        print(f"✅ Match: {match_pct}%, matched: {matched[:5]}")

        return JSONResponse({
            "role":           role,
            "match":          match_pct,
            "role_skills":    [s.title() for s in role_skills],
            "matched_skills": [s.title() for s in matched]
        })

    except Exception as e:
        print("❌ ERROR in analyze-custom-role:", str(e))
        return JSONResponse({"error": str(e)}, status_code=500)