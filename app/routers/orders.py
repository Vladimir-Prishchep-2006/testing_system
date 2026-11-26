from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AttemptBalance, CartItem, Order, OrderItem, User
from ..schemas import OrderRead
from ..security import get_current_user, require_admin
from ..utils import get_or_404

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=201)
def checkout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Оформляет заказ из корзины: создаёт заказ, начисляет попытки, очищает корзину."""
    items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not items:
        raise HTTPException(400, "Корзина пуста")

    order = Order(user_id=user.id, total=sum(i.test.price * i.quantity for i in items))
    for item in items:
        order.items.append(OrderItem(test_id=item.test_id, title=item.test.title,
                                     price=item.test.price, quantity=item.quantity))
        balance = (db.query(AttemptBalance)
                   .filter(AttemptBalance.user_id == user.id, AttemptBalance.test_id == item.test_id)
                   .first())
        if balance:
            balance.attempts_left += item.quantity
        else:
            db.add(AttemptBalance(user_id=user.id, test_id=item.test_id, attempts_left=item.quantity))
        db.delete(item)

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/me", response_model=list[OrderRead])
def my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc()).all()


@router.get("", response_model=list[OrderRead], dependencies=[Depends(require_admin)])
def all_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.id.desc()).all()


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = get_or_404(db, Order, order_id)
    if order.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "Это не ваш заказ")
    return order