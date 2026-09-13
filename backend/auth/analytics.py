from datetime import date, timedelta

def get_analytics_data_raw(conn, start_date: date = None):
    today = date.today()
    if not start_date:
        start_date = today - timedelta(days=365)

    with conn.cursor() as cursor:

        # 1. Видачі по днях
        cursor.execute("""
            SELECT DATE(borrow_date) AS date, COUNT(*) AS count
            FROM borrowings
            WHERE borrow_date >= %s
            GROUP BY DATE(borrow_date)
            ORDER BY DATE(borrow_date)
        """, (start_date,))
        borrowings_by_day = cursor.fetchall()

        # 2. Активні читачі
        cursor.execute("""
            SELECT COUNT(DISTINCT reader_id) AS active_readers
            FROM borrowings
            WHERE borrow_date >= %s
        """, (start_date,))
        active_readers = cursor.fetchone()["active_readers"]

        # 3. Прострочені книги
        cursor.execute("""
            SELECT COUNT(*) AS overdue_books
            FROM borrowings
            WHERE return_date IS NULL AND DATE_ADD(borrow_date, INTERVAL 14 DAY) < %s
        """, (today,))
        overdue_books = cursor.fetchone()["overdue_books"]

        # 4. Найпопулярніша книга
        cursor.execute("""
            SELECT books.title, COUNT(*) AS borrow_count
            FROM borrowings
            JOIN books ON borrowings.book_id = books.id
            WHERE borrow_date >= %s
            GROUP BY books.id
            ORDER BY borrow_count DESC
            LIMIT 1
        """, (start_date,))
        top_book_row = cursor.fetchone()
        top_book = top_book_row["title"] if top_book_row else "Немає даних"

    return {
        "borrowings_by_day": borrowings_by_day,
        "general_stats": {
            "active_readers": active_readers,
            "overdue_books": overdue_books,
            "top_book": top_book
        }
    }
