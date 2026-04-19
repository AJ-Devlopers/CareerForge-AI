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

    request.session.clear()
    request.session["session_id"] = session_id

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
# ✅ Route is /analyze-custom-role
# Because router is mounted at /module1,
# full path = /module1/analyze-custom-role
# =============================
@router.post("/analyze-custom-role")
async def analyze_custom_role(request: Request):
    try:
        data = await request.json()
        role = data.get("role", "").strip()

        if not role:
            return JSONResponse({"error": "Role required"}, status_code=400)

        session_id = request.session.get("session_id")
        result     = report_store.get(session_id)

        user_skills = []
        if result:
            user_skills = [s.lower() for s in result.get("skills_found", [])]

        # AI call to get required skills for this role
        role_skills_raw = generate_role_skills(role)

        if not role_skills_raw:
            raise Exception("Empty skills from LLM")

        role_skills = [s.lower().strip() for s in role_skills_raw if s.strip()]

        matched = list(set(user_skills) & set(role_skills))

        match_pct = 0
        if role_skills:
            match_pct = int((len(matched) / len(role_skills)) * 100)
            if len(matched) >= 3:
                match_pct += 10
            match_pct = min(match_pct, 100)

        return JSONResponse({
            "role":           role,
            "match":          match_pct,
            "role_skills":    [s.title() for s in role_skills],
            "matched_skills": [s.title() for s in matched]
        })

    except Exception as e:
        print("❌ ERROR:", str(e))
        return JSONResponse({"error": str(e)}, status_code=500)