from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AttemptBalance, User
from ..schemas import BalanceRead
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["attempts"])


@router.get("/my-tests", response_model=list[BalanceRead])
def my_tests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Купленные тесты и остаток попыток по каждому."""
    return db.query(AttemptBalance).filter(AttemptBalance.user_id == user.id).order_by(AttemptBalance.id).all()