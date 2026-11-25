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
class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class CategoryRead(ORM):
    id: int
    name: str


# ---------- тесты (товары) ----------
class TestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=2000)
    difficulty: Difficulty = "medium"
    duration_minutes: int = Field(ge=1, le=300)
    pass_score: int = Field(default=60, ge=1, le=100)
    price: int = Field(default=0, ge=0, le=1_000_000, description="Цена одной попытки, тенге")
    category_id: int


class TestRead(TestCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: CategoryRead


class TestPage(BaseModel):
    items: list[TestRead]
    total: int
    page: int
    pages: int