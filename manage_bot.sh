#!/bin/bash

# Функция для получения PID бота
get_bot_pid() {
    pgrep -f "python.*bot.py" || echo ""
}

# Функция для запуска бота
start_bot() {
    if [ -n "$(get_bot_pid)" ]; then
        echo "Бот уже запущен"
        return 1
    fi
    
    echo "Запускаем бота..."
    python bot.py > bot.log 2>&1 &
    sleep 2
    
    if [ -n "$(get_bot_pid)" ]; then
        echo "Бот успешно запущен"
        return 0
    else
        echo "Ошибка запуска бота"
        return 1
    fi
}

# Функция для остановки бота
stop_bot() {
    local pid=$(get_bot_pid)
    if [ -z "$pid" ]; then
        echo "Бот не запущен"
        return 0
    fi
    
    echo "Останавливаем бота..."
    kill -15 $pid
    sleep 2
    
    if [ -n "$(get_bot_pid)" ]; then
        echo "Принудительная остановка бота..."
        kill -9 $pid
        sleep 1
    fi
    
    if [ -z "$(get_bot_pid)" ]; then
        echo "Бот остановлен"
        return 0
    else
        echo "Ошибка остановки бота"
        return 1
    fi
}

# Функция для перезапуска бота
restart_bot() {
    echo "Перезапуск бота..."
    stop_bot
    sleep 2
    start_bot
}

# Функция для просмотра статуса бота
status_bot() {
    local pid=$(get_bot_pid)
    if [ -n "$pid" ]; then
        echo "Бот запущен (PID: $pid)"
        echo "Последние логи:"
        tail -n 5 bot.log
    else
        echo "Бот не запущен"
    fi
}

# Обработка аргументов командной строки
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac 