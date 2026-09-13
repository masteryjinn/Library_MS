import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    guest = "guest"
    librarian = "librarian"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False), 
        default=UserRole.guest
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[str] = mapped_column(String(255), index=True)
    year: Mapped[int]
    publisher: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(100))

    borrowings: Mapped[List["Borrowing"]] = relationship(back_populates="book")

class Reader(Base):
    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(String(255))

    borrowings: Mapped[List["Borrowing"]] = relationship(back_populates="reader")

class Borrowing(Base):
    __tablename__ = "borrowings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reader_id: Mapped[int] = mapped_column(ForeignKey("readers.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    borrow_date: Mapped[datetime] = mapped_column(server_default=func.now())
    return_date: Mapped[Optional[datetime]]

    book: Mapped["Book"] = relationship(back_populates="borrowings")
    reader: Mapped["Reader"] = relationship(back_populates="borrowings")