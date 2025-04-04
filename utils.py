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
    """Усовершенствованная функция для отправки сообщений без мерцания."""
    message_ids = load_message_ids()
    existing_message_id = message_ids.get(message_key)
    
    try:
        # Сначала отправляем новое сообщение, только потом удаляем старое
        message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_notification=True  # Отключаем уведомления
        )
        
        # Сохраняем ID нового сообщения
        message_ids[message_key] = message.message_id
        
        # Также добавляем ID в список всех сообщений
        if "all_messages" not in message_ids:
            message_ids["all_messages"] = []
        
        if message.message_id not in message_ids["all_messages"]:
            message_ids["all_messages"].append(message.message_id)
        
        # Удаляем старое сообщение только после отправки нового
        if existing_message_id and existing_message_id != message.message_id:
            try:
                await context.bot.delete_message(
                    chat_id=CHANNEL_ID,
                    message_id=existing_message_id
                )
                
                # Удаляем ID старого сообщения из списка
                if existing_message_id in message_ids["all_messages"]:
                    message_ids["all_messages"].remove(existing_message_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении старого сообщения: {e}")
        
        # Сохраняем обновленный список ID
        save_message_ids(message_ids)
        
        logger.info(f"Сообщение {message_key} (ID: {message.message_id}) отправлено в канал {CHANNEL_ID}")
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
    
    # Путь к приветственному изображению
    welcome_image_path = "media/images/photo.jpg"
    
    try:
        # Пробуем отправить с фото
        with open(welcome_image_path, "rb") as photo_file:
            message = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_file,
                caption=welcome_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке фото: {e}")
        # В случае ошибки отправляем текст
        message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=welcome_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
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
    Теперь работает без мерцания и промежуточных сообщений.
    
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
        
        # Копируем список, чтобы избежать изменения списка во время итерации
        messages_to_delete = all_messages.copy()
        
        # Удаляем except_message_id из списка для удаления, если он указан
        if except_message_id is not None and except_message_id in messages_to_delete:
            messages_to_delete.remove(except_message_id)
        
        # Удаляем сообщения из копии списка
        for msg_id in messages_to_delete:
            try:
                await context.bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
                logger.info(f"Удалено сообщение {msg_id} из канала {CHANNEL_ID}")
                # Небольшая пауза, чтобы избежать ограничений API
                await asyncio.sleep(0.1)
            except TelegramError as e:
                logger.error(f"Не удалось удалить сообщение {msg_id}: {e}")
                failed_to_delete.append(msg_id)
        
        # Обновляем список всех сообщений
        # Оставляем исключенное сообщение и те, которые не удалось удалить
        message_ids["all_messages"] = failed_to_delete
        if except_message_id is not None and except_message_id not in failed_to_delete:
            message_ids["all_messages"].append(except_message_id)
        
        # Если какие-то ключи остались от предыдущих подменю, удаляем их
        keys_to_keep = ["welcome_message", "all_messages"]
        if except_message_id is not None:
            for key, value in message_ids.items():
                if value == except_message_id:
                    keys_to_keep.append(key)
        
        # Очищаем ненужные ключи
        for key in list(message_ids.keys()):
            if key not in keys_to_keep and message_ids.get(key) not in message_ids["all_messages"]:
                del message_ids[key]
        
        # Сохраняем обновленный список
        save_message_ids(message_ids)
        
        return len(messages_to_delete) - len(failed_to_delete) > 0
    else:
        logger.info("Нет дополнительных сообщений для удаления")
        return False

async def send_photo_to_channel(context, photo_path, caption=None, reply_markup=None, message_key="photo_message"):
    """Улучшенная функция для отправки фото без мерцания."""
    message_ids = load_message_ids()
    existing_message_id = message_ids.get(message_key)
    
    try:
        # Сначала отправляем новое сообщение с фото
        with open(photo_path, "rb") as photo_file:
            message = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_file,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown",
                disable_notification=True  # Важно: отключаем уведомления
            )
        
        # Сохраняем ID нового сообщения
        message_ids[message_key] = message.message_id
        
        # Добавляем ID в список всех сообщений
        if "all_messages" not in message_ids:
            message_ids["all_messages"] = []
        
        if message.message_id not in message_ids["all_messages"]:
            message_ids["all_messages"].append(message.message_id)
        
        # Теперь, когда новое сообщение отправлено, удаляем старое
        if existing_message_id and existing_message_id != message.message_id:
            try:
                await context.bot.delete_message(
                    chat_id=CHANNEL_ID,
                    message_id=existing_message_id
                )
                
                # Удаляем ID из списка всех сообщений
                if existing_message_id in message_ids["all_messages"]:
                    message_ids["all_messages"].remove(existing_message_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении старого сообщения с фото: {e}")
        
        # Сохраняем обновленный список ID
        save_message_ids(message_ids)
        
        logger.info(f"Отправлено новое сообщение с фото {message_key} (ID: {message.message_id})")
        return message
    except Exception as e:
        logger.error(f"Ошибка отправки фото в канал: {e}")
        # В случае ошибки пытаемся отправить обычное текстовое сообщение
        return await send_to_channel(context, caption, reply_markup, message_key)