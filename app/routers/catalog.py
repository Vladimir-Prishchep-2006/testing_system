from math import ceil
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category, Option, Question, Test
from ..schemas import (CategoryCreate, CategoryRead, Difficulty, QuestionAdmin,
                       QuestionCreate, TestCreate, TestPage, TestRead)
from ..security import require_admin
from ..utils import get_or_404

router = APIRouter(prefix="/api", tags=["catalog"])
admin_only = [Depends(require_admin)]


# ---------- категории ----------
@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.post("/categories", response_model=CategoryRead, status_code=201, dependencies=admin_only)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    if db.query(Category).filter(Category.name == data.name).first():
        raise HTTPException(409, "Такая категория уже существует")
    category = Category(name=data.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryRead, dependencies=admin_only)
def update_category(category_id: int, data: CategoryCreate, db: Session = Depends(get_db)):
    category = get_or_404(db, Category, category_id)
    duplicate = db.query(Category).filter(Category.name == data.name, Category.id != category_id).first()
    if duplicate:
        raise HTTPException(409, "Такая категория уже существует")
    category.name = data.name
    db.commit()
    return category


@router.delete("/categories/{category_id}", status_code=204, dependencies=admin_only)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = get_or_404(db, Category, category_id)
    if category.tests:
        raise HTTPException(409, "В категории есть тесты, сначала удалите или перенесите их")
    db.delete(category)
    db.commit()


# ---------- каталог тестов ----------
@router.get("/tests", response_model=TestPage)
def list_tests(
    search: str | None = None,
    category_id: int | None = None,
    difficulty: Difficulty | None = None,
    min_price: int | None = Query(None, ge=0),
    max_price: int | None = Query(None, ge=0),
    sort: Literal["id", "price_asc", "price_desc", "title"] = "id",
    page: int = Query(1, ge=1),
    size: int = Query(6, ge=1, le=50),
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(400, "Минимальная цена больше максимальной")

    query = db.query(Test)
    if search:
        query = query.filter(Test.title.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Test.category_id == category_id)
    if difficulty:
        query = query.filter(Test.difficulty == difficulty)
    if min_price is not None:
        query = query.filter(Test.price >= min_price)
    if max_price is not None:
        query = query.filter(Test.price <= max_price)

    order = {"id": Test.id, "price_asc": Test.price, "price_desc": Test.price.desc(), "title": Test.title}[sort]
    total = query.count()
    items = query.order_by(order, Test.id).offset((page - 1) * size).limit(size).all()
    return {"items": items, "total": total, "page": page, "pages": max(1, ceil(total / size))}


@router.get("/tests/{test_id}", response_model=TestRead)
def get_test(test_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Test, test_id)


@router.post("/tests", response_model=TestRead, status_code=201, dependencies=admin_only)
def create_test(data: TestCreate, db: Session = Depends(get_db)):
    get_or_404(db, Category, data.category_id)  # 404, если категории нет
    test = Test(**data.model_dump())
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.put("/tests/{test_id}", response_model=TestRead, dependencies=admin_only)
def update_test(test_id: int, data: TestCreate, db: Session = Depends(get_db)):
    test = get_or_404(db, Test, test_id)
    get_or_404(db, Category, data.category_id)
    for field, value in data.model_dump().items():
        setattr(test, field, value)
    db.commit()
    db.refresh(test)
    return test


@router.delete("/tests/{test_id}", status_code=204, dependencies=admin_only)
def delete_test(test_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Test, test_id))
    db.commit()
# ---------- вопросы (только администратор) ----------
@router.get("/tests/{test_id}/questions", response_model=list[QuestionAdmin], dependencies=admin_only)
def list_questions(test_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Test, test_id).questions


@router.post("/tests/{test_id}/questions", response_model=QuestionAdmin, status_code=201, dependencies=admin_only)
def add_question(test_id: int, data: QuestionCreate, db: Session = Depends(get_db)):
    test = get_or_404(db, Test, test_id)
    question = Question(text=data.text, options=[Option(**o.model_dump()) for o in data.options])
    test.questions.append(question)
    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}", status_code=204, dependencies=admin_only)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Question, question_id))
    db.commit()