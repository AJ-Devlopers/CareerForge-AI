from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

# 🔥 IMPORT ROUTERS
from app.routers import module1, module2, module3

load_dotenv()

app = FastAPI(title="CareerForge AI")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "supersecretkey"),
    max_age=7200,
    same_site="lax",
    https_only=False
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={"request": request}
    )


app.include_router(module1.router, prefix="/module1")
app.include_router(module2.router)
app.include_router(module3.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/session/clear-all")
async def clear_all_sessions(request: Request):
    """Clears ALL session data — module1 report store, module2, module3."""
    from app.routers.module1 import report_store

    session_id = request.session.get("session_id")
    if session_id and session_id in report_store:
        del report_store[session_id]

    request.session.clear()

    return JSONResponse({"status": "cleared", "message": "All session data cleared"})