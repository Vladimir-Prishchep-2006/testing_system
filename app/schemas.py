from typing import Literal

from pydantic import BaseModel, ConfigDict

Difficulty = Literal["easy", "medium", "hard"]


class ORM(BaseModel):
    """Базовый класс: позволяет строить схему прямо из ORM-объекта."""
    model_config = ConfigDict(from_attributes=True)


# ---------- категории ----------
class CategoryRead(ORM):
    id: int
    name: str


# ---------- тесты (товары) ----------
class TestRead(ORM):
    id: int
    title: str
    description: str
    difficulty: Difficulty
    duration_minutes: int
    pass_score: int
    price: int
    category_id: int
    category: CategoryRead


class TestPage(BaseModel):
    items: list[TestRead]
    total: int
    page: int
    pages: int