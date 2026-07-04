#!/usr/bin/env python
"""
Скрипт для автоматической генерации API-токена для суперпользователя.
Запускается при старте проекта из run.bat.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rd_engine.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

def main():
    User = get_user_model()
    
    # Создаём суперпользователя, если его нет
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'is_superuser': True, 'is_staff': True}
    )
    if created:
        user.set_password('Turedy123')
        user.save()
        print("👤 Суперпользователь admin создан (пароль: Turedy123)")
    else:
        print("👤 Суперпользователь admin уже существует")

    # Генерируем или получаем токен
    token, created = Token.objects.get_or_create(user=user)
    if created:
        print(f"🔑 Новый токен сгенерирован: {token.key}")
    else:
        print(f"🔑 Используется существующий токен: {token.key}")

    # Записываем токен в файл static/js/token.js
    token_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'static', 'js', 'token.js'
    )
    
    # Создаём папку, если её нет
    os.makedirs(os.path.dirname(token_file), exist_ok=True)
    
    with open(token_file, 'w', encoding='utf-8') as f:
        f.write(f"// Автоматически сгенерированный токен для API\n")
        f.write(f"window.API_TOKEN = '{token.key}';\n")
    
    print(f"✅ Токен сохранён в {token_file}")

if __name__ == "__main__":
    main()