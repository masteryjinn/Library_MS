from faker import Faker
import pymysql

fake = Faker('uk_UA')  # українська локалізація

# Функція для генерації українського номера телефону формату +380XXXXXXXXX
def generate_uk_phone():
    operator_codes = ['39', '50', '63', '66', '67', '68', '73', '91', '92', '93', '94', '95', '96', '97', '98', '99']
    operator = fake.random_element(operator_codes)
    number = f"+380{operator}{fake.random_number(digits=7, fix_len=True)}"
    return number

# Вставка читачів у таблицю
def insert_readers(conn, n=20):
    with conn.cursor() as cursor:
        for _ in range(n):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.email()
            phone = generate_uk_phone()
            address = fake.address().replace('\n', ', ')
            sql = """
                INSERT INTO readers (first_name, last_name, email, phone, address)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (first_name, last_name, email, phone, address))
    conn.commit()
    print(f"Додано {n} читачів.")

# Вставка книг у таблицю
def insert_books(conn, n=20):
    with conn.cursor() as cursor:
        for _ in range(n):
            title = fake.sentence(nb_words=4).rstrip('.')
            author = fake.name()
            publisher = fake.company()
            year = fake.year()
            location = f"Зал {fake.random_int(1,3)}, Полиця {fake.random_uppercase_letter()}{fake.random_int(1,10)}"
            sql = """
                INSERT INTO books (title, author, publisher, year, location)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (title, author, publisher, year, location))
    conn.commit()
    print(f"Додано {n} книг.")

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
    insert_readers(conn, 20)
    insert_books(conn, 20)
finally:
    conn.close()
