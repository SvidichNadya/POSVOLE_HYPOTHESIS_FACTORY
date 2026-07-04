@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

set RESET=0
if "%1"=="reset" set RESET=1
if "%1"=="--reset" set RESET=1

echo 🚀 Auto start settings of project...

:: Активация виртуального окружения
if exist venv\Scripts\activate (
    call venv\Scripts\activate
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
)

:: Установка зависимостей
echo 📥 Install requirements...
pip install -r requirements.txt

:: Полный сброс (если указан параметр reset)
if %RESET%==1 (
    echo 🔄 Performing full reset...

    if exist db.sqlite3 (
        del db.sqlite3
        echo   - Deleted db.sqlite3
    )

    REM Очистка папок migrations (упрощённо, без вложенных for /f)
    if exist apps\core\migrations (
        echo   - Cleaning apps\core\migrations...
        del /q apps\core\migrations\*.py 2>nul
        del /q apps\core\migrations\*.pyc 2>nul
        rmdir /s /q apps\core\migrations\__pycache__ 2>nul
    )
    if exist apps\objects\migrations (
        echo   - Cleaning apps\objects\migrations...
        del /q apps\objects\migrations\*.py 2>nul
        del /q apps\objects\migrations\*.pyc 2>nul
        rmdir /s /q apps\objects\migrations\__pycache__ 2>nul
    )
    if exist apps\hypotheses\migrations (
        echo   - Cleaning apps\hypotheses\migrations...
        del /q apps\hypotheses\migrations\*.py 2>nul
        del /q apps\hypotheses\migrations\*.pyc 2>nul
        rmdir /s /q apps\hypotheses\migrations\__pycache__ 2>nul
    )
    if exist apps\knowledge\migrations (
        echo   - Cleaning apps\knowledge\migrations...
        del /q apps\knowledge\migrations\*.py 2>nul
        del /q apps\knowledge\migrations\*.pyc 2>nul
        rmdir /s /q apps\knowledge\migrations\__pycache__ 2>nul
    )
    if exist apps\graph\migrations (
        echo   - Cleaning apps\graph\migrations...
        del /q apps\graph\migrations\*.py 2>nul
        del /q apps\graph\migrations\*.pyc 2>nul
        rmdir /s /q apps\graph\migrations\__pycache__ 2>nul
    )

    echo ✅ Reset complete.
)

:: Создание миграций
echo 🔄 Create migrations...
python manage.py makemigrations core objects hypotheses knowledge graph

:: Применение миграций
echo 🔄 Apply migrations...
python manage.py migrate

:: Генерация API-токена
echo 🔑 Generate API token...
python scripts\generate_token.py

:: Загрузка тестовых данных (раскомментируйте, если нужно заполнить БД демо-данными)
REM echo 📦 Load test data...
REM python manage.py seed_data

:: Запуск сервера
echo ✅ Done Start server...
echo 🌐 Open http://127.0.0.1:8000
echo 🔑 Admin page: http://127.0.0.1:8000/admin (login: admin, password: Turedy123)
echo 🔄 Server working. For stop use Ctrl+C.
python manage.py runserver