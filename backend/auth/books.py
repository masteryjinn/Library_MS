from utils.db import get_connection
from fastapi import HTTPException
import pymysql.err

def get_books(search: str, available_only: bool, page: int, page_size: int):
    offset = (page - 1) * page_size
    search_query = f"%{search}%"

    where_clause = "WHERE (b.title LIKE %s OR b.author LIKE %s)"
    if available_only:
        where_clause += " AND br.id IS NOT NULL AND br.return_date IS NOT NULL"

    query = f"""
        SELECT SQL_CALC_FOUND_ROWS
            b.id, b.title, b.author, b.publisher, b.year, b.location,
            CASE
                WHEN br.id IS NOT NULL AND br.return_date IS NULL THEN FALSE
                ELSE TRUE
            END AS available
        FROM books b
        LEFT JOIN borrowings br ON b.id = br.book_id
        AND br.id = (
            SELECT br2.id
            FROM borrowings br2
            WHERE br2.book_id = b.id
            ORDER BY br2.borrow_date DESC, br2.id DESC
            LIMIT 1
        )
        {where_clause}
        LIMIT %s OFFSET %s
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (search_query, search_query, page_size, offset))
            books = cursor.fetchall()

            cursor.execute("SELECT FOUND_ROWS()")
            total = cursor.fetchone()['FOUND_ROWS()']
            total_pages = (total + page_size - 1) // page_size

    return {
        "books": books,
        "total": total,
        "total_pages": total_pages
    }

def get_all_books():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM books")
            return cursor.fetchall()

def get_book_by_id(book_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
            return cursor.fetchone()

def add_book(book):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO books (title, author, year, publisher, location)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                book.title, book.author, book.year,
                book.publisher, book.location
            ))
            conn.commit()
            return cursor.lastrowid

def update_book(book_id: int, book):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            sql = """
                UPDATE books
                SET title = %s, author = %s, year = %s, publisher = %s,
                    location = %s
                WHERE id = %s
            """
            cursor.execute(sql, (
                book.title, book.author, book.year,
                book.publisher, book.location,
                book_id
            ))
            conn.commit()

def delete_book(book_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS count FROM borrowings WHERE book_id = %s AND return_date IS NULL",
                (book_id,)
            )
            result = cursor.fetchone()
            active_loans_count = result["count"] if result is not None else 0

            if active_loans_count > 0:
                raise HTTPException(status_code=409, detail=f"Книга з id={book_id} має активні позичання і не може бути видалена.")

            try:
                cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
            except pymysql.err.IntegrityError:
                raise HTTPException(
                    status_code=409,
                    detail="Книгу не можна видалити, бо вона має історію позичань у базі."
                )
        conn.commit()

# --- Функція, яка тільки виконує SQL-запит і повертає дані ---
def fetch_available_books(conn):
    sql = """
        SELECT b.id, b.title, b.author, b.publisher, b.year
        FROM books b
        WHERE NOT EXISTS (
            SELECT 1 FROM borrowings br
            WHERE br.book_id = b.id AND br.return_date IS NULL
        )
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()

# --- Функція, яка отримує з'єднання, викликає запит і закриває підключення ---
def get_available_books():
    conn = get_connection()
    try:
        books = fetch_available_books(conn)
        return books
    finally:
        conn.close()