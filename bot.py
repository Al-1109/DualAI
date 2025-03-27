import os
import logging
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
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Константы для путей
WELCOME_IMAGE_PATH = "media/images/photo.jpg"

async def send_welcome_to_channel(context):
    """Отправка приветственного сообщения с изображением в канал без мерцания."""
    logger.info("Отправляем приветственное сообщение с изображением...")
    welcome_message = load_content_file("Telegram_content/welcome_message.md")
    
    # Создаем клавиатуру для выбора языка
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        ],
        [
            InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
        ],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Получаем текущие сообщения
    message_ids = load_message_ids()
    
    try:
        # Отправляем изображение с текстом в подписи, отключив уведомления
        with open(WELCOME_IMAGE_PATH, "rb") as photo:
            message = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo,
                caption=welcome_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
                disable_notification=True  # Отключаем пуши
            )
            
            # Сохраняем ID сообщения
            message_ids["welcome_message"] = message.message_id
            
            # Добавляем в список всех сообщений
            if "all_messages" not in message_ids:
                message_ids["all_messages"] = []
            
            if message.message_id not in message_ids["all_messages"]:
                message_ids["all_messages"].append(message.message_id)
            
            save_message_ids(message_ids)
            
            # Очищаем все сообщения, кроме только что отправленного
            # (теперь удаление происходит после успешной отправки нового сообщения)
            await clean_all_channel_messages(context, message.message_id, True)
            
            logger.info(f"Отправлено приветственное сообщение с изображением (ID: {message.message_id})")
            return message
            
    except Exception as e:
        logger.error(f"Ошибка при отправке изображения: {e}")
        # Если не удалось отправить изображение, отправляем обычное текстовое сообщение (тоже без уведомления)
        logger.info("Отправляем текстовое сообщение без изображения...")
        message = await send_to_channel(context, welcome_message, reply_markup, "welcome_message")
        
        # Очищаем все сообщения, кроме только что отправленного
        await clean_all_channel_messages(context, message.message_id, True)
        
        return message

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
        # Принудительно сбрасываем канал при каждом запуске
        logger.info("Запуск бота: принудительный сброс состояния канала")
        # Используем send_welcome_to_channel вместо импорта reset_channel
        await send_welcome_to_channel(app)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

def main() -> None:
    """Запуск бота."""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("sendtochannel", admin_send_to_channel))
    
    # Обработчики коллбэков от inline кнопок
    application.add_handler(CallbackQueryHandler(language_callback, pattern=r'^lang_'))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^menu_'))
    
    # Обработчик для неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Добавляем функцию, которая выполнится при запуске бота
    application.post_init = startup

    # Запускаем бота
    logger.info("Bot started")
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

if __name__ == '__main__':
    main()