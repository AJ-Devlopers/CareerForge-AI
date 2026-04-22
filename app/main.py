from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

# 🔥 IMPORT ROUTERS
from app.routers import module1, module2


# =============================
# LOAD ENV VARIABLES
# =============================
load_dotenv()


# =============================
# CREATE FASTAPI APP
# =============================
app = FastAPI(title="CareerForge AI")


# =============================
# SESSION MIDDLEWARE (IMPORTANT)
# =============================
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "supersecretkey"),
    max_age=7200,
    same_site="lax",
    https_only=False
)


# =============================
# STATIC FILES (CSS / JS)
# =============================
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# =============================
# TEMPLATES (JINJA2)
# =============================
templates = Jinja2Templates(directory="app/templates")


# =============================
# LANDING PAGE
# =============================
@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={"request": request}
    )


# =============================
# MODULE 1 ROUTES
# =============================
app.include_router(module1.router, prefix="/module1")


# =============================
# MODULE 2 ROUTES ✅
# =============================
app.include_router(module2.router)


# =============================
# HEALTH CHECK
# =============================
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/session/clear-all")
async def clear_all_sessions(request: Request):
    """Clears all module sessions — module1 report store, module2 interview results."""
    from app.routers.module1 import report_store

    # Clear module1 report store
    session_id = request.session.get("session_id")
    if session_id and session_id in report_store:
        del report_store[session_id]

    # Wipe entire server session (covers module2 interview_results, module2_session, etc.)
    request.session.clear()

    return JSONResponse({"status": "cleared"})