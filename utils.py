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

# Функция для очистки всех сообщений в канале
async def clean_all_channel_messages(context, except_message_id=None):
    """Удаляет все сообщения в канале, за исключением указанного ID."""
    message_ids = load_message_ids()
    
    # Получаем список всех сообщений
    all_messages = message_ids.get("all_messages", [])
    
    # Создаем новый список для сохранения ID сообщений, которые не удалось удалить
    failed_to_delete = []
    
    # Удаляем все сообщения, кроме исключенного
    for msg_id in all_messages:
        if msg_id != except_message_id:
            try:
                await context.bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
                logger.info(f"Удалено сообщение {msg_id} из канала {CHANNEL_ID}")
                # Небольшая пауза, чтобы избежать ограничений API
                await asyncio.sleep(0.1)
            except TelegramError as e:
                logger.error(f"Не удалось удалить сообщение {msg_id}: {e}")
                failed_to_delete.append(msg_id)
    
    # Обновляем список всех сообщений, оставляя только те, которые не удалось удалить
    # и добавляем исключенное сообщение, если оно есть
    message_ids["all_messages"] = failed_to_delete
    if except_message_id is not None and except_message_id not in failed_to_delete:
        message_ids["all_messages"].append(except_message_id)
    
    # Сохраняем обновленный список
    save_message_ids(message_ids)
    
    return True