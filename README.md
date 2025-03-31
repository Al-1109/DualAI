# DualAI - Telegram Bot на Vercel

## Описание проекта
DualAI - это Telegram бот для работы с недвижимостью, развернутый на платформе Vercel. Проект демонстрирует использование serverless-функций для обработки Telegram webhook и взаимодействия с пользователями.

## Архитектура
Проект использует гибридную архитектуру:
- **Локальная разработка**: Python бот с long polling
- **Продакшен**: JavaScript webhook на Vercel

## Основные компоненты
- **api/webhook.js** - JavaScript обработчик webhook для Vercel
- **test_bot.py** - Python бот для локальной разработки (long polling)
- **watchdog_bot.py** - Скрипт мониторинга для локального запуска бота
- **set_webhook.py** - Утилита для управления webhook в Telegram API

## Использование

### Локальная разработка и тестирование
1. Клонировать репозиторий
   ```
   git clone [URL репозитория]
   ```

2. Создать виртуальное окружение Python
   ```
   python -m venv venv
   source venv/bin/activate  # На Windows: venv\Scripts\activate
   ```

3. Установить зависимости
   ```
   pip install -r requirements.txt
   ```

4. Создать файл .env на основе .env.example
   ```
   cp .env.example .env
   # Отредактировать .env и добавить актуальные токены
   ```

5. Запустить бота локально
   ```
   python test_bot.py
   ```

6. Для мониторинга бота (опционально)
   ```
   python watchdog_bot.py
   ```

### Деплой на Vercel
1. Установить Vercel CLI
   ```
   npm install -g vercel
   ```

2. Выполнить деплой
   ```
   vercel --prod
   ```

3. Настроить webhook в Telegram API
   ```
   python set_webhook.py set --url https://[ваш-домен-vercel]/api/webhook --secret [ваш-секрет]
   ```

4. Проверить статус webhook
   ```
   python set_webhook.py info
   ```

## Vercel конфигурация
Файл `vercel.json` содержит настройки для маршрутизации API и сборки проекта:
```json
{
  "version": 2,
  "builds": [
    { "src": "api/*.js", "use": "@vercel/node" }
  ],
  "rewrites": [
    { "source": "/api/webhook", "destination": "/api/webhook.js" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,OPTIONS" },
        { "key": "Access-Control-Allow-Headers", "value": "X-Telegram-Bot-Api-Secret-Token,Content-Type" }
      ]
    }
  ]
}
```

## Окружение
Для работы проекта требуются следующие переменные окружения:
- `TEST_TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `TEST_WEBHOOK_SECRET` - секретный токен для верификации webhook

## Ограничения
- Long polling не работает на Vercel из-за ограничений serverless-архитектуры
- Webhook имеет ограничение по времени выполнения (10-60 секунд)

## Дополнительная документация
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - Подробный контекст проекта
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Текущий статус разработки

## Лицензия
MIT 