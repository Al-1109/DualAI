@echo off
TITLE DualAI Bot Setup and Runner
COLOR 0A

ECHO ====================================
ECHO DualAI Bot Setup and Runner
ECHO ====================================
ECHO.

:: Проверка наличия Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Python не установлен! Установите Python 3.8 или выше.
    PAUSE
    EXIT /B 1
)

:: Создание виртуального окружения, если его нет
IF NOT EXIST venv (
    ECHO Создание виртуального окружения...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO ERROR: Не удалось создать виртуальное окружение!
        PAUSE
        EXIT /B 1
    )
)

:: Активация виртуального окружения
ECHO Активация виртуального окружения...
CALL venv\Scripts\activate

:: Установка необходимых пакетов
ECHO Установка необходимых пакетов...
pip install python-telegram-bot python-dotenv

:: Проверка наличия файла окружения
IF NOT EXIST .env (
    ECHO Создание файла .env...
    (
        ECHO # Переменные окружения для бота
        ECHO TEST_TELEGRAM_BOT_TOKEN=7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E
    ) > .env
    ECHO Файл .env создан с токеном по умолчанию. Измените его при необходимости.
)

:: Запуск бота через систему мониторинга
ECHO.
ECHO ====================================
ECHO Запуск бота...
ECHO ====================================
ECHO.
ECHO Для остановки бота нажмите Ctrl+C в этой консоли.
ECHO.

python windows_bot_runner.py

:: Деактивация виртуального окружения при завершении работы
CALL venv\Scripts\deactivate.bat

ECHO.
ECHO ====================================
ECHO Бот остановлен
ECHO ====================================
ECHO.

PAUSE 