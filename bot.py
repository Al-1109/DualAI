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
    """
    Отправка приветственного сообщения с кнопками перехода к боту на разных языках.
    Это сообщение будет закреплено в канале.
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
    
    # Получаем текущие сообщения
    message_ids = load_message_ids()
    pinned_message_id = message_ids.get("pinned_welcome")
    
    try:
        # Проверяем, существует ли уже закрепленное сообщение
        if pinned_message_id:
            try:
                # Пытаемся редактировать существующее сообщение
                if "welcome_has_photo" in message_ids and message_ids["welcome_has_photo"]:
                    # Если у нас есть фото, то редактируем подпись
                    await context.bot.edit_message_caption(
                        chat_id=CHANNEL_ID,
                        message_id=pinned_message_id,
                        caption=welcome_message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Обновлено закрепленное сообщение с ID: {pinned_message_id}")
                    return pinned_message_id
                else:
                    # Если нет фото, редактируем текст
                    await context.bot.edit_message_text(
                        chat_id=CHANNEL_ID,
                        message_id=pinned_message_id,
                        text=welcome_message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Обновлено закрепленное сообщение с ID: {pinned_message_id}")
                    return pinned_message_id
            except Exception as e:
                logger.error(f"Не удалось отредактировать закрепленное сообщение: {e}")
                # Продолжаем и создаем новое сообщение
        
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
                message_ids["welcome_has_photo"] = True
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
            message_ids["welcome_has_photo"] = False
        
        # Закрепляем сообщение
        await context.bot.pin_chat_message(
            chat_id=CHANNEL_ID,
            message_id=message.message_id,
            disable_notification=True
        )
        
        # Сохраняем ID нового сообщения
        message_ids["pinned_welcome"] = message.message_id
        
        # Добавляем в список всех сообщений
        if "all_messages" not in message_ids:
            message_ids["all_messages"] = []
        
        if message.message_id not in message_ids["all_messages"]:
            message_ids["all_messages"].append(message.message_id)
        
        save_message_ids(message_ids)
        
        # Удаляем все другие сообщения канала, кроме закрепленного
        # Но только если это новый pin, а не обновление существующего
        if not pinned_message_id or pinned_message_id != message.message_id:
            await clean_all_channel_messages(context, message.message_id, True)
        
        logger.info(f"Отправлено и закреплено приветственное сообщение (ID: {message.message_id})")
        return message.message_id
            
    except Exception as e:
        logger.error(f"Ошибка при работе с приветственным сообщением: {e}")
        return None

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