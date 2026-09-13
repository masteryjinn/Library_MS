import os
from datetime import datetime, timedelta
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt

# Налаштування JWT (у реальному проєкті SECRET_KEY виноситься в .env)
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-lab-3-jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 годин

ph = PasswordHasher()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє відповідність введеного пароля Argon2-хешу"""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Генерує JWT-токен із корисним навантаженням (payload)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt