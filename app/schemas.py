from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Difficulty = Literal["easy", "medium", "hard"]


class ORM(BaseModel):
    """Базовый класс: позволяет строить схему прямо из ORM-объекта."""
    model_config = ConfigDict(from_attributes=True)

# ---------- пользователи ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[\w.-]+$")
    password: str = Field(min_length=6, max_length=100)


class UserRead(ORM):
    id: int
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

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