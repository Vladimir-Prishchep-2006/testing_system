from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import models  # noqa: F401  (регистрирует таблицы в Base.metadata)
from .database import Base, SessionLocal, engine
from .seed import seed

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # создаёт таблицы, если их ещё нет
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="Система онлайн-тестирования и оценки результатов", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def page_home(request: Request):
    return templates.TemplateResponse(request, "home.html")