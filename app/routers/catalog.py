from math import ceil
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category, Test
from ..schemas import CategoryRead, Difficulty, TestPage, TestRead
from ..utils import get_or_404

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


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