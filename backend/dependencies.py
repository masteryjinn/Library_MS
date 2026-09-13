from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from utils.auth_utils import SECRET_KEY, ALGORITHM

security = HTTPBearer()

def get_current_user_payload(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Декодує JWT-токен із заголовоку Authorization: Bearer <token>"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Термін дії токена закінчився"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний токен авторизації"
        )

def require_role(required_role: str):
    """Декоратор/залежність для розмежування прав (наприклад, тільки librarian)"""
    def role_checker(payload: dict = Depends(get_current_user_payload)):
        user_role = payload.get("role")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас недостатньо прав для виконання цієї операції"
            )
        return payload
    return role_checker