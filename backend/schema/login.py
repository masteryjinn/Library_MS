from pydantic import BaseModel, ConfigDict

# Вхідний запит від клієнта
class LoginRequest(BaseModel):
    username: str
    password: str

# Відповідь, яку очікує PyQt6 клієнт
class LoginResponse(BaseModel):
    user_id: int
    name: str
    token: str
    role: str

    model_config = ConfigDict(from_attributes=True)