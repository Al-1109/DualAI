import os
import json
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Файл для хранения ID сообщений
MESSAGE_IDS_FILE = "data/channel_messages.json"

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