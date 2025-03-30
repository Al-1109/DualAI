# This file makes the utils directory a Python package 

import os
import json
from typing import Dict, List, Optional

# Константы
CHANNEL_ID = "@MirasolEstate"

def load_message_ids() -> Dict:
    """Загружает сохраненные ID сообщений."""
    try:
        with open("message_ids.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"all_messages": []}

def save_message_ids(message_ids: Dict) -> None:
    """Сохраняет ID сообщений."""
    with open("message_ids.json", "w") as f:
        json.dump(message_ids, f)

def load_content_file(file_path: str) -> str:
    """Загружает содержимое файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Content file not found: {file_path}"

async def send_to_channel(bot, message: str) -> Optional[int]:
    """Отправляет сообщение в канал."""
    try:
        sent_message = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="Markdown"
        )
        return sent_message.message_id
    except Exception as e:
        print(f"Error sending message to channel: {e}")
        return None

async def clean_all_channel_messages(bot) -> None:
    """Удаляет все сообщения из канала."""
    message_ids = load_message_ids()
    for msg_id in message_ids.get("all_messages", []):
        try:
            await bot.delete_message(chat_id=CHANNEL_ID, message_id=msg_id)
        except Exception as e:
            print(f"Error deleting message {msg_id}: {e}")
    save_message_ids({"all_messages": []})

async def send_photo_to_channel(bot, photo_path: str, caption: str = "") -> Optional[int]:
    """Отправляет фото в канал."""
    try:
        with open(photo_path, "rb") as photo:
            sent_message = await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo,
                caption=caption,
                parse_mode="Markdown"
            )
            return sent_message.message_id
    except Exception as e:
        print(f"Error sending photo to channel: {e}")
        return None 