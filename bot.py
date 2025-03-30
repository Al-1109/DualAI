import os
import logging
import asyncio  # Добавлен импорт asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError
import hmac

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
BOT_USERNAME = os.getenv("TEST_TELEGRAM_BOT_USERNAME") if IS_TEST_ENV else None
WEBHOOK_SECRET = os.getenv("TEST_WEBHOOK_SECRET") if IS_TEST_ENV else None

if not BOT_TOKEN:
    raise ValueError("Bot token not configured. Please set TEST_TELEGRAM_BOT_TOKEN for test environment or TELEGRAM_BOT_TOKEN for production.")

# Логируем информацию о текущем окружении
logger.info(f"Running in {'TEST' if IS_TEST_ENV else 'PRODUCTION'} environment")
logger.info(f"Using bot username: {BOT_USERNAME if BOT_USERNAME else 'Not configured'}")
logger.info(f"Webhook secret configured: {bool(WEBHOOK_SECRET)}")

# Константы для путей
WELCOME_IMAGE_PATH = "media/images/photo.jpg"

async def send_welcome_to_channel(context):
    """
    Отправка приветственного сообщения с кнопками перехода к боту на разных языках.
    Сообщение не закрепляется, но является единственным в канале.
    """
    logger.info("Отправляем приветственное сообщение с кнопками перехода к боту...")
    welcome_message = load_content_file("Telegram_content/welcome_message.md")
    
    # Получаем имя бота из контекста
    bot_username = context.bot.username
    
    # Создаем кнопки перехода к боту с выбором языка
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 Start in English", url=f"https://t.me/{bot_username}?start=lang_en"),
            InlineKeyboardButton("🇪🇸 Comenzar en Español", url=f"https://t.me/{bot_username}?start=lang_es"),
        ],
        [
            InlineKeyboardButton("🇩🇪 Auf Deutsch starten", url=f"https://t.me/{bot_username}?start=lang_de"),
            InlineKeyboardButton("🇫🇷 Commencer en Français", url=f"https://t.me/{bot_username}?start=lang_fr"),
        ],
        [
            InlineKeyboardButton("🇷🇺 Начать на русском", url=f"https://t.me/{bot_username}?start=lang_ru"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Сначала удаляем все существующие сообщения в канале
    message_ids = load_message_ids()
    for msg_id in message_ids.get("all_messages", []):
        try:
            await context.bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
            logger.info(f"Удалено сообщение {msg_id}")
            await asyncio.sleep(0.1)  # Небольшая пауза для API
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение {msg_id}: {e}")
    
    # Отправляем новое сообщение с изображением
    try:
        with open(WELCOME_IMAGE_PATH, "rb") as photo:
            message = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo,
                caption=welcome_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
                disable_notification=True
            )
            
            # Отмечаем, что сообщение содержит фото
            message_ids = {"welcome_message": message.message_id, "welcome_has_photo": True, "all_messages": [message.message_id]}
            
    except Exception as e:
        logger.error(f"Ошибка при отправке изображения: {e}")
        # Если не удалось отправить изображение, отправляем обычное текстовое сообщение
        message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=welcome_message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_notification=True
        )
        message_ids = {"welcome_message": message.message_id, "welcome_has_photo": False, "all_messages": [message.message_id]}
    
    # Сохраняем новое состояние сообщений (только одно сообщение в канале)
    save_message_ids(message_ids)
    
    logger.info(f"Отправлено приветственное сообщение (ID: {message.message_id})")
    return message.message_id

async def admin_send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Административная команда для отправки сообщения в канал."""
    # Здесь можно добавить проверку прав администратора
    # Например:
    # if update.effective_user.id != ADMIN_ID:
    #     await update.message.reply_text("У вас нет прав для выполнения этой команды.")
    #     return
    
    await update.message.reply_text("Отправка приветственного сообщения в канал...")
    await send_welcome_to_channel(context)
    await update.message.reply_text("Сообщение отправлено в канал.")

async def startup(app):
    """Функция, которая выполняется при запуске бота."""
    try:
        # Отправляем приветственное сообщение в канал
        logger.info("Запуск бота: отправка приветственного сообщения в канал")
        await send_welcome_to_channel(app)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

def main() -> None:
    """Запуск бота."""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Импортируем административные обработчики
    from handlers import admin

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("sendtochannel", admin_send_to_channel))
    
    # Обработчики коллбэков от inline кнопок основного меню
    application.add_handler(CallbackQueryHandler(language_callback, pattern=r'^lang_'))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^menu_'))
    
    # Обработчики коллбэков административной панели
    application.add_handler(CallbackQueryHandler(admin.admin_panel_callback, pattern=r'^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin.admin_content_management, pattern=r'^admin_content$'))
    application.add_handler(CallbackQueryHandler(admin.admin_statistics, pattern=r'^admin_stats$'))
    application.add_handler(CallbackQueryHandler(admin.admin_notifications, pattern=r'^admin_notifications$'))
    application.add_handler(CallbackQueryHandler(admin.admin_back_to_main, pattern=r'^admin_back_to_main$'))
    
    # Обработчики тестовых команд (только для тестового окружения)
    if IS_TEST_ENV:
        application.add_handler(CallbackQueryHandler(admin.admin_test_commands, pattern=r'^admin_test_commands$'))
        application.add_handler(CallbackQueryHandler(admin.admin_test_refresh, pattern=r'^admin_test_refresh$'))
        application.add_handler(CallbackQueryHandler(admin.admin_test_send, pattern=r'^admin_test_send$'))
        # Добавляем тестовые команды
        application.add_handler(CommandHandler("test", lambda update, context: update.message.reply_text("Test command received!")))
        application.add_handler(CommandHandler("env", lambda update, context: update.message.reply_text(
            f"Environment: {ENVIRONMENT}\nVercel: {'YES' if os.getenv('VERCEL') else 'NO'}\nAdmin ID: {ADMIN_ID}"
        )))
        application.add_handler(CommandHandler("ping", lambda update, context: update.message.reply_text("Pong! 🏓")))
        application.add_handler(CommandHandler("echo", lambda update, context: update.message.reply_text(
            " ".join(context.args) if context.args else "Usage: /echo [text]"
        )))
    
    # Обработчик для неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Добавляем функцию, которая выполнится при запуске бота
    application.post_init = startup

    # Запускаем бота
    logger.info(f"Bot started in {ENVIRONMENT} environment")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик неизвестных команд."""
    await update.message.reply_text(
        "Извините, я не распознал эту команду. Попробуйте /start для начала работы или /sendtochannel для отправки сообщения в канал."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    # В будущем здесь будет обработка естественного языка через OpenAI
    user_language = context.user_data.get('language', 'en')
    
    await update.message.reply_text(
        f"В будущем я смогу отвечать на ваши вопросы. Пока что используйте меню."
    )

def verify_telegram_request(request) -> bool:
    """Verify that the request came from Telegram using the secret token."""
    if not BOT_TOKEN or not WEBHOOK_SECRET:
        return False
        
    # Get token from header
    token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    if not token:
        return False
        
    # Compare tokens using constant time comparison
    return hmac.compare_digest(token, WEBHOOK_SECRET)

if __name__ == '__main__':
    main()