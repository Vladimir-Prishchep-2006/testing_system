from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    """Текущее время UTC без tzinfo (SQLite не хранит часовой пояс)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student")  # student (покупатель) | admin

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
    questions: Mapped[list["Question"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    balances: Mapped[list["AttemptBalance"]] = relationship(back_populates="test", cascade="all, delete-orphan")

    @property
    def questions_count(self) -> int:
        return len(self.questions)

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    text: Mapped[str] = mapped_column(String(1000))

    test: Mapped[Test] = relationship(back_populates="questions")
    options: Mapped[list["Option"]] = relationship(back_populates="question", cascade="all, delete-orphan")

    @property
    def multiple(self) -> bool:
        """True, если верных ответов несколько (в интерфейсе тогда чекбоксы, а не радиокнопки)."""
        return sum(o.is_correct for o in self.options) > 1


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    text: Mapped[str] = mapped_column(String(300))
    is_correct: Mapped[bool] = mapped_column(default=False)

    question: Mapped[Question] = relationship(back_populates="options")



class CartItem(Base):
    """Позиция корзины: тест и количество попыток, которое пользователь хочет купить."""
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "test_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    quantity: Mapped[int] = mapped_column(default=1)

    test: Mapped[Test] = relationship(back_populates="cart_items")



class Order(Base):
    """Оформленный заказ. Оплата имитируется: заказ сразу получает статус paid."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    total: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="paid")

    items: Mapped[list["OrderItem"]] = relationship(cascade="all, delete-orphan")


class OrderItem(Base):
    """Строка заказа. Название и цена копируются в момент покупки, поэтому
    история заказов не меняется, если тест потом изменят или удалят."""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    test_id: Mapped[int]  # намеренно без внешнего ключа
    title: Mapped[str] = mapped_column(String(200))
    price: Mapped[int]
    quantity: Mapped[int]


class AttemptBalance(Base):
    """Сколько попыток по тесту осталось у пользователя. Пополняется при оформлении заказа."""
    __tablename__ = "attempt_balances"
    __table_args__ = (UniqueConstraint("user_id", "test_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    attempts_left: Mapped[int] = mapped_column(default=0)

    test: Mapped[Test] = relationship(back_populates="balances")


class Attempt(Base):
    """Одна попытка прохождения теста."""
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    finished_at: Mapped[datetime | None]
    correct_count: Mapped[int | None]
    total: Mapped[int | None]
    percent: Mapped[float | None]
    grade: Mapped[int | None]
    passed: Mapped[bool | None]

    test: Mapped[Test] = relationship(back_populates="attempts")
    answers: Mapped[list["AttemptAnswer"]] = relationship(cascade="all, delete-orphan")

    @property
    def test_title(self) -> str:
        return self.test.title


class AttemptAnswer(Base):
    """Ответ студента на один вопрос в рамках попытки."""
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    selected: Mapped[list[int]] = mapped_column(JSON)  # id выбранных вариантов
    is_correct: Mapped[bool]