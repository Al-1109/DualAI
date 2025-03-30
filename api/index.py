import json
import os
import logging
import sys
import hmac
from http import HTTPStatus
from telegram import Update
from datetime import datetime

# Настраиваем пути для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем основное приложение бота
from bot import application, verify_telegram_request

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определяем, в каком окружении работаем (тестовое или продакшен)
IS_TEST_ENV = os.getenv("VERCEL_ENV") == "preview"
BOT_TOKEN = os.getenv("TEST_TELEGRAM_BOT_TOKEN") if IS_TEST_ENV else os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("TEST_WEBHOOK_SECRET") if IS_TEST_ENV else os.getenv("WEBHOOK_SECRET")

# Обработчик Vercel-совместимого API эндпоинта
async def handler(request):
    """Handle incoming requests for Vercel."""
    try:
        if request.method == 'GET':
            body = {
                "status": "ok",
                "message": "DualAI bot webhook endpoint is ready",
                "timestamp": datetime.now().isoformat(),
                "environment": "TEST" if IS_TEST_ENV else "PRODUCTION",
                "bot_info": {
                    "token_configured": bool(BOT_TOKEN),
                    "webhook_secret_configured": bool(WEBHOOK_SECRET),
                    "endpoint_url": request.headers.get('x-forwarded-proto', 'http') + '://' + request.headers.get('x-forwarded-host', 'localhost')
                }
            }
            return {
                "statusCode": 200,
                "body": json.dumps(body),
                "headers": {
                    "Content-Type": "application/json"
                }
            }
        elif request.method == 'POST':
            # Проверяем валидность запроса от Telegram
            if not verify_telegram_request(request.headers, request.body):
                return {
                    "statusCode": 401,
                    "body": json.dumps({"error": "Unauthorized request"}),
                    "headers": {"Content-Type": "application/json"}
                }
            
            # Парсим запрос от Telegram
            try:
                update_dict = json.loads(request.body)
            except json.JSONDecodeError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid JSON"}),
                    "headers": {"Content-Type": "application/json"}
                }
            
            # Инициализируем бота если не инициализирован
            if not hasattr(application, '_initialized'):
                await application.initialize()
                application._initialized = True
            
            # Обрабатываем обновление
            update = Update.de_json(update_dict, application.bot)
            await application.process_update(update)
            
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "ok"}),
                "headers": {"Content-Type": "application/json"}
            }
        else:
            return {
                "statusCode": 405,
                "body": json.dumps({"error": "Method not allowed"}),
                "headers": {"Content-Type": "application/json"}
            }
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        } 