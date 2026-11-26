from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..grading import grade_from_percent, is_question_correct
from ..models import Attempt, AttemptAnswer, AttemptBalance, Test, User, utcnow
from ..schemas import AttemptRead, AttemptStart, BalanceRead, SubmitIn, TestStats
from ..security import get_current_user, require_admin
from ..utils import get_or_404

router = APIRouter(prefix="/api", tags=["attempts"])
GRACE_SECONDS = 15  # запас на задержку сети при отправке в последнюю секунду


@router.post("/tests/{test_id}/start", response_model=AttemptStart, status_code=201)
def start_attempt(test_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    test = get_or_404(db, Test, test_id)
    if not test.questions:
        raise HTTPException(400, "В тесте пока нет вопросов")
    balance = (db.query(AttemptBalance)
               .filter(AttemptBalance.user_id == user.id, AttemptBalance.test_id == test_id)
               .first())
    if balance is None or balance.attempts_left < 1:
        raise HTTPException(402, "Нет доступных попыток: добавьте тест в корзину и оформите заказ")
    balance.attempts_left -= 1  # попытка списывается в момент старта

    attempt = Attempt(user_id=user.id, test_id=test_id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {
        "attempt_id": attempt.id,
        "deadline": attempt.started_at + timedelta(minutes=test.duration_minutes),
        "questions": test.questions,  # схема QuestionPublic не отдаёт is_correct
    }


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptRead)
def submit_attempt(attempt_id: int, data: SubmitIn, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    attempt = get_or_404(db, Attempt, attempt_id)
    if attempt.user_id != user.id:
        raise HTTPException(403, "Это не ваша попытка")
    if attempt.finished_at:
        raise HTTPException(409, "Попытка уже завершена")

    test = attempt.test
    total = len(test.questions)
    attempt.finished_at = utcnow()

    # Время вышло: попытка закрывается с нулевым результатом
    limit = attempt.started_at + timedelta(minutes=test.duration_minutes, seconds=GRACE_SECONDS)
    if attempt.finished_at > limit:
        attempt.correct_count, attempt.total, attempt.percent = 0, total, 0.0
        attempt.grade, attempt.passed = grade_from_percent(0), False
        db.commit()
        raise HTTPException(400, "Время вышло, попытка засчитана с нулевым результатом")

    chosen = {a.question_id: set(a.option_ids) for a in data.answers}
    correct_count = 0
    for question in test.questions:
        selected = chosen.get(question.id, set())
        right = {o.id for o in question.options if o.is_correct}
        ok = is_question_correct(selected, right)
        correct_count += ok
        attempt.answers.append(AttemptAnswer(question_id=question.id, selected=sorted(selected), is_correct=ok))

    percent = round(correct_count / total * 100, 1)
    attempt.correct_count, attempt.total, attempt.percent = correct_count, total, percent
    attempt.grade = grade_from_percent(percent)
    attempt.passed = percent >= test.pass_score
    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/my-tests", response_model=list[BalanceRead])
def my_tests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Купленные тесты и остаток попыток по каждому."""
    return db.query(AttemptBalance).filter(AttemptBalance.user_id == user.id).order_by(AttemptBalance.id).all()


@router.get("/attempts/me", response_model=list[AttemptRead])
def my_attempts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Attempt).filter(Attempt.user_id == user.id).order_by(Attempt.id.desc()).all()


@router.get("/tests/{test_id}/stats", response_model=TestStats, dependencies=[Depends(require_admin)])
def test_stats(test_id: int, db: Session = Depends(get_db)):
    test = get_or_404(db, Test, test_id)
    done = [a for a in test.attempts if a.percent is not None]

    questions = []
    for q in test.questions:
        rows = db.query(AttemptAnswer).filter(AttemptAnswer.question_id == q.id).all()
        rate = round(sum(r.is_correct for r in rows) / len(rows) * 100, 1) if rows else 0.0
        questions.append({"question_id": q.id, "text": q.text, "correct_rate": rate})

    return {
        "attempts": len(done),
        "avg_percent": round(sum(a.percent for a in done) / len(done), 1) if done else 0.0,
        "pass_rate": round(sum(a.passed for a in done) / len(done) * 100, 1) if done else 0.0,
        "questions": questions,
    }