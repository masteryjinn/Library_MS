import math
from typing import  List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, exists, and_
from sqlalchemy.orm import Session
from schema.books import BookCreate, BookUpdate, BookOut, BooksPaginatedResponse
import logging
from utils.db import get_db
from models.models import Book, Borrowing
from dependencies import require_role  

logger = logging.getLogger("books")

books_router = APIRouter(prefix="/books", tags=["Books"])
# --- Роути ---

@books_router.get("", response_model=BooksPaginatedResponse)
def get_books(
    search: str = "",
    available_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Отримання списку книг із фільтрацією, пагінацією та статусом доступності."""
    # Підзапит для перевірки, чи книга зараз видана (return_date IS NULL)
    active_borrow_exists = exists().where(
        and_(
            Borrowing.book_id == Book.id,
            Borrowing.return_date.is_(None)
        )
    )

    # Базовий запит
    stmt = select(Book, (~active_borrow_exists).label("available"))

    # Фільтр по пошуковому слову
    if search.strip():
        search_filter = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Book.title.ilike(search_filter),
                Book.author.ilike(search_filter)
            )
        )

    # Фільтр тільки доступних книг
    if available_only:
        stmt = stmt.where(~active_borrow_exists)

    # Підрахунок загальної кількості записів
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    # Пагінація
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    results = db.execute(stmt).all()

    # Формування результату
    books_list = []
    for book, is_available in results:
        book_data = BookOut.model_validate(book)
        book_data.available = is_available
        books_list.append(book_data)

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    logger.info(f"Fetched books list: page {page}/{total_pages}, search='{search}', available_only={available_only}, total_books={total}")
    return BooksPaginatedResponse(
        books=books_list,
        total=total,
        total_pages=total_pages
    )

@books_router.get("/available", response_model=List[BookOut])
def get_available_books(db: Session = Depends(get_db)):
    """Оримання списку книг, які фізично в наявності."""
    active_borrow_exists = exists().where(
        and_(
            Borrowing.book_id == Book.id,
            Borrowing.return_date.is_(None)
        )
    )
    stmt = select(Book).where(~active_borrow_exists)
    books = db.scalars(stmt).all()
    
    res = []
    for b in books:
        dto = BookOut.model_validate(b)
        dto.available = True
        res.append(dto)
    logger.info(f"Fetched available books list: total_available_books={len(res)}")
    return res

@books_router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Отримання однієї книги за її ID."""
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книгу не знайдено")

    # Перевіряємо доступність
    is_borrowed = db.scalar(
        select(exists().where(and_(Borrowing.book_id == book_id, Borrowing.return_date.is_(None))))
    )
    
    dto = BookOut.model_validate(book)
    dto.available = not is_borrowed
    logger.info(f"Fetched book details: {dto.title}, available: {dto.available}")
    return dto

# --- Операції, доступні ТІЛЬКИ БІБЛІОТЕКАРЮ ---

@books_router.post("", status_code=status.HTTP_201_CREATED)
def create_book(
    book_in: BookCreate, 
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Створення книги (Тільки для бібліотекаря)."""
    new_book = Book(**book_in.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    logger.info(f"Librarian {_user.get('sub')} created a new book: {new_book.title} (ID: {new_book.id})")
    return {"id": new_book.id, "message": "Книгу успішно додано"}

@books_router.put("/{book_id}")
def update_book(
    book_id: int, 
    book_in: BookUpdate, 
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Оновлення даних книги (Тільки для бібліотекаря)."""
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книгу не знайдено")

    for key, value in book_in.model_dump().items():
        setattr(book, key, value)

    db.commit()
    logger.info(f"Librarian {_user.get('sub')} updated book ID {book_id}: {book.title}")
    return {"message": "Дані книги оновлено"}

@books_router.delete("/{book_id}")
def delete_book(
    book_id: int, 
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Видалення книги (Тільки для бібліотекаря)."""
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книгу не знайдено")

    # Перевірка на активні позичання
    active_loan = db.scalar(
        select(exists().where(and_(Borrowing.book_id == book_id, Borrowing.return_date.is_(None))))
    )
    if active_loan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Книга з id={book_id} має активні позичання і не може бути видалена."
        )

    # Перевірка на наявність будь-якої історії в borrowings
    has_history = db.scalar(
        select(exists().where(Borrowing.book_id == book_id))
    )
    if has_history:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Книгу не можна видалити, бо вона має історію позичань у базі."
        )

    db.delete(book)
    logger.info(f"Librarian {_user.get('sub')} deleted book ID {book_id}: {book.title}")
    db.commit()
    return {"message": "Книгу видалено"}