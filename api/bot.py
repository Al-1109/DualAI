from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from telegram import Update
from telegram.ext import Application
from datetime import datetime

# Импортируем наш существующий бот
from bot import TELEGRAM_BOT_TOKEN, start_command, language_callback, menu_callback

# Инициализируем бота
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Добавляем обработчики
application.add_handler(start_command)
application.add_handler(language_callback)
application.add_handler(menu_callback)

async def handle_update(update_dict):
    """Обработка обновлений от Telegram."""
    update = Update.de_json(update_dict, application.bot)
    await application.process_update(update)

# Функция для Vercel
async def handler(request):
    """Точка входа для Vercel."""
    if request.method == 'POST':
        update_dict = json.loads(request.body)
        await handle_update(update_dict)
        return {'statusCode': 200, 'body': 'OK'}
    elif request.method == 'GET':
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'ok',
                'message': 'Vercel endpoint is working',
                'timestamp': datetime.now().isoformat()
            })
        }
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({
                'error': 'Method not allowed'
            })
        } 