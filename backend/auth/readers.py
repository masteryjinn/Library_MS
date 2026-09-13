from utils.db import get_connection
from fastapi import HTTPException
import pymysql.err

def get_readers(page=1, limit=15, search=""):
    offset = (page - 1) * limit
    search_pattern = f"%{search}%"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            sql_count = """
                SELECT COUNT(*) as total
                FROM readers
                WHERE first_name LIKE %s OR last_name LIKE %s
            """
            cursor.execute(sql_count, (search_pattern, search_pattern))
            total = cursor.fetchone()["total"]

            sql = """
                SELECT r.id, r.first_name, r.last_name, r.email, r.phone, r.address,
                       COUNT(b.id) AS book_count
                FROM readers r
                LEFT JOIN borrowings b ON r.id = b.reader_id AND b.return_date IS NULL
                WHERE r.first_name LIKE %s OR r.last_name LIKE %s
                GROUP BY r.id, r.first_name, r.last_name, r.email, r.phone, r.address
                ORDER BY r.id
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (search_pattern, search_pattern, limit, offset))
            readers = cursor.fetchall()

    total_pages = max(1, (total + limit - 1) // limit)
    return {
        "data": readers,
        "total": total,
        "total_pages": total_pages,
        "current_page": page,
    }

def get_reader_by_id(reader_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, first_name, last_name, email, phone, address FROM readers WHERE id = %s"
            cursor.execute(sql, (reader_id,))
            return cursor.fetchone()

def add_reader(first_name, last_name, email, phone=None, address=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO readers (first_name, last_name, email, phone, address)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (first_name, last_name, email, phone, address))
        conn.commit()
        return cursor.lastrowid

def update_reader(reader_id, first_name, last_name, email, phone=None, address=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            sql = """
                UPDATE readers
                SET first_name=%s, last_name=%s, email=%s, phone=%s, address=%s
                WHERE id=%s
            """
            cursor.execute(sql, (first_name, last_name, email, phone, address, reader_id))
        conn.commit()


def delete_reader(reader_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Перевірка наявності будь-яких позичань
            cursor.execute(
                "SELECT COUNT(*) AS count FROM borrowings WHERE reader_id = %s",
                (reader_id,)
            )
            result = cursor.fetchone()
            #print(result)
            #print(type(result))
            active_loans_count = result["count"] if result is not None else 0

            if active_loans_count > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Читач з id={reader_id} має позичання в базі й не може бути видалений."
                )

            try:
                cursor.execute("DELETE FROM readers WHERE id = %s", (reader_id,))
                conn.commit()
            except pymysql.err.IntegrityError:
                raise HTTPException(
                    status_code=409,
                    detail=f"Читача з id={reader_id} не вдалося видалити через обмеження цілісності даних."
                )
            
def get_eligible_readers():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Повертаємо читачів, у яких менше 5 позичань без дати повернення
            query = """
            SELECT r.id, r.first_name, r.last_name, r.phone
            FROM readers r
            LEFT JOIN borrowings b ON r.id = b.reader_id AND b.return_date IS NULL
            GROUP BY r.id
            HAVING COUNT(b.id) < 5
            """
            cursor.execute(query)
            readers = cursor.fetchall()
        return readers
    finally:
        conn.close()