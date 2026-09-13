from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Імпорти ваших моделей та сесії БД (змініть шляхи відповідно до структури вашого проєкту)
from utils.db import get_db
from models.models import User
from schema.login import LoginRequest, LoginResponse
from utils.auth_utils import verify_password, create_access_token
import logging

logger = logging.getLogger("auth")

router = APIRouter(tags=["Auth"])

@router.post("/login/", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # 1. Пошук користувача за username
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірне ім'я користувача або пароль"
        )

    # 2. Перевірка статусу акаунта
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Обліковий запис деактивовано"
        )

    # 3. Перевірка пароля через Argon2
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірне ім'я користувача або пароль"
        )

    # 4. Генерація JWT-токена з роллю та user_id
    token_payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role)
    }
    access_token = create_access_token(data=token_payload)

    # 5. Формування відповіді для PyQt6 клієнта
    user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    user_display_name = user.full_name if user.full_name else user.username
    logger.info(f"User {user.username} (ID: {user.id}) logged in successfully with role: {user_role}")
    return LoginResponse(
        user_id=user.id,
        name=user_display_name,
        token=access_token,
        role=user_role
    )