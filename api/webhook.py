from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import traceback
from datetime import datetime

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.environ.get('TEST_TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    TELEGRAM_BOT_TOKEN = "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"  # Fallback токен

# Базовый URL для Telegram API
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram_message(chat_id, text, reply_markup=None):
    """Отправляет сообщение пользователю через Telegram API."""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        print(f"Отправка сообщения на {chat_id}: {text}")
        response = requests.post(url, json=payload)
        print(f"Ответ API: {response.text}")
        return {"ok": True, "response": response.text}
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_data = {
            'status': 'ok',
            'message': 'Webhook активен',
            'timestamp': str(datetime.now())
        }
        
        self.wfile.write(json.dumps(response_data).encode())
        return
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Сразу отвечаем Telegram, что получили сообщение
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())
            
            # Теперь обрабатываем сообщение
            update = json.loads(post_data.decode('utf-8'))
            print(f"Получено обновление: {json.dumps(update)}")
            
            if 'message' in update and 'text' in update['message']:
                chat_id = update['message']['chat']['id']
                text = update['message']['text']
                user = update['message']['from'].get('first_name', 'пользователь')
                
                print(f"Сообщение от {user} ({chat_id}): {text}")
                
                if text == '/start':
                    # Создаем клавиатуру с кнопками
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "О боте", "callback_data": "info"}],
                            [{"text": "Тест", "callback_data": "test"}]
                        ]
                    }
                    
                    # Отправляем приветствие
                    send_telegram_message(
                        chat_id, 
                        f"👋 Привет, {user}!\n\nЯ тестовый бот для проекта DualAI.",
                        keyboard
                    )
                else:
                    # Отправляем эхо
                    send_telegram_message(chat_id, f"Вы сказали: {text}")
            
            # Обрабатываем нажатия на кнопки
            elif 'callback_query' in update:
                callback = update['callback_query']
                chat_id = callback['message']['chat']['id']
                data = callback['data']
                
                print(f"Получен callback с данными: {data}")
                
                if data == 'info':
                    send_telegram_message(chat_id, "Это тестовый бот для проекта DualAI на Vercel.")
                else:
                    send_telegram_message(chat_id, "Тестовое сообщение. Webhook работает!")
            
            return
        
        except Exception as e:
            print(f"Ошибка обработки webhook: {e}")
            traceback.print_exc()
            return 