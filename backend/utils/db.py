import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 1. Параметри підключення (бажано через змінні оточення з дефолтними значеннями)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345678")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "librarydb")

# 2. URL підключення SQLAlchemy за допомогою pymysql
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 3. Створення Engine з пулом з'єднань
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Автоматична перевірка живості з'єднання перед запитом
    pool_recycle=3600    # Оновлення з'єднань щогодини (корисно для MySQL)
)

# 4. Фабрика сесій для обробки запитів
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Базовий клас для моделей
class Base(DeclarativeBase):
    pass

# 6. Dependency для FastAPI роутів (створює та закриває сесію для кожного HTTP-запиту)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()