import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

# Импортируем утилиты
from utils import load_message_ids, save_message_ids, load_content_file

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
CHANNEL_ID = "@MirasolEstate"   # ID канала

# Файл для хранения ID сообщений
MESSAGE_IDS_FILE = "data/channel_messages.json"

async def send_to_channel(context, text, reply_markup=None, message_key="message"):
    """Функция для отправки сообщений в канал."""
    message_ids = load_message_ids()
    existing_message_id = message_ids.get(message_key)
    
    try:
        # Если есть существующее сообщение, пробуем отредактировать его
        if existing_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=existing_message_id,
                    text=text,
                    reply_markup=reply_markup
                )
                logger.info(f"Сообщение {message_key} обновлено в канале {CHANNEL_ID}")
                return None  # Возвращаем None, так как мы обновили существующее сообщение
            except TelegramError as e:
                logger.error(f"Ошибка при обновлении сообщения: {e}, отправляем новое")
                # Если сообщение не удалось обновить, отправляем новое
        
        # Отправляем новое сообщение
        message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            reply_markup=reply_markup
        )
        
        # Сохраняем ID нового сообщения
        message_ids[message_key] = message.message_id
        save_message_ids(message_ids)
        
        logger.info(f"Новое сообщение {message_key} отправлено в канал {CHANNEL_ID}")
        return message
    except Exception as e:
        logger.error(f"Ошибка отправки в канал: {e}")
        return None

async def send_welcome_to_channel(context):
    """Отправка приветственного сообщения в канал."""
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
    
    # Используем ключ "welcome_message" для сохранения/обновления этого сообщения
    await send_to_channel(context, welcome_message, reply_markup, "welcome_message")

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
    logger.info("Обновление приветственного сообщения в канале при запуске...")
    await send_welcome_to_channel(app)

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