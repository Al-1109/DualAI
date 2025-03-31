from http import HTTPStatus
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

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

async def handler(request):
    """Точка входа для Vercel Serverless Function."""
    logger.info(f"Получен запрос: {request.method}")
    
    # Обработка GET-запроса для проверки работоспособности
    if request.method == 'GET':
        logger.info("Обработка GET запроса")
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
        logger.info("Обработка POST запроса")
        
        # Проверяем аутентичность запроса
        if not verify_telegram_request(request.headers):
            logger.warning("Не удалось верифицировать запрос")
            return {
                'statusCode': HTTPStatus.UNAUTHORIZED,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        try:
            # Логируем содержимое запроса
            logger.info(f"Тело запроса: {request.body[:100]}...")
            
            # В полной реализации здесь был бы код для отправки ответа в Telegram,
            # но для тестирования мы просто возвращаем успешный статус
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({'status': 'ok', 'message': 'Webhook received'})
            }
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {str(e)}")
            return {
                'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'body': json.dumps({'error': str(e)})
            }
    
    # Обработка остальных методов
    else:
        logger.warning(f"Неподдерживаемый метод: {request.method}")
        return {
            'statusCode': HTTPStatus.METHOD_NOT_ALLOWED,
            'body': json.dumps({'error': 'Method not allowed'})
        } 