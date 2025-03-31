#!/usr/bin/env python
import os
import requests
import argparse
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

def setup_webhook(webhook_url=None, webhook_secret=None):
    """
    Настраивает webhook для Telegram бота
    
    Args:
        webhook_url (str, optional): URL для webhook. 
            Если не указан, будет использоваться URL на основе VERCEL_URL из окружения.
        webhook_secret (str, optional): Секретный токен для верификации запросов.
            Если не указан, будет использоваться TEST_WEBHOOK_SECRET из окружения.
    """
    # Получаем токен бота и webhook secret из окружения
    bot_token = os.getenv('TEST_TELEGRAM_BOT_TOKEN')
    
    # Если webhook_secret не передан, используем из окружения
    if not webhook_secret:
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
        webhook_url = f"https://{vercel_url}/api/webhook"
    
    # URL для установки webhook
    set_webhook_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    # Параметры запроса
    params = {
        'url': webhook_url
    }
    
    # Добавляем secret_token, если он указан
    if webhook_secret:
        params['secret_token'] = webhook_secret
    
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

def get_webhook_info():
    """Получает информацию о текущем webhook."""
    bot_token = os.getenv('TEST_TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("Ошибка: Токен бота не найден в переменных окружения")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    print("Запрашиваем информацию о webhook...")
    response = requests.get(url)
    
    if response.status_code == 200 and response.json().get('ok'):
        print("Информация о webhook получена:")
        info = response.json().get('result', {})
        
        print(f"URL: {info.get('url', 'Не установлен')}")
        print(f"Ожидает обновлений: {info.get('pending_update_count', 0)}")
        print(f"Последняя ошибка: {info.get('last_error_message', 'Нет ошибок')}")
        print(f"Максимальные подключения: {info.get('max_connections', 'Не указано')}")
        print(f"IP-адрес: {info.get('ip_address', 'Не указан')}")
    else:
        print(f"Ошибка получения информации: {response.status_code}")
        print(f"Ответ: {response.text}")

def delete_webhook():
    """Удаляет текущий webhook."""
    bot_token = os.getenv('TEST_TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("Ошибка: Токен бота не найден в переменных окружения")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    print("Удаляем webhook...")
    response = requests.get(url)
    
    if response.status_code == 200 and response.json().get('ok'):
        print("Webhook успешно удален!")
    else:
        print(f"Ошибка удаления webhook: {response.status_code}")
        print(f"Ответ: {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Управление webhook для Telegram бота')
    
    # Создаем подпарсеры для разных команд
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # Подпарсер для установки webhook
    set_parser = subparsers.add_parser('set', help='Установить webhook')
    set_parser.add_argument('--url', help='URL для webhook (включая протокол и путь)')
    set_parser.add_argument('--secret', help='Секретный токен для верификации запросов')
    
    # Подпарсер для получения информации о webhook
    info_parser = subparsers.add_parser('info', help='Получить информацию о webhook')
    
    # Подпарсер для удаления webhook
    delete_parser = subparsers.add_parser('delete', help='Удалить webhook')
    
    args = parser.parse_args()
    
    if args.command == 'set':
        setup_webhook(args.url, args.secret)
    elif args.command == 'info':
        get_webhook_info()
    elif args.command == 'delete':
        delete_webhook()
    else:
        # По умолчанию выводим помощь
        parser.print_help() 