import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

# Импортируем утилиты
from utils import load_message_ids, save_message_ids, load_content_file, send_to_channel, CHANNEL_ID, clean_all_channel_messages

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
    logger.info("Отправляем приветственное сообщение...")
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
    
    # Принудительно очищаем канал от всех сообщений кроме welcome
    await clean_all_channel_messages(context, None, True)
    
    # Отправляем новое приветственное сообщение
    message = await send_to_channel(context, welcome_message, reply_markup, "welcome_message")
    
    # Окончательно очищаем все сообщения, кроме только что отправленного
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
        # Проверяем ID сообщений в канале
        message_ids = load_message_ids()
        
        # Проверяем, находится ли канал в неправильном состоянии
        welcome_message_id = message_ids.get("welcome_message")
        is_incorrect_state = False
        
        # Если есть welcome_message_id, но он не является "активным" сообщением
        # или есть другие сообщения
        if welcome_message_id:
            # Если в канале больше одного сообщения, считаем, что состояние неправильное
            if len(message_ids.get("all_messages", [])) > 1:
                is_incorrect_state = True
                logger.info("Найдены дополнительные сообщения в канале")
            
            # Если в списке ключей есть не-welcome, значит, было переключение на подменю
            for key in message_ids.keys():
                if key != "welcome_message" and key != "all_messages":
                    is_incorrect_state = True
                    logger.info(f"Найдено сообщение подменю: {key}")
        else:
            # Если нет welcome_message_id, однозначно состояние неправильное
            is_incorrect_state = True
            logger.info("Приветственное сообщение не найдено")
        
        # Если обнаружено неправильное состояние, возвращаем канал к приветственному сообщению
        if is_incorrect_state:
            logger.info("Обнаружено неправильное состояние канала, восстанавливаем приветственное сообщение...")
            await send_welcome_to_channel(app)
        else:
            logger.info("Канал в правильном состоянии, никаких действий не требуется")
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