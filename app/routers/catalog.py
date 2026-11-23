from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category, Test
from ..schemas import CategoryRead, TestPage, TestRead
from ..utils import get_or_404

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.get("/tests", response_model=TestPage)
def list_tests(
    page: int = Query(1, ge=1),
    size: int = Query(6, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(Test)
    total = query.count()
    items = query.order_by(Test.id).offset((page - 1) * size).limit(size).all()
    return {"items": items, "total": total, "page": page, "pages": max(1, ceil(total / size))}


@router.get("/tests/{test_id}", response_model=TestRead)
def get_test(test_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Test, test_id)