from http import HTTPStatus
import json
import os
import hmac
import hashlib
from telegram import Update
from telegram.ext import Application
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота и webhook secret из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TEST_TELEGRAM_BOT_TOKEN')
WEBHOOK_SECRET = os.getenv('TEST_WEBHOOK_SECRET')

# Проверка переменных окружения
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Telegram bot token is not set")
if not WEBHOOK_SECRET:
    raise ValueError("Webhook secret is not set")

# Инициализируем бота
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Импортируем обработчики команд из основного файла
# Примечание: импорт кода может привести к циклической зависимости, 
# поэтому лучше не импортировать из bot.py, а определить здесь нужные обработчики
# или использовать общий модуль с обработчиками
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.client import start_command, language_callback, menu_callback, handle_message, unknown_command

# Добавляем обработчики
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CallbackQueryHandler(language_callback, pattern=r'^lang_'))
application.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^menu_'))
application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

async def process_telegram_update(update_dict):
    """Обработка обновлений от Telegram."""
    update = Update.de_json(update_dict, application.bot)
    await application.process_update(update)

def verify_telegram_request(request_headers, request_body):
    """Проверка подлинности запроса от Telegram."""
    if WEBHOOK_SECRET == "test_webhook_secret":
        # В тестовом режиме пропускаем проверку
        return True
        
    # Для продакшена проверяем подпись
    telegram_hash = request_headers.get('X-Telegram-Bot-Api-Secret-Token')
    if not telegram_hash:
        return False
    
    # Проверяем, совпадает ли полученный хэш с нашим секретом
    return telegram_hash == WEBHOOK_SECRET

async def handler(request):
    """Точка входа для Vercel Serverless Function."""
    # Обработка GET-запроса для проверки работоспособности
    if request.method == 'GET':
        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps({
                'status': 'ok',
                'message': 'Telegram webhook endpoint is active',
                'timestamp': datetime.now().isoformat(),
                'environment': os.getenv('VERCEL_ENV', 'unknown')
            })
        }
    
    # Обработка POST-запроса от Telegram
    elif request.method == 'POST':
        # Проверяем аутентичность запроса
        if not verify_telegram_request(request.headers, request.body):
            return {
                'statusCode': HTTPStatus.UNAUTHORIZED,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        try:
            update_dict = json.loads(request.body)
            await process_telegram_update(update_dict)
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({'status': 'ok'})
            }
        except Exception as e:
            return {
                'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'body': json.dumps({'error': str(e)})
            }
    
    # Обработка остальных методов
    else:
        return {
            'statusCode': HTTPStatus.METHOD_NOT_ALLOWED,
            'body': json.dumps({'error': 'Method not allowed'})
        } 