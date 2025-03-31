#!/usr/bin/env python
import os
import requests
import argparse
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

def setup_webhook(webhook_url=None):
    """
    Настраивает webhook для Telegram бота
    
    Args:
        webhook_url (str, optional): URL для webhook. 
            Если не указан, будет использоваться URL на основе VERCEL_URL из окружения.
    """
    # Получаем токен бота и webhook secret
    bot_token = os.getenv('TEST_TELEGRAM_BOT_TOKEN')
    webhook_secret = os.getenv('TEST_WEBHOOK_SECRET')
    
    if not bot_token:
        print("Ошибка: Токен бота не найден в переменных окружения")
        return
    
    if not webhook_secret:
        print("Предупреждение: Секрет webhook не найден. Это может привести к проблемам безопасности.")
    
    # Если URL не указан, создаем его на основе VERCEL_URL
    if not webhook_url:
        vercel_url = os.getenv('VERCEL_URL')
        if not vercel_url:
            print("Ошибка: URL не указан и VERCEL_URL не найден в переменных окружения")
            return
        webhook_url = f"https://{vercel_url}/webhook"
    
    # URL для установки webhook
    set_webhook_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    # Параметры запроса
    params = {
        'url': webhook_url,
        'secret_token': webhook_secret
    }
    
    # Отправляем запрос
    print(f"Устанавливаем webhook на {webhook_url}...")
    response = requests.post(set_webhook_url, json=params)
    
    # Проверяем ответ
    if response.status_code == 200 and response.json().get('ok'):
        print("Webhook успешно установлен!")
        print(f"Детали: {response.json()}")
    else:
        print(f"Ошибка установки webhook: {response.status_code}")
        print(f"Ответ: {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Настройка webhook для Telegram бота')
    parser.add_argument('--url', help='URL для webhook (включая протокол и путь)')
    
    args = parser.parse_args()
    setup_webhook(args.url) 