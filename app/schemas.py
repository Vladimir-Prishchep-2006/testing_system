from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    questions_count: int


class TestPage(BaseModel):
    items: list[TestRead]
    total: int
    page: int
    pages: int

# ---------- вопросы ----------
class OptionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    is_correct: bool = False


class QuestionCreate(BaseModel):
    text: str = Field(min_length=3, max_length=1000)
    options: list[OptionCreate] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def at_least_one_correct(self):
        if not any(o.is_correct for o in self.options):
            raise ValueError("Нужен хотя бы один правильный вариант ответа")
        return self


class OptionAdmin(ORM):  # видит администратор: с признаком правильности
    id: int
    text: str
    is_correct: bool


class QuestionAdmin(ORM):
    id: int
    text: str
    options: list[OptionAdmin]


class OptionPublic(ORM):  # видит студент: без признака правильности
    id: int
    text: str


class QuestionPublic(ORM):
    id: int
    text: str
    multiple: bool
    options: list[OptionPublic]



# ---------- корзина ----------
class CartAdd(BaseModel):
    test_id: int
    quantity: int = Field(default=1, ge=1, le=20)


class CartUpdate(BaseModel):
    quantity: int = Field(ge=1, le=20)


class CartItemRead(BaseModel):
    test: TestRead
    quantity: int
    subtotal: int


class CartRead(BaseModel):
    items: list[CartItemRead]
    total: int
    count: int  # число позиций



# ---------- заказы ----------
class OrderItemRead(ORM):
    test_id: int
    title: str
    price: int
    quantity: int


class OrderRead(ORM):
    id: int
    user_id: int
    created_at: datetime
    total: int
    status: str
    items: list[OrderItemRead]


class BalanceRead(ORM):
    test: TestRead
    attempts_left: int

# ---------- попытки ----------
class AttemptStart(BaseModel):
    attempt_id: int
    deadline: datetime
    questions: list[QuestionPublic]


class AnswerIn(BaseModel):
    question_id: int
    option_ids: list[int] = []


class SubmitIn(BaseModel):
    answers: list[AnswerIn]


class AttemptRead(ORM):
    id: int
    test_id: int
    test_title: str
    started_at: datetime
    finished_at: datetime | None
    correct_count: int | None
    total: int | None
    percent: float | None
    grade: int | None
    passed: bool | None

class QuestionStat(BaseModel):
    question_id: int
    text: str
    correct_rate: float


class TestStats(BaseModel):
    attempts: int
    avg_percent: float
    pass_rate: float
    questions: list[QuestionStat]