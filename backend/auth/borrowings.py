from typing import List
from utils.db import get_connection
from pymysql.cursors import DictCursor
from datetime import date

def fetch_borrowings(search: str, active_only: bool, offset: int, limit: int) -> List[dict]:
    query = """
    SELECT 
        b.id, 
        CONCAT(r.first_name, ' ', r.last_name) AS reader_name,
        bk.title AS book_title, 
        b.borrow_date, 
        b.return_date
    FROM borrowings b
    JOIN readers r ON b.reader_id = r.id
    JOIN books bk ON b.book_id = bk.id
    WHERE (%s = '' OR CONCAT(r.first_name, ' ', r.last_name) LIKE %s OR bk.title LIKE %s)
    """
    params = [search, f"%{search}%", f"%{search}%"]
    
    if active_only:
        query += " AND b.return_date IS NULL"
    
    query += " ORDER BY b.borrow_date DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    conn = get_connection()
    with conn:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def count_borrowings(search: str, active_only: bool) -> int:
    query = """
    SELECT COUNT(*) AS total
    FROM borrowings b
    JOIN readers r ON b.reader_id = r.id
    JOIN books bk ON b.book_id = bk.id
    WHERE (%s = '' OR CONCAT(r.first_name, ' ', r.last_name) LIKE %s OR bk.title LIKE %s)
    """
    params = [search, f"%{search}%", f"%{search}%"]
    
    if active_only:
        query += " AND b.return_date IS NULL"

    conn = get_connection()
    with conn:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result["total"] if result else 0


def insert_borrowing(data: dict):
    conn = get_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO borrowings (reader_id, book_id, borrow_date)
                VALUES (%s, %s, %s)
            """, (
                data["reader_id"],
                data["book_id"],
                data.get("borrow_date")
            ))
            conn.commit()


def update_borrowing(borrowing_id: int, data: dict):
    conn = get_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE borrowings
                SET reader_id = %s, 
                    book_id = %s, 
                    borrow_date = %s, 
                    return_date = %s
                WHERE id = %s
            """, (
                data["reader_id"],
                data["book_id"],
                data.get("borrow_date"),
                data.get("return_date"),
                borrowing_id
            ))
            conn.commit()


def delete_borrowing(borrowing_id: int):
    conn = get_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM borrowings WHERE id = %s", (borrowing_id,))
            conn.commit()

def set_return_date(borrowing_id: int, return_date: date):
    conn = get_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE borrowings
                SET return_date = %s
                WHERE id = %s
            """, (return_date, borrowing_id))
            conn.commit()
