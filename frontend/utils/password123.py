import hashlib

# 1. Вкажіть новий бажаний пароль тут:
new_password = "admin12345"

# 2. Значення перцю (значення pepper має бути точно таким же, як у вашому роуті):
pepper = "someSecretPepperValue123!"

# 3. Генерація хешу:
new_hash = hashlib.sha256((new_password + pepper).encode()).hexdigest()

print(f"Новий пароль: {new_password}")
print(f"Новий ADMIN_PASSWORD_HASH: {new_hash}")