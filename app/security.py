from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET_KEY = "change-me-in-production"  # в реальном проекте берётся из переменной окружения
ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = 60

password_hasher = PasswordHash.recommended()  # Argon2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")  # даёт кнопку Authorize в Swagger


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hasher.verify(password, hashed)


def create_token(username: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)
    return jwt.encode({"sub": username, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Достаёт пользователя из JWT. Любая проблема с токеном даёт 401."""
    error = HTTPException(401, "Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    try:
        username = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
    except (jwt.PyJWTError, KeyError):
        raise error
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise error
    return user