from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import models  # noqa: F401  (регистрирует таблицы в Base.metadata)
from .database import Base, SessionLocal, engine
from .routers import auth, cart, catalog
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
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(cart.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def page_catalog(request: Request):
    return templates.TemplateResponse(request, "catalog.html")


@app.get("/tests/{test_id}", include_in_schema=False)
def page_test(request: Request, test_id: int):
    return templates.TemplateResponse(request, "test.html", {"test_id": test_id})

@app.get("/login", include_in_schema=False)
def page_login(request: Request):
    return templates.TemplateResponse(request, "auth.html")

@app.get("/cart", include_in_schema=False)
def page_cart(request: Request):
    return templates.TemplateResponse(request, "cart.html")