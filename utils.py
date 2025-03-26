import os
import json
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

# Настройка логирования
logger = logging.getLogger(__name__)

# Файл для хранения ID сообщений
MESSAGE_IDS_FILE = "data/channel_messages.json"

# ID канала Telegram
CHANNEL_ID = "@New_Age_Realty"

# Функция для сохранения ID сообщений
def save_message_ids(message_ids):
    os.makedirs("data", exist_ok=True)
    with open(MESSAGE_IDS_FILE, 'w') as f:
        json.dump(message_ids, f)

# Функция для загрузки ID сообщений
def load_message_ids():
    try:
        with open(MESSAGE_IDS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"all_messages": []}

# Функция для загрузки содержимого файлов
def load_content_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return "Content file not found."

# Функция для отправки сообщений в канал
async def send_to_channel(context, text, reply_markup=None, message_key="message"):
    """Функция для отправки/обновления сообщений в канале."""
    message_ids = load_message_ids()
    existing_message_id = message_ids.get(message_key)
    
    try:
        # Если есть существующее сообщение, редактируем его
        if existing_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=existing_message_id,
                    text=text,
                    reply_markup=reply_markup
                )
                logger.info(f"Сообщение {message_key} (ID: {existing_message_id}) обновлено в канале {CHANNEL_ID}")
                return type('obj', (object,), {'message_id': existing_message_id})  # Возвращаем объект с message_id
            except Exception as e:
                logger.error(f"Ошибка при редактировании сообщения: {e}, отправляем новое")
                # Если сообщение не удалось обновить, продолжаем и отправляем новое
        
        # Отправляем новое сообщение
        message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            reply_markup=reply_markup,
            disable_notification=True  # Отключаем уведомление
        )
        
        # Сохраняем ID нового сообщения
        message_ids[message_key] = message.message_id
        
        # Также добавляем ID в список всех сообщений
        if "all_messages" not in message_ids:
            message_ids["all_messages"] = []
        
        if message.message_id not in message_ids["all_messages"]:
            message_ids["all_messages"].append(message.message_id)
        
        # Сохраняем обновленный список ID
        save_message_ids(message_ids)
        
        logger.info(f"Новое сообщение {message_key} (ID: {message.message_id}) отправлено в канал {CHANNEL_ID}")
        return message
    except Exception as e:
        logger.error(f"Ошибка отправки в канал: {e}")
        return None

async def reset_channel(context):
    """Полностью сбрасывает состояние канала - удаляет все сообщения и отправляет приветственное."""
    logger.info("Начинаем полный сброс состояния канала...")
    
    # Загружаем текущие ID сообщений
    message_ids = load_message_ids()
    
    # Удаляем все известные сообщения
    for msg_id in message_ids.get("all_messages", []):
        try:
            await context.bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
            logger.info(f"Удалено сообщение {msg_id}")
            await asyncio.sleep(0.1)  # Пауза для API
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение {msg_id}: {e}")
    
    # Отправляем приветственное сообщение
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
    
    # Отправляем сообщение
    message = await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=welcome_message,
        reply_markup=reply_markup,
        disable_notification=True
    )
    
    # Полностью сбрасываем данные о сообщениях
    new_message_ids = {
        "welcome_message": message.message_id,
        "all_messages": [message.message_id]
    }
    
    # Сохраняем новое состояние
    save_message_ids(new_message_ids)
    
    logger.info(f"Канал полностью сброшен. Новое приветственное сообщение: {message.message_id}")
    return message

async def clean_all_channel_messages(context, except_message_id=None, force_cleanup=False):
    """
    Удаляет все сообщения в канале, за исключением указанного ID.
    
    Args:
        context: Контекст бота
        except_message_id: ID сообщения, которое нужно сохранить
        force_cleanup: Если True, принудительно удаляет все сообщения, кроме указанного
    """
    message_ids = load_message_ids()
    
    # Получаем список всех сообщений
    all_messages = message_ids.get("all_messages", [])
    
    # Если принудительная очистка или больше одного сообщения
    if force_cleanup or len(all_messages) > 1:
        # Создаем новый список для сохранения ID сообщений, которые не удалось удалить
        failed_to_delete = []
        
        # Счетчик удаленных сообщений
        deleted_count = 0
        
        # Удаляем все сообщения, кроме исключенного
        for msg_id in all_messages:
            if msg_id != except_message_id:
                try:
                    await context.bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
                    logger.info(f"Удалено сообщение {msg_id} из канала {CHANNEL_ID}")
                    deleted_count += 1
                    # Небольшая пауза, чтобы избежать ограничений API
                    await asyncio.sleep(0.1)
                except TelegramError as e:
                    logger.error(f"Не удалось удалить сообщение {msg_id}: {e}")
                    failed_to_delete.append(msg_id)
        
        # ВАЖНОЕ ИЗМЕНЕНИЕ: Создаем новый список сообщений вместо модификации существующего
        new_messages = []
        if except_message_id is not None:
            new_messages.append(except_message_id)
        
        # Обновляем все message_ids с новым списком
        message_ids = {"all_messages": new_messages}
        if except_message_id is not None:
            message_ids["welcome_message"] = except_message_id
        
        # Сохраняем обновленный список
        save_message_ids(message_ids)
        
        return deleted_count > 0
    else:
        logger.info("Нет дополнительных сообщений для удаления")
        return False