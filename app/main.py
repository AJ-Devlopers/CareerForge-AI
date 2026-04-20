from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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