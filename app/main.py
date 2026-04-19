from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

from app.routers import module1

# 🔹 Load env
load_dotenv()

# 🔹 Create app
app = FastAPI(title="CareerForge AI")

# 🔹 Session middleware (IMPORTANT for SSR)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "supersecretkey")
)

# 🔹 Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 🔹 Templates
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
# MODULE 1 ROUTER
# =============================
app.include_router(module1.router, prefix="/module1")


# =============================
# HEALTH CHECK
# =============================
@app.get("/health")
def health_check():
    return {"status": "ok"}