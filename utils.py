import os
import json
import logging
from telegram.error import TelegramError

# Настройка логирования
logger = logging.getLogger(__name__)

# Файл для хранения ID сообщений
MESSAGE_IDS_FILE = "data/channel_messages.json"

# ID канала Telegram
CHANNEL_ID = "@MirasolEstate"

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
        return {}

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