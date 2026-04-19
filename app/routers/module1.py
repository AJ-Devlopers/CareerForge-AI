from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.modules.module1_genai.pipeline import run_module1_pipeline
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
        context={
            "request": request,
            "result": result
        }
    )


# =============================
# UPLOAD + PROCESS
# =============================
@router.post("/upload", response_class=HTMLResponse)
async def upload_resume(request: Request, file: UploadFile = File(...)):

    contents = await file.read()

    # 🔹 clear old session
    old_id = request.session.get("session_id")
    if old_id and old_id in report_store:
        del report_store[old_id]

    # 🔹 run pipeline
    result = run_module1_pipeline(contents)

    # 🔹 store result
    session_id = str(uuid.uuid4())
    report_store[session_id] = result

    # 🔹 save session
    request.session.clear()
    request.session["session_id"] = session_id

    return templates.TemplateResponse(
        request=request,
        name="module1.html",
        context={
            "request": request,
            "result": result
        }
    )


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