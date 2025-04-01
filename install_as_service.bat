@echo off
TITLE DualAI Bot Service Installer
COLOR 0A

ECHO ====================================
ECHO DualAI Bot Service Installer
ECHO ====================================
ECHO.

:: Проверка администраторских прав
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Этот скрипт требует прав администратора!
    ECHO Пожалуйста, запустите его от имени администратора.
    PAUSE
    EXIT /B 1
)

:: Получение полного пути к текущей директории
SET "CURRENT_DIR=%~dp0"
SET "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

:: Создание .bat файла для службы
ECHO Создание скрипта для службы...
(
    ECHO @echo off
    ECHO cd /d "%CURRENT_DIR%"
    ECHO CALL venv\Scripts\activate
    ECHO python windows_bot_runner.py
    ECHO EXIT /B 0
) > "%CURRENT_DIR%\run_bot_service.bat"

:: Установка NSSM, если его нет
IF NOT EXIST "%CURRENT_DIR%\nssm.exe" (
    ECHO Загрузка NSSM (Non-Sucking Service Manager)...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm' -Force"
    IF EXIST "%TEMP%\nssm\nssm-2.24\win64\nssm.exe" (
        copy "%TEMP%\nssm\nssm-2.24\win64\nssm.exe" "%CURRENT_DIR%\" >nul
    ) ELSE (
        copy "%TEMP%\nssm\nssm-2.24\win32\nssm.exe" "%CURRENT_DIR%\" >nul
    )
    del "%TEMP%\nssm.zip" >nul 2>&1
    rmdir /s /q "%TEMP%\nssm" >nul 2>&1
)

:: Удаление существующей службы, если она уже есть
"%CURRENT_DIR%\nssm.exe" stop DualAIBot >nul 2>&1
"%CURRENT_DIR%\nssm.exe" remove DualAIBot confirm >nul 2>&1

:: Установка новой службы
ECHO Установка службы DualAIBot...
"%CURRENT_DIR%\nssm.exe" install DualAIBot "%CURRENT_DIR%\run_bot_service.bat"
"%CURRENT_DIR%\nssm.exe" set DualAIBot DisplayName "DualAI Telegram Bot"
"%CURRENT_DIR%\nssm.exe" set DualAIBot Description "Telegram бот для проекта DualAI с long polling"
"%CURRENT_DIR%\nssm.exe" set DualAIBot Start SERVICE_AUTO_START
"%CURRENT_DIR%\nssm.exe" set DualAIBot AppStdout "%CURRENT_DIR%\logs\service_stdout.log"
"%CURRENT_DIR%\nssm.exe" set DualAIBot AppStderr "%CURRENT_DIR%\logs\service_stderr.log"
"%CURRENT_DIR%\nssm.exe" set DualAIBot AppRotateFiles 1
"%CURRENT_DIR%\nssm.exe" set DualAIBot AppRotateBytes 10485760

:: Запуск службы
ECHO Запуск службы DualAIBot...
"%CURRENT_DIR%\nssm.exe" start DualAIBot

ECHO.
ECHO ====================================
ECHO Установка службы завершена!
ECHO ====================================
ECHO.
ECHO Служба "DualAI Telegram Bot" установлена и запущена.
ECHO Она будет автоматически запускаться при старте системы.
ECHO.
ECHO Для управления службой используйте команды:
ECHO - Запуск:   sc start DualAIBot
ECHO - Остановка: sc stop DualAIBot
ECHO - Статус:    sc query DualAIBot
ECHO.

PAUSE 