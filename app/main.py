from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

from app.routers import module1

load_dotenv()

app = FastAPI(title="CareerForge AI")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY")
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(module1.router)