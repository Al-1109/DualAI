import os
import json
import logging
import asyncio
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

async def clean_channel_messages(context, except_ids=None):
    """Удаляет все сообщения в канале, кроме указанных в except_ids."""
    if except_ids is None:
        except_ids = []
    
    try:
        # Получаем историю сообщений в канале
        # Ограничиваем 100 последними сообщениями
        messages = []
        try:
            async for message in context.bot.get_chat_history(chat_id=CHANNEL_ID, limit=100):
                if message.message_id not in except_ids:
                    messages.append(message.message_id)
        except (TelegramError, AttributeError) as e:
            logger.warning(f"Не удалось получить историю чата: {e}")
            # Альтернативный подход - использовать ID сообщений из нашей базы
            message_ids = load_message_ids()
            # Удаляем все ID кроме тех, что нужно сохранить
            for key, msg_id in message_ids.items():
                if key != "welcome_message" and msg_id not in except_ids:
                    messages.append(msg_id)
        
        # Удаляем сообщения по одному
        for message_id in messages:
            try:
                await context.bot.delete_message(chat_id=CHANNEL_ID, message_id=message_id)
                logger.info(f"Удалено сообщение {message_id} из канала {CHANNEL_ID}")
                # Небольшая пауза, чтобы избежать ограничений API
                await asyncio.sleep(0.1)
            except TelegramError as e:
                logger.error(f"Не удалось удалить сообщение {message_id}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке канала: {e}")
        return False