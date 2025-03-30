import os
import logging
import hmac
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

# Импортируем утилиты
from utils import load_message_ids, save_message_ids, load_content_file, send_to_channel, CHANNEL_ID, clean_all_channel_messages, send_photo_to_channel

# Импортируем наши обработчики
from handlers.client import start_command, language_callback, menu_callback

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Определяем, в каком окружении работаем (тестовое или продакшен)
IS_TEST_ENV = os.getenv("VERCEL_ENV") == "preview"
BOT_TOKEN = os.getenv("TEST_TELEGRAM_BOT_TOKEN") if IS_TEST_ENV else os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME = os.getenv("TEST_BOT_USERNAME") if IS_TEST_ENV else None
WEBHOOK_SECRET = os.getenv("TEST_WEBHOOK_SECRET") if IS_TEST_ENV else os.getenv("WEBHOOK_SECRET")

if not BOT_TOKEN:
    raise ValueError("Bot token not configured. Please set TEST_TELEGRAM_BOT_TOKEN for test environment or TELEGRAM_BOT_TOKEN for production.")

# Логируем информацию о текущем окружении
logger.info(f"Running in {'TEST' if IS_TEST_ENV else 'PRODUCTION'} environment")
logger.info(f"Using bot username: {BOT_USERNAME if BOT_USERNAME else 'Not configured'}")
logger.info(f"Webhook secret configured: {bool(WEBHOOK_SECRET)}")

# Константы для путей
WELCOME_IMAGE_PATH = "media/images/photo.jpg"

# Initialize the application globally
application = Application.builder().token(BOT_TOKEN).build()
application._initialized = False

def verify_telegram_request(request_headers, request_body):
    """Verify that the request is from Telegram using the secret token."""
    if not WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured")
        return True  # Allow all requests if secret is not configured
        
    token = request_headers.get('X-Telegram-Bot-Api-Secret-Token')
    if not token:
        logger.warning("No secret token in request headers")
        return False
        
    if not hmac.compare_digest(token, WEBHOOK_SECRET):
        logger.warning("Invalid secret token")
        return False
        
    return True

# Register handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CallbackQueryHandler(language_callback, pattern=r'^lang_'))
application.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^menu_'))

# Text message handler
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))