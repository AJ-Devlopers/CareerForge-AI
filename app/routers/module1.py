from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.modules.module1_genai.pipeline import run_module1_pipeline
from app.modules.module1_genai.llm_service import generate_role_skills
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# 🔹 In-memory store
report_store = {}


# =============================
# GET PAGE
# =============================
@router.get("/", response_class=HTMLResponse)
def module1_page(request: Request):
    session_id = request.session.get("session_id")
    result = report_store.get(session_id) if session_id else None
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

    old_id = request.session.get("session_id")
    if old_id and old_id in report_store:
        del report_store[old_id]

    result = run_module1_pipeline(file)

    session_id = str(uuid.uuid4())
    report_store[session_id] = result

    request.session["session_id"] = session_id
    request.session["resume_data"] = {
        "name":         result.get("name", ""),
        "ats_score":    result.get("ats_score", ""),
        "skills_found": result.get("skills_found", []),
        "resume_text":  result.get("resume_text", ""),
    }
    print("SESSION DATA:", request.session.get("resume_data"))
    print("SKILLS SAVED:", request.session.get("resume_data", {}).get("skills_found", [])[:5])

    # ── ADD THIS DEBUG PRINT ──
    print("✅ SESSION SET:", request.session.get("resume_data", {}).get("name"))
    print("✅ SESSION ID:", session_id)
    print("✅ SKILLS:", result.get("skills_found", []))

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


@router.post("/analyze-custom-role")
async def analyze_custom_role(request: Request):
    try:
        data = await request.json()
        role = data.get("role", "").strip()

        if not role:
            return JSONResponse({"error": "Role required"}, status_code=400)

        # ── Pull user skills from report_store OR session fallback ──
        resume_data = request.session.get("resume_data", {})

        print("📦 SESSION DATA:", resume_data)

        user_skills = [
            s.lower().strip()
            for s in resume_data.get("skills_found", [])
        ]  

        print(f"🔍 Custom role check — user skills count: {len(user_skills)}, role: {role}")

        # ── AI call to get required skills for this role ──
        role_skills_raw = generate_role_skills(role)

        if not role_skills_raw:
            raise Exception("Empty skills from LLM")

        # Normalize: lowercase, strip, remove empty, remove punctuation artifacts
        role_skills = list(set(
            s.lower().strip().strip(".,;:")
            for s in role_skills_raw
            if s.strip()
        ))

        print(f"🔍 Role skills fetched: {role_skills[:8]}")
        print(f"🔍 User skills sample: {user_skills[:8]}")

        # ── Fuzzy-ish match: check if any user skill is contained in or contains role skill ──
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