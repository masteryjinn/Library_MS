import math
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
import logging
from utils.db import get_db
from models.models import Borrowing, Reader, Book
from dependencies import require_role

borrowings_router = APIRouter(prefix="/borrowings", tags=["Borrowings"])
logger = logging.getLogger("borrowings")

# --- Pydantic Схеми ---

class BorrowingBase(BaseModel):
    reader_id: int
    book_id: int
    borrow_date: Optional[datetime] = None
    return_date: Optional[datetime] = None

class BorrowingCreate(BorrowingBase):
    pass

class BorrowingUpdate(BorrowingBase):
    pass

class BorrowingOut(BaseModel):
    id: int
    reader_name: str
    book_title: str
    borrow_date: datetime
    return_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class BorrowingsPaginatedResponse(BaseModel):
    borrowings: List[BorrowingOut]
    total_pages: int

class ReturnDatePayload(BaseModel):
    return_date: datetime


# --- Роути ---

@borrowings_router.get("", response_model=BorrowingsPaginatedResponse)
def get_borrowings(
    search: str = "",
    active_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Отримання списку позичань із фільтрацією та пагінацією."""
    # Конкатенація імені та прізвища читача для зручного пошуку
    reader_full_name = func.concat(Reader.first_name, ' ', Reader.last_name)

    # Базовий запит з JOIN
    stmt = (
        select(
            Borrowing.id,
            reader_full_name.label("reader_name"),
            Book.title.label("book_title"),
            Borrowing.borrow_date,
            Borrowing.return_date
        )
        .join(Reader, Borrowing.reader_id == Reader.id)
        .join(Book, Borrowing.book_id == Book.id)
    )

    # Пошук за прізвищем/іменем читача або назвою книги
    if search.strip():
        search_filter = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                reader_full_name.ilike(search_filter),
                Book.title.ilike(search_filter)
            )
        )

    # Фільтрація тільки активних (не повернутих) позичань
    if active_only:
        stmt = stmt.where(Borrowing.return_date.is_(None))

    # Підрахунок загальної кількості записів
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    # Сортування та пагінація
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Borrowing.borrow_date.desc()).offset(offset).limit(page_size)

    results = db.execute(stmt).all()

    borrowings_list = [
        BorrowingOut(
            id=row.id,
            reader_name=row.reader_name,
            book_title=row.book_title,
            borrow_date=row.borrow_date,
            return_date=row.return_date
        )
        for row in results
    ]

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    logger.info(f"Fetched borrowings list: page {page}/{total_pages}, search='{search}', active_only={active_only}, total_borrowings={total}")
    return BorrowingsPaginatedResponse(
        borrowings=borrowings_list,
        total_pages=total_pages
    )


@borrowings_router.post("", status_code=status.HTTP_201_CREATED)
def create_borrowing(
    data: BorrowingCreate,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Створення запису про позичання книги (Тільки для бібліотекаря)."""
    # Перевірка наявності читача та книги в БД
    if not db.get(Reader, data.reader_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Читача не знайдено")
    if not db.get(Book, data.book_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книгу не знайдено")

    new_borrowing = Borrowing(
        reader_id=data.reader_id,
        book_id=data.book_id,
        borrow_date=data.borrow_date or datetime.utcnow()
    )
    db.add(new_borrowing)
    db.commit()
    logger.info(f"Librarian {_user.get('sub')} created a new borrowing: ID {new_borrowing.id}")
    return {"message": "Позичання створено"}


@borrowings_router.put("/{borrowing_id}")
def update_borrowing(
    borrowing_id: int,
    data: BorrowingUpdate,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Редагування позичання (Тільки для бібліотекаря)."""
    borrowing = db.get(Borrowing, borrowing_id)
    if not borrowing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запис про позичання не знайдено")

    borrowing.reader_id = data.reader_id
    borrowing.book_id = data.book_id
    if data.borrow_date:
        borrowing.borrow_date = data.borrow_date
    borrowing.return_date = data.return_date

    db.commit()
    logger.info(f"Librarian {_user.get('sub')} updated borrowing ID {borrowing_id}")
    return {"message": "Позичання оновлено"}


@borrowings_router.delete("/{borrowing_id}")
def delete_borrowing(
    borrowing_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Видалення запису про позичання (Тільки для бібліотекаря)."""
    borrowing = db.get(Borrowing, borrowing_id)
    if not borrowing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запис про позичання не знайдено")

    db.delete(borrowing)
    db.commit()
    logger.info(f"Librarian {_user.get('sub')} deleted borrowing ID {borrowing_id}")
    return {"message": "Позичання видалено"}


@borrowings_router.put("/return/{borrowing_id}")
def set_return_with_date(
    borrowing_id: int,
    payload: ReturnDatePayload,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Фіксація дати повернення книги (Тільки для бібліотекаря)."""
    borrowing = db.get(Borrowing, borrowing_id)
    if not borrowing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запис про позичання не знайдено")

    borrowing.return_date = payload.return_date
    db.commit()
    logger.info(f"Librarian {_user.get('sub')} set return date for borrowing ID {borrowing_id} to {payload.return_date}")
    return {"message": "Дату повернення зафіксовано", "return_date": payload.return_date}

import hashlib
ADMIN_PASSWORD_HASH = "ff66e5d5b915f971df138ef6d25fde96758151642d5ad1fc8054fd19e06996a8"  # Хеш для пароля "admin123"
pepper = "someSecretPepperValue123!"

class PasswordCheckPayload(BaseModel):
    password: str

@borrowings_router.post("/check-password")
async def check_password(payload: PasswordCheckPayload, 
                         _user: dict = Depends(require_role("librarian"))):
    """
    Проста перевірка пароля через SHA-256
    """
    password_with_pepper = payload.password + pepper
    input_hash = hashlib.sha256(password_with_pepper.encode()).hexdigest()
    
    if input_hash != ADMIN_PASSWORD_HASH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний пароль адміністратора"
        )
    logger.info(f"Librarian {_user.get('sub')} successfully verified admin password")
    return {"detail": "Пароль вірний"}