import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import select, func, or_, exists, and_, case
from sqlalchemy.orm import Session
import logging
from utils.db import get_db
from models.models import Reader, Borrowing
from dependencies import require_role

readers_router = APIRouter(prefix="/readers", tags=["Readers"])
logger = logging.getLogger("readers")


# --- Pydantic Схеми ---

class ReaderBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class ReaderCreate(ReaderBase):
    pass

class ReaderUpdate(ReaderBase):
    pass

class ReaderOut(ReaderBase):
    id: int
    book_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class EligibleReaderOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EligibleReadersResponse(BaseModel):
    readers: List[EligibleReaderOut]

class ReadersPaginatedResponse(BaseModel):
    data: List[ReaderOut]
    total: int
    total_pages: int
    current_page: int

class ActionSuccessResponse(BaseModel):
    message: str
    id: Optional[int] = None


# --- Роути ---

@readers_router.get("", response_model=ReadersPaginatedResponse)
def read_readers(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    search: str = "",
    db: Session = Depends(get_db)
):
    """Отримання списку читачів із підрахунком активних книжок на руках та пагінацією."""
    search_term = search.strip()
    
    # 1. Формуємо легкий запит для підрахунку загальної кількості (без JOIN)
    count_stmt = select(func.count(Reader.id))
    
    # 2. Основний запит для вибірки даних із підрахунком книг (Сумісно з MySQL)
    active_borrowings_count = func.count(
        case((Borrowing.return_date.is_(None), Borrowing.id))
    ).label("book_count")

    stmt = (
        select(Reader, active_borrowings_count)
        .outerjoin(Borrowing, Reader.id == Borrowing.reader_id)
        .group_by(Reader.id)
    )

    # Застосування фільтра пошуку
    if search_term:
        search_filter = f"%{search_term}%"
        reader_full_name = func.concat(Reader.first_name, " ", Reader.last_name)
        filter_condition = or_(
            Reader.first_name.ilike(search_filter),
            Reader.last_name.ilike(search_filter),
            reader_full_name.ilike(search_filter)
        )
        stmt = stmt.where(filter_condition)
        count_stmt = count_stmt.where(filter_condition)

    # Отримуємо загальну кількість
    total = db.scalar(count_stmt) or 0

    # Сортування та пагінація
    offset = (page - 1) * limit
    stmt = stmt.order_by(Reader.id).offset(offset).limit(limit)

    results = db.execute(stmt).all()

    readers_list = []
    for reader_obj, count in results:
        dto = ReaderOut.model_validate(reader_obj)
        dto.book_count = count
        readers_list.append(dto)

    total_pages = math.ceil(total / limit) if total > 0 else 0
    logger.info(f"Fetched readers list: page {page}/{total_pages}, search='{search}', total_readers={total}")
    return ReadersPaginatedResponse(
        data=readers_list,
        total=total,
        total_pages=total_pages,
        current_page=page
    )


@readers_router.get("/eligible", response_model=EligibleReadersResponse)
def api_get_eligible_readers(db: Session = Depends(get_db)):
    """Отримання читачів, у яких менше 5 неповернутих книг."""
    stmt = (
        select(Reader)
        .outerjoin(Borrowing, and_(Reader.id == Borrowing.reader_id, Borrowing.return_date.is_(None)))
        .group_by(Reader.id)
        .having(func.count(Borrowing.id) < 5)
    )
    readers = db.scalars(stmt).all()
    logger.info(f"Fetched eligible readers: count={len(readers)}")
    return EligibleReadersResponse(
        readers=[EligibleReaderOut.model_validate(r) for r in readers]
    )


@readers_router.get("/{reader_id}", response_model=ReaderOut)
def read_reader(reader_id: int, db: Session = Depends(get_db)):
    """Отримання детальної інформації про одного читача."""
    reader = db.get(Reader, reader_id)
    if not reader:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Читача не знайдено")

    active_count = db.scalar(
        select(func.count(Borrowing.id)).where(
            and_(Borrowing.reader_id == reader_id, Borrowing.return_date.is_(None))
        )
    ) or 0

    dto = ReaderOut.model_validate(reader)
    dto.book_count = active_count
    logger.info(f"Fetched reader details: ID {reader_id}, name {reader.first_name} {reader.last_name}, active_borrowings {active_count}")
    return dto


# --- Захищені операції (Тільки для бібліотекаря) ---

@readers_router.post("", status_code=status.HTTP_201_CREATED, response_model=ActionSuccessResponse)
def create_reader(
    reader_in: ReaderCreate,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Створення нового читача (Тільки для бібліотекаря)."""
    new_reader = Reader(**reader_in.model_dump())
    db.add(new_reader)
    db.commit()
    db.refresh(new_reader)
    logger.info(f"Librarian {_user.get('sub')} created a new reader: {new_reader.first_name} {new_reader.last_name} (ID: {new_reader.id})")
    return ActionSuccessResponse(id=new_reader.id, message="Читача успішно додано")


@readers_router.put("/{reader_id}", response_model=ActionSuccessResponse)
def update_reader(
    reader_id: int,
    reader_in: ReaderUpdate,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Оновлення інформації про читача (Тільки для бібліотекаря)."""
    reader = db.get(Reader, reader_id)
    if not reader:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Читача не знайдено")

    for key, value in reader_in.model_dump().items():
        setattr(reader, key, value)

    db.commit()
    logger.info(f"Librarian {_user.get('sub')} updated reader ID {reader_id}: {reader.first_name} {reader.last_name}")
    return ActionSuccessResponse(message="Дані читача оновлено")


@readers_router.delete("/{reader_id}", response_model=ActionSuccessResponse)
def delete_reader(
    reader_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_role("librarian"))
):
    """Видалення читача за відсутності заборгованостей/позичань (Тільки для бібліотекаря)."""
    reader = db.get(Reader, reader_id)
    if not reader:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Читача не знайдено")

    has_borrowings = db.scalar(
        select(exists().where(Borrowing.reader_id == reader_id))
    )
    if has_borrowings:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Читач з id={reader_id} має позичання в базі й не може бути видалений."
        )

    db.delete(reader)
    db.commit()
    logger.info(f"Librarian {_user.get('sub')} deleted reader ID {reader_id}: {reader.first_name} {reader.last_name}")
    return ActionSuccessResponse(message="Читача видалено")
