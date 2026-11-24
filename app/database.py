from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine("sqlite:///./testing.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


@event.listens_for(engine, "connect")
def _unicode_lower(dbapi_conn, _record):
    # Встроенный lower() в SQLite понимает только ASCII, поэтому поиск по русским
    # названиям зависел бы от регистра. Подменяем функцию на Python-версию.
    dbapi_conn.create_function("lower", 1, lambda s: s.lower() if s is not None else None)


class Base(DeclarativeBase):
    pass


def get_db():
    """Зависимость FastAPI: открывает сессию БД на время запроса и закрывает её."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()