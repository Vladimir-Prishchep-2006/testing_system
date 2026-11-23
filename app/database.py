from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine("sqlite:///./testing.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Зависимость FastAPI: открывает сессию БД на время запроса и закрывает её."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()