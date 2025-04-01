# Инструкция по установке DualAI бота на VPS

## Предварительные требования
- VPS с операционной системой Linux (Ubuntu/Debian рекомендуется)
- Python 3.8 или выше
- Права sudo для установки пакетов
- Доступ по SSH

## Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv git

# Создание пользователя для бота
sudo useradd -m -s /bin/bash dualai

# Создание директории для логов
sudo mkdir -p /var/log/dualai
sudo chown dualai:dualai /var/log/dualai
```

## Шаг 2: Установка бота

```bash
# Переключение на пользователя dualai
sudo su - dualai

# Клонирование репозитория
git clone https://github.com/Al-1109/DualAI.git
cd DualAI

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install python-telegram-bot python-dotenv

# Тестовый запуск бота
python vps_bot.py

# Нажмите Ctrl+C для остановки после проверки
exit
```

## Шаг 3: Настройка systemd сервиса

```bash
# Копирование файла сервиса
sudo cp /home/dualai/DualAI/dualai-bot.service /etc/systemd/system/

# Настройка токена бота и других переменных окружения (если нужно)
sudo nano /etc/systemd/system/dualai-bot.service

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение и запуск сервиса
sudo systemctl enable dualai-bot
sudo systemctl start dualai-bot
```

## Шаг 4: Мониторинг и управление

### Проверка статуса
```bash
sudo systemctl status dualai-bot
```

### Просмотр логов
```bash
# Логи systemd
sudo journalctl -u dualai-bot

# Логи приложения
sudo tail -f /var/log/dualai/bot*.log
```

### Перезапуск бота
```bash
sudo systemctl restart dualai-bot
```

### Остановка бота
```bash
sudo systemctl stop dualai-bot
```

## Шаг 5: Обновление бота

```bash
# Переключение на пользователя dualai
sudo su - dualai
cd DualAI

# Получение последних изменений
git pull

# Активация виртуального окружения и обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Выход из пользователя dualai
exit

# Перезапуск сервиса
sudo systemctl restart dualai-bot
```

## Важные замечания

1. **Безопасность токена**: 
   - Никогда не публикуйте токен бота в открытом доступе
   - Храните токен в переменных окружения или .env файле

2. **Мониторинг работы**:
   - Настройте мониторинг для отслеживания работы бота
   - Можно использовать инструменты вроде Monit или Zabbix

3. **Резервное копирование**:
   - Регулярно создавайте резервные копии данных бота
   - Храните бэкапы в безопасном месте

4. **Ограничение ресурсов**:
   - В файле systemd сервиса настроены ограничения по памяти и CPU
   - При необходимости измените их под ваши потребности

## Решение проблем

### Бот не запускается
1. Проверьте статус сервиса: `sudo systemctl status dualai-bot`
2. Проверьте логи: `sudo journalctl -u dualai-bot`
3. Проверьте права доступа: `ls -la /home/dualai/DualAI`
4. Проверьте конфигурацию systemd: `cat /etc/systemd/system/dualai-bot.service`

### Проблемы с подключением к Telegram API
1. Проверьте доступность API: `curl https://api.telegram.org`
2. Проверьте правильность токена в переменных окружения
3. Проверьте логи бота на наличие ошибок сети

### Высокое потребление ресурсов
1. Проверьте нагрузку: `top` или `htop`
2. Настройте ограничения в файле systemd сервиса
3. Оптимизируйте код бота 