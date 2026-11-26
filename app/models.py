from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

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
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="test", cascade="all, delete-orphan")

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