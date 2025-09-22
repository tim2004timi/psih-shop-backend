# Генерация случайного ключа
import secrets
secret_key = secrets.token_urlsafe(32)
print(secret_key)  # Скопируйте в .env