from http import HTTPStatus
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Получаем настройки из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TEST_TELEGRAM_BOT_TOKEN')
WEBHOOK_SECRET = os.getenv('TEST_WEBHOOK_SECRET')

# Проверяем конфигурацию
if not TELEGRAM_BOT_TOKEN:
    logger.error("Токен бота не найден в переменных окружения")
else:
    logger.info(f"Токен бота получен, длина: {len(TELEGRAM_BOT_TOKEN)}")

if not WEBHOOK_SECRET:
    logger.warning("Webhook secret не найден в переменных окружения")
else:
    logger.info("Webhook secret получен")

def verify_telegram_request(request_headers):
    """Проверка подлинности запроса от Telegram."""
    # В тестовом режиме пропускаем проверку
    if WEBHOOK_SECRET == "test_webhook_secret":
        return True
        
    # Проверяем заголовок X-Telegram-Bot-Api-Secret-Token
    telegram_hash = request_headers.get('X-Telegram-Bot-Api-Secret-Token')
    if not telegram_hash:
        return False
    
    # Сравниваем секреты
    return telegram_hash == WEBHOOK_SECRET

def handler(request):
    """Простая функция-обработчик для Vercel."""
    
    # Обработка GET-запроса
    if request.method == 'GET':
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'ok',
                'message': 'Webhook endpoint is active',
                'timestamp': str(datetime.now())
            })
        }
    
    # Обработка POST-запроса
    elif request.method == 'POST':
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'ok',
                'message': 'Webhook received'
            })
        }
    
    # Обработка остальных методов
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({
                'error': 'Method not allowed'
            })
        } 