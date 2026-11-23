from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Category(Base):
    """Предмет или тема (категория каталога)."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    tests: Mapped[list["Test"]] = relationship(back_populates="category")


class Test(Base):
    """Тест — товар каталога. Цена указана за одну попытку прохождения."""
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(String(2000), default="")
    difficulty: Mapped[str] = mapped_column(String(10), default="medium")  # easy | medium | hard
    duration_minutes: Mapped[int]
    pass_score: Mapped[int] = mapped_column(default=60)  # проходной порог, %
    price: Mapped[int] = mapped_column(default=0)  # тенге за одну попытку
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    category: Mapped[Category] = relationship(back_populates="tests")