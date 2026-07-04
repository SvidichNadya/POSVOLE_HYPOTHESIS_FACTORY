@echo off
setlocal enabledelayedexpansion

echo 🚀 Auto start settings of project POSVOL ITe...

REM Проверка наличия Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found. Install Python 3.10+ and add in PATH.
    pause
    exit /b 1
)

REM Создание виртуального окружения
if not exist "venv" (
    echo 📦 Create venv...
    python -m venv venv
)

REM Активация
call venv\Scripts\activate.bat

REM Установка зависимостей
echo 📥 Install requirements...
pip install --upgrade pip
pip install django pillow python-dotenv

if exist requirements.txt (
    pip install -r requirements.txt
)

REM Генерация .env если отсутствует
if not exist ".env" (
    echo 🔐 Generate secret key...
    python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))" > .env
    echo DEBUG=True >> .env
    echo ALLOWED_HOSTS=localhost,127.0.0.1 >> .env
)

REM Проверка manage.py
if not exist "manage.py" (
    echo ❌ File manage.py not found. Убедитесь, что вы в корневой папке.
    pause
    exit /b 1
)

REM Миграции
echo 🔄 Use migration...
python manage.py makemigrations
python manage.py migrate

REM Загрузка фикстур (если есть)
if exist "fixtures" (
    echo 📂 Download fixtures...
    for %%f in (fixtures\*.json) do (
        echo Download %%f...
        python manage.py loaddata %%f
    )
)

REM Создание суперпользователя через отдельный скрипт
echo 👤 Create superuser...
(
echo from django.contrib.auth import get_user_model
echo User = get_user_model()
echo if not User.objects.filter(username='admin').exists():
echo     User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
echo     print('Superuser admin created (password: adminpass)')
echo else:
echo     print('Superuser admin already exist')
) > create_superuser.py
python manage.py shell < create_superuser.py
del create_superuser.py

REM Сбор статики
echo 📦 Cache statistic...
python manage.py collectstatic --noinput

echo ✅ Done! Start server...
echo 🌐 Open http://127.0.0.1:8000
echo 🔑 Admin page: http://127.0.0.1:8000/admin (login: admin, password: adminpass)
echo 🔄 Server working. For stop use Ctrl+C.
python manage.py runserver

REM Если сервер завершится (по Ctrl+C), покажем сообщение
echo Server stoped.
pause