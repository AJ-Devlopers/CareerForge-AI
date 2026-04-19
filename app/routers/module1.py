from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.modules.module1_genai.pipeline import run_module1

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# 🏠 HOME PAGE (now at "/")
@router.get("/", response_class=HTMLResponse)
def module1_page(request: Request):
    result = request.session.get("module1_result")

    return templates.TemplateResponse(
        request=request,
        name="module1.html",
        context={
            "request": request,
            "result": result           # None on first visit, populated on return
        }
    )


# 📤 Upload
@router.post("/upload", response_class=HTMLResponse)
async def upload_resume(request: Request, file: UploadFile = File(...)):
    
    contents = await file.read()
    request.session.clear()

    result = run_module1(contents)
    request.session["module1_result"] = result

    return templates.TemplateResponse(
        request=request,
        name="module1.html",
        context={
            "request": request,
            "result": result           # None on first visit, populated on return
        }
    )


# 🔄 Clear session
@router.post("/clear-session")
async def clear_session(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)