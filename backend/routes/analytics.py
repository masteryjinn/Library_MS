from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func, cast, Date, and_
from sqlalchemy.orm import Session
import logging
from utils.db import get_db
from models.models import Borrowing, Book
from dependencies import require_role

logger = logging.getLogger("analytics")

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

# --- Pydantic Схеми ---

class DailyBorrowingCount(BaseModel):
    date: date
    count: int

    model_config = ConfigDict(from_attributes=True)

class GeneralStats(BaseModel):
    active_readers: int
    overdue_books: int
    top_book: str

class AnalyticsResponse(BaseModel):
    borrowings_by_day: List[DailyBorrowingCount]
    general_stats: GeneralStats


# --- Роути ---

@analytics_router.get("/stats", response_model=AnalyticsResponse)
def get_stats(
    start_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Отримання аналітичних даних та статистики (Тільки для бібліотекаря)."""
    today = date.today()
    if not start_date:
        start_date = today - timedelta(days=365)

    # 1. Видачі по днях
    borrow_date_col = cast(Borrowing.borrow_date, Date)
    daily_stmt = (
        select(
            borrow_date_col.label("date"),
            func.count(Borrowing.id).label("count")
        )
        .where(Borrowing.borrow_date >= start_date)
        .group_by(borrow_date_col)
        .order_by(borrow_date_col)
    )
    daily_results = db.execute(daily_stmt).all()
    borrowings_by_day = [
        DailyBorrowingCount(date=row.date, count=row.count)
        for row in daily_results
    ]

    # 2. Активні читачі (унікальні reader_id за період)
    active_readers_stmt = (
        select(func.count(func.distinct(Borrowing.reader_id)))
        .where(Borrowing.borrow_date >= start_date)
    )
    active_readers = db.scalar(active_readers_stmt) or 0

    # 3. Прострочені книги (return_date IS NULL та видані понад 14 днів тому)
    overdue_cutoff = today - timedelta(days=14)
    overdue_stmt = (
        select(func.count(Borrowing.id))
        .where(
            and_(
                Borrowing.return_date.is_(None),
                cast(Borrowing.borrow_date, Date) < overdue_cutoff
            )
        )
    )
    overdue_books = db.scalar(overdue_stmt) or 0

    # 4. Найпопулярніша книга
    top_book_stmt = (
        select(Book.title, func.count(Borrowing.id).label("borrow_count"))
        .join(Borrowing, Borrowing.book_id == Book.id)
        .where(Borrowing.borrow_date >= start_date)
        .group_by(Book.id, Book.title)
        .order_by(func.count(Borrowing.id).desc())
        .limit(1)
    )
    top_book_result = db.execute(top_book_stmt).first()
    top_book = top_book_result.title if top_book_result else "Немає даних"

    logger.info(f"Librarian {_user.get('sub')} requested analytics stats from date: {start_date}")

    return AnalyticsResponse(
        borrowings_by_day=borrowings_by_day,
        general_stats=GeneralStats(
            active_readers=active_readers,
            overdue_books=overdue_books,
            top_book=top_book
        )
    )