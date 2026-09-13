import enum
import datetime
from argon2 import PasswordHasher
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Enum as SQLEnum, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ----------------------------------------------------
# 1. Підключення до MySQL (база librarydb)
# ----------------------------------------------------
# Формат: mysql+pymysql://<user>:<password>@localhost:3306/librarydb
DATABASE_URL = "mysql+pymysql://root:12345678@localhost:3306/librarydb"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ----------------------------------------------------
# 2. Модель користувача
# ----------------------------------------------------
class UserRole(str, enum.Enum):
    GUEST = "guest"
    LIBRARIAN = "librarian"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.GUEST, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ----------------------------------------------------
# 3. Наповнення бази даних
# ----------------------------------------------------
def seed_database():
    ph = PasswordHasher()

    # Створюємо таблицю у MySQL, якщо її ще немає
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    users_to_create = [
        {
            "username": "librarian",
            "raw_password": "lib12345",
            "full_name": "Головний Бібліотекар",
            "role": UserRole.LIBRARIAN
        },
        {
            "username": "guest",
            "raw_password": "guest12345",
            "full_name": "Гість Читач",
            "role": UserRole.GUEST
        }
    ]

    try:
        for u in users_to_create:
            existing_user = session.query(User).filter(User.username == u["username"]).first()
            if existing_user:
                print(f"[-] Користувач '{u['username']}' вже існує в БД. Пропускаємо.")
                continue

            # Хешування пароля за допомогою Argon2
            hashed_pw = ph.hash(u["raw_password"])

            new_user = User(
                username=u["username"],
                password_hash=hashed_pw,
                full_name=u["full_name"],
                role=u["role"],
                is_active=True
            )
            session.add(new_user)
            print(f"[+] Користувача '{u['username']}' успішно додано!")

        session.commit()
        print("\nУспішно оновлено базу даних librarydb у MySQL!")

    except Exception as e:
        session.rollback()
        print(f"[!] Помилка під час виконання скрипта: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()