from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CartItem, Test, User
from ..schemas import CartAdd, CartRead, CartUpdate
from ..security import get_current_user
from ..utils import get_or_404

router = APIRouter(prefix="/api/cart", tags=["cart"])
MAX_QUANTITY = 20


def _find(db: Session, user: User, test_id: int):
    return db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.test_id == test_id).first()


def _cart(db: Session, user: User) -> dict:
    """Собирает корзину пользователя с суммами по позициям и итогом."""
    items = db.query(CartItem).filter(CartItem.user_id == user.id).order_by(CartItem.id).all()
    rows = [{"test": i.test, "quantity": i.quantity, "subtotal": i.test.price * i.quantity} for i in items]
    return {"items": rows, "total": sum(r["subtotal"] for r in rows), "count": len(rows)}


@router.get("", response_model=CartRead)
def get_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _cart(db, user)


@router.post("/items", response_model=CartRead, status_code=201)
def add_item(data: CartAdd, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_or_404(db, Test, data.test_id)
    item = _find(db, user, data.test_id)
    if item:  # такой тест уже в корзине: увеличиваем количество
        item.quantity = min(item.quantity + data.quantity, MAX_QUANTITY)
    else:
        db.add(CartItem(user_id=user.id, test_id=data.test_id, quantity=data.quantity))
    db.commit()
    return _cart(db, user)


@router.put("/items/{test_id}", response_model=CartRead)
def set_quantity(test_id: int, data: CartUpdate, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    item = _find(db, user, test_id)
    if item is None:
        raise HTTPException(404, "Этого теста нет в корзине")
    item.quantity = data.quantity
    db.commit()
    return _cart(db, user)


@router.delete("/items/{test_id}", response_model=CartRead)
def remove_item(test_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = _find(db, user, test_id)
    if item is None:
        raise HTTPException(404, "Этого теста нет в корзине")
    db.delete(item)
    db.commit()
    return _cart(db, user)