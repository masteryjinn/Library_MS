from faker import Faker
import pymysql
import random
from datetime import datetime, timedelta

fake = Faker('uk_UA')

def get_all_ids(conn, table_name):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT id FROM {table_name}")
        results = cursor.fetchall()
        return [row["id"] for row in results]

def insert_borrowings(conn, n=50):
    book_ids = get_all_ids(conn, 'books')
    reader_ids = get_all_ids(conn, 'readers')

    with conn.cursor() as cursor:
        for _ in range(n):
            book_id = random.choice(book_ids)
            reader_id = random.choice(reader_ids)

            # Генерація дати позичання — випадкова від 30 днів тому до сьогодні
            borrow_date = fake.date_time_between(start_date='-30d', end_date='now')

            # Випадково вирішуємо, чи книга повернена (70% імовірності)
            if random.random() < 0.7:
                return_date = borrow_date + timedelta(days=random.randint(1, 20))
                sql = """
                    INSERT INTO borrowings (book_id, reader_id, borrow_date, return_date)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (book_id, reader_id, borrow_date, return_date))
            else:
                sql = """
                    INSERT INTO borrowings (book_id, reader_id, borrow_date)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (book_id, reader_id, borrow_date))
    
    conn.commit()
    print(f"Додано {n} записів позичань.")

# Підключення до БД
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='12345678',
    database='librarydb',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    insert_borrowings(conn, 100)  # Задай іншу кількість, якщо потрібно
finally:
    conn.close()
