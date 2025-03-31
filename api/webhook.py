from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import traceback
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("webhook")

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.environ.get('TEST_TELEGRAM_BOT_TOKEN')
WEBHOOK_SECRET = os.environ.get('TEST_WEBHOOK_SECRET')

if not TELEGRAM_BOT_TOKEN:
    logger.warning("Токен бота не найден в переменных окружения, использую fallback токен")
    TELEGRAM_BOT_TOKEN = "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"  # Fallback токен

# Проверяем наличие webhook secret
if not WEBHOOK_SECRET:
    logger.warning("WEBHOOK_SECRET не найден. Верификация запросов будет отключена.")

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
        logger.info(f"Отправка сообщения на {chat_id}: {text[:50]}...")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            logger.info(f"Сообщение успешно отправлено, chat_id: {chat_id}")
            return {"ok": True, "response": response.json()}
        else:
            logger.error(f"Ошибка API при отправке: {response.status_code}, {response.text}")
            return {"ok": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Исключение при отправке сообщения: {e}")
        logger.debug(traceback.format_exc())
        return {"ok": False, "error": str(e)}

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        """Устанавливает заголовки ответа."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
    
    def _send_json_response(self, data):
        """Отправляет JSON-ответ."""
        self.wfile.write(json.dumps(data).encode())
    
    def _verify_telegram_webhook(self):
        """Проверяет подлинность запроса от Telegram."""
        if not WEBHOOK_SECRET:
            logger.warning("Верификация пропущена: WEBHOOK_SECRET не настроен")
            return True
            
        secret_header = self.headers.get('X-Telegram-Bot-Api-Secret-Token')
        
        if not secret_header:
            logger.warning("Запрос не содержит заголовка X-Telegram-Bot-Api-Secret-Token")
            return False
            
        return secret_header == WEBHOOK_SECRET
    
    def do_GET(self):
        """Обработка GET-запроса - проверка работоспособности."""
        self._set_headers()
        
        response_data = {
            'status': 'ok',
            'message': 'Webhook активен',
            'timestamp': str(datetime.now()),
            'version': '1.1.0'
        }
        
        self._send_json_response(response_data)
    
    def do_POST(self):
        """Обработка POST-запроса от Telegram."""
        try:
            # Верификация запроса
            if not self._verify_telegram_webhook():
                logger.warning("Получен неверифицированный запрос")
                self._set_headers(403)
                self._send_json_response({'ok': False, 'error': 'Forbidden'})
                return
                
            # Чтение данных запроса
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Сразу отвечаем Telegram, что получили сообщение
            self._set_headers()
            self._send_json_response({'ok': True})
            
            # Теперь обрабатываем сообщение
            update = json.loads(post_data.decode('utf-8'))
            logger.info(f"Получено обновление ID: {update.get('update_id')}")
            logger.debug(f"Содержимое: {json.dumps(update)}")
            
            # Обработка текстовых сообщений
            if 'message' in update and 'text' in update['message']:
                chat_id = update['message']['chat']['id']
                text = update['message']['text']
                user = update['message']['from'].get('first_name', 'пользователь')
                
                logger.info(f"Сообщение от {user} ({chat_id}): {text}")
                
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
                        f"👋 Привет, {user}!\n\nЯ тестовый бот для проекта DualAI на Vercel.\nЯ использую webhook-подход.",
                        keyboard
                    )
                else:
                    # Отправляем эхо
                    send_telegram_message(chat_id, f"Вы сказали: {text}")
            
            # Обработка нажатий на кнопки
            elif 'callback_query' in update:
                callback = update['callback_query']
                chat_id = callback['message']['chat']['id']
                data = callback['data']
                
                logger.info(f"Получен callback с данными: {data}")
                
                if data == 'info':
                    send_telegram_message(chat_id, "Это тестовый бот для проекта DualAI на Vercel через webhook.")
                elif data == 'test':
                    send_telegram_message(chat_id, "Тестовое сообщение. Webhook работает!")
                else:
                    send_telegram_message(chat_id, f"Получена команда: {data}")
            
            return
        
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            logger.debug(traceback.format_exc())
            
            # Отправляем ответ с ошибкой
            self._set_headers(500)
            self._send_json_response({'ok': False, 'error': str(e)})
            return 