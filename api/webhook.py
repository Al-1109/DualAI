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

def send_message(chat_id, text, reply_markup=None):
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
        print(f"GET запрос на {self.path}")
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
        print(f"POST запрос на {self.path}")
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update = json.loads(post_data.decode('utf-8'))
            
            print(f"Получены данные: {json.dumps(update)}")
            
            # Готовим ответ на webhook
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {'status': 'ok'}
            self.wfile.write(json.dumps(response_data).encode())
            
            # После отправки ответа на webhook обрабатываем сообщение
            try:
                # Проверяем наличие сообщения с текстом
                if 'message' in update and 'text' in update['message']:
                    chat_id = update['message']['chat']['id']
                    message_text = update['message']['text']
                    user_name = update['message']['from'].get('first_name', 'пользователь')
                    
                    print(f"Сообщение от {user_name} ({chat_id}): {message_text}")
                    
                    # Обработка команды /start
                    if message_text == '/start':
                        reply_text = f"Привет, {user_name}! Я тестовый бот для проекта DualAI."
                        
                        # Создаем клавиатуру
                        keyboard = {
                            "inline_keyboard": [
                                [{"text": "Информация", "callback_data": "info"}],
                                [{"text": "Тест", "callback_data": "test"}]
                            ]
                        }
                        
                        # Отправляем сообщение с клавиатурой
                        send_result = send_message(chat_id, reply_text, keyboard)
                        print(f"Результат отправки: {json.dumps(send_result)}")
                    else:
                        # Эхо для других сообщений
                        reply_text = f"Вы сказали: {message_text}"
                        send_result = send_message(chat_id, reply_text)
                        print(f"Результат отправки: {json.dumps(send_result)}")
                
                # Обработка нажатий на кнопки
                elif 'callback_query' in update:
                    callback_query = update['callback_query']
                    chat_id = callback_query['message']['chat']['id']
                    data = callback_query['data']
                    
                    print(f"Callback query с данными: {data}")
                    
                    if data == 'info':
                        text = "Это тестовый бот для проекта DualAI на Vercel."
                    else:
                        text = "Тестовый ответ на callback."
                    
                    send_result = send_message(chat_id, text)
                    print(f"Результат отправки: {json.dumps(send_result)}")
            except Exception as e:
                print(f"Ошибка при обработке сообщения: {e}")
                traceback.print_exc()
            
            return
        except Exception as e:
            print(f"Общая ошибка обработки webhook: {e}")
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {'status': 'error', 'error': str(e)}
            self.wfile.write(json.dumps(response_data).encode())
            return 