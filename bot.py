import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

# Импортируем утилиты
from utils import load_message_ids, save_message_ids, load_content_file, send_to_channel, CHANNEL_ID

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

async def send_welcome_to_channel(context):
    """Отправка приветственного сообщения в канал."""
    # Удаляем старое сообщение если оно есть
    message_ids = load_message_ids()
    welcome_message_id = message_ids.get("welcome_message")
    
    # Если есть старое сообщение, удаляем его
    if welcome_message_id:
        try:
            await context.bot.delete_message(chat_id=CHANNEL_ID, message_id=welcome_message_id)
            logger.info(f"Удалено старое приветственное сообщение {welcome_message_id}")
            # Удаляем ID из хранилища
            del message_ids["welcome_message"]
            save_message_ids(message_ids)
        except Exception as e:
            logger.error(f"Не удалось удалить старое приветственное сообщение: {e}")
    
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
    
    # Отправляем новое приветственное сообщение
    message = await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=welcome_message,
        reply_markup=reply_markup,
        disable_notification=True  # Отправка без уведомления
    )
    
    # Сохраняем ID нового сообщения
    message_ids["welcome_message"] = message.message_id
    save_message_ids(message_ids)
    
    logger.info(f"Новое приветственное сообщение {message.message_id} отправлено в канал {CHANNEL_ID}")
    
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
    logger.info("Обновление приветственного сообщения в канале при запуске...")
    await send_welcome_to_channel(app)
    
    # Не отправляем приветственное сообщение пользователям автоматически
    # Пользователи получат его, когда нажмут /start

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