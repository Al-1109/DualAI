from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TEST_TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    TELEGRAM_BOT_TOKEN = "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"  # Fallback токен из .env

# Базовый URL для Telegram API
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    """Отправляет сообщение пользователю через Telegram API."""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        print(f"API Response: {json.dumps(result)}")
        return result
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return {"ok": False, "error": str(e)}

def process_update(update):
    """Обрабатывает обновление от Telegram."""
    print(f"Processing update: {json.dumps(update)}")
    
    # Обработка сообщения
    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        message_text = update['message']['text']
        user_name = update['message']['from'].get('first_name', 'пользователь')
        
        # Логирование сообщения
        print(f"Получено сообщение от {user_name} (ID: {chat_id}): {message_text}")
        
        # Формируем ответ в зависимости от полученного сообщения
        if message_text == '/start':
            reply_text = f"Привет, {user_name}! Я тестовый бот для проекта DualAI. Рад приветствовать тебя!"
            
            # Создаем клавиатуру с кнопками
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "Информация о боте", "callback_data": "info"}
                    ],
                    [
                        {"text": "Тестовое сообщение", "callback_data": "test_message"}
                    ]
                ]
            }
            
            # Отправляем ответ с клавиатурой
            return send_message(chat_id, reply_text, keyboard)
        else:
            # Для всех остальных сообщений просто отправляем эхо
            reply_text = f"Вы сказали: {message_text}\n\nЭто тестовый ответ от DualAI webhook на Vercel."
            return send_message(chat_id, reply_text)
    
    # Обработка callback запросов (нажатия на inline кнопки)
    elif 'callback_query' in update:
        callback_id = update['callback_query']['id']
        chat_id = update['callback_query']['message']['chat']['id']
        callback_data = update['callback_query']['data']
        user_name = update['callback_query']['from'].get('first_name', 'пользователь')
        
        # Логирование callback
        print(f"Получен callback от {user_name} (ID: {chat_id}): {callback_data}")
        
        # Отвечаем в зависимости от callback_data
        if callback_data == 'info':
            reply_text = "Это тестовый бот для проекта DualAI, размещенный на Vercel с использованием webhook."
            return send_message(chat_id, reply_text)
        elif callback_data == 'test_message':
            reply_text = "Это тестовое сообщение. Webhook успешно работает!"
            return send_message(chat_id, reply_text)
    
    return {"ok": True, "message": "No action taken"}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_data = {
            'status': 'ok',
            'message': 'Telegram webhook is active',
            'timestamp': str(datetime.now()),
            'bot_token_exists': bool(TELEGRAM_BOT_TOKEN)
        }
        
        self.wfile.write(json.dumps(response_data).encode())
        return
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Парсим JSON данные от Telegram
            update = json.loads(post_data.decode('utf-8'))
            
            # Логирование полученного обновления
            print(f"Получено обновление: {json.dumps(update)}")
            
            # Обрабатываем обновление
            result = process_update(update)
            
            # Отправляем HTTP ответ на webhook запрос
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {
                'status': 'ok',
                'message': 'Webhook обработан успешно',
                'result': result
            }
            
            self.wfile.write(json.dumps(response_data).encode())
            return
        except Exception as e:
            # В случае ошибки отправляем 500 и информацию об ошибке
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {
                'status': 'error',
                'message': f'Ошибка обработки webhook: {str(e)}'
            }
            
            self.wfile.write(json.dumps(response_data).encode())
            return 