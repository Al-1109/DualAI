from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import traceback
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("webhook")

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.environ.get('TEST_TELEGRAM_BOT_TOKEN')
WEBHOOK_SECRET = os.environ.get('TEST_WEBHOOK_SECRET')

if not TELEGRAM_BOT_TOKEN:
    logger.warning("Токен бота не найден в переменных окружения, использую fallback токен")
    TELEGRAM_BOT_TOKEN = "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"  # Fallback токен

# Проверяем наличие webhook secret
if not WEBHOOK_SECRET:
    logger.warning("WEBHOOK_SECRET не найден. Верификация запросов будет отключена.")

# Базовый URL для Telegram API
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram_message(chat_id, text, reply_markup=None):
    """Отправляет сообщение пользователю через Telegram API."""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        logger.info(f"Отправка сообщения на {chat_id}: {text[:50]}...")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            logger.info(f"Сообщение успешно отправлено, chat_id: {chat_id}")
            return {"ok": True, "response": response.json()}
        else:
            logger.error(f"Ошибка API при отправке: {response.status_code}, {response.text}")
            return {"ok": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Исключение при отправке сообщения: {e}")
        logger.debug(traceback.format_exc())
        return {"ok": False, "error": str(e)}

# Базовый обработчик для Vercel
def handler(event, context):
    """Обрабатывает запросы для Serverless функции Vercel."""
    try:
        # HTTP метод
        method = event.get('method', 'UNKNOWN')
        
        # Обработка GET-запроса для проверки работоспособности
        if method == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'ok',
                    'message': 'Webhook активен',
                    'timestamp': str(datetime.now()),
                    'version': '1.2.0'
                })
            }
        
        # Обработка POST-запроса от Telegram
        elif method == 'POST':
            # Верификация запроса от Telegram
            secret_header = event.get('headers', {}).get('x-telegram-bot-api-secret-token')
            
            if WEBHOOK_SECRET and secret_header != WEBHOOK_SECRET:
                logger.warning("Получен неверифицированный запрос")
                return {
                    'statusCode': 403,
                    'body': json.dumps({'ok': False, 'error': 'Forbidden'})
                }
            
            # Парсинг данных запроса
            try:
                body = event.get('body', '{}')
                if isinstance(body, str):
                    update = json.loads(body)
                else:
                    update = body
                    
                logger.info(f"Получено обновление ID: {update.get('update_id')}")
                
                # Обработка текстовых сообщений
                if 'message' in update and 'text' in update['message']:
                    chat_id = update['message']['chat']['id']
                    text = update['message']['text']
                    user = update['message']['from'].get('first_name', 'пользователь')
                    
                    logger.info(f"Сообщение от {user} ({chat_id}): {text}")
                    
                    if text == '/start':
                        # Создаем клавиатуру с кнопками
                        keyboard = {
                            "inline_keyboard": [
                                [{"text": "О боте", "callback_data": "info"}],
                                [{"text": "Тест", "callback_data": "test"}]
                            ]
                        }
                        
                        # Отправляем приветствие
                        send_telegram_message(
                            chat_id, 
                            f"👋 Привет, {user}!\n\nЯ тестовый бот для проекта DualAI на Vercel.\nЯ использую webhook-подход.",
                            keyboard
                        )
                    else:
                        # Отправляем эхо
                        send_telegram_message(chat_id, f"Вы сказали: {text}")
                
                # Обработка нажатий на кнопки
                elif 'callback_query' in update:
                    callback = update['callback_query']
                    chat_id = callback['message']['chat']['id']
                    data = callback['data']
                    
                    logger.info(f"Получен callback с данными: {data}")
                    
                    if data == 'info':
                        send_telegram_message(chat_id, "Это тестовый бот для проекта DualAI на Vercel через webhook.")
                    elif data == 'test':
                        send_telegram_message(chat_id, "Тестовое сообщение. Webhook работает!")
                    else:
                        send_telegram_message(chat_id, f"Получена команда: {data}")
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({'ok': True})
                }
                
            except Exception as e:
                logger.error(f"Ошибка обработки данных: {e}")
                logger.debug(traceback.format_exc())
                return {
                    'statusCode': 400,
                    'body': json.dumps({'ok': False, 'error': f'Invalid request: {str(e)}'})
                }
        
        # Обработка других HTTP методов
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'ok': False, 'error': 'Method not allowed'})
            }
            
    except Exception as e:
        logger.error(f"Общая ошибка обработки webhook: {e}")
        logger.debug(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({'ok': False, 'error': str(e)})
        } 