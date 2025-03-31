#!/usr/bin/env python
"""
Скрипт-обертка для мониторинга и поддержания работы Telegram бота.
Автоматически перезапускает бота при его зависании или сбое.
"""
import os
import sys
import time
import subprocess
import logging
import signal
import datetime
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"watchdog_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("watchdog")

# Константы
BOT_COMMAND = ["python", "test_bot.py"]
BOT_TOKEN = os.environ.get("TEST_TELEGRAM_BOT_TOKEN") or "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"
CHECK_INTERVAL = 30  # Проверяем состояние бота каждые 30 секунд
MAX_INACTIVITY = 120  # Максимальное время без активности (в секундах)
RESTART_DELAY = 5  # Задержка перед перезапуском (в секундах)

class BotWatchdog:
    """Класс для мониторинга и перезапуска Telegram бота."""
    
    def __init__(self):
        """Инициализация watchdog."""
        self.bot_process = None
        self.last_activity_time = time.time()
        self.start_count = 0
        self.restart_required = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов для корректного завершения."""
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
    
    def handle_exit(self, signum, frame):
        """Корректное завершение при получении сигнала."""
        logger.info(f"Получен сигнал {signum}. Завершение работы watchdog...")
        self.stop_bot()
        sys.exit(0)
    
    def start_bot(self):
        """Запуск бота как отдельного процесса."""
        if self.bot_process and self.bot_process.poll() is None:
            logger.warning("Бот уже запущен. Остановка текущего процесса...")
            self.stop_bot()
        
        # Устанавливаем переменную окружения для токена бота
        env = os.environ.copy()
        env["TEST_TELEGRAM_BOT_TOKEN"] = BOT_TOKEN
        
        try:
            logger.info("Запуск бота...")
            self.start_count += 1
            self.bot_process = subprocess.Popen(
                BOT_COMMAND,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            logger.info(f"Бот запущен (PID: {self.bot_process.pid}, запуск #{self.start_count})")
            self.last_activity_time = time.time()
            self.restart_required = False
            
            # Запускаем асинхронное чтение вывода бота
            self.start_output_monitoring()
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            return False
        
        return True
    
    def start_output_monitoring(self):
        """Запускает мониторинг вывода бота в отдельном потоке."""
        from threading import Thread
        
        def read_output():
            """Чтение вывода бота и запись в лог."""
            while self.bot_process and self.bot_process.poll() is None:
                try:
                    line = self.bot_process.stdout.readline()
                    if line:
                        logger.debug(f"BOT: {line.strip()}")
                        self.last_activity_time = time.time()  # Обновляем время активности
                except Exception as e:
                    logger.error(f"Ошибка при чтении вывода бота: {e}")
                    break
        
        # Запускаем мониторинг вывода
        Thread(target=read_output, daemon=True).start()
    
    def stop_bot(self):
        """Остановка процесса бота."""
        if not self.bot_process:
            logger.warning("Нет запущенного процесса бота для остановки")
            return
        
        try:
            if self.bot_process.poll() is None:  # Если процесс еще работает
                logger.info(f"Остановка бота (PID: {self.bot_process.pid})...")
                
                # Сначала пробуем корректно завершить процесс
                self.bot_process.terminate()
                
                # Даем процессу 5 секунд на завершение
                for _ in range(5):
                    if self.bot_process.poll() is not None:
                        break
                    time.sleep(1)
                
                # Если процесс еще работает, убиваем его
                if self.bot_process.poll() is None:
                    logger.warning("Бот не ответил на сигнал terminate, принудительное завершение...")
                    self.bot_process.kill()
                
                logger.info("Бот остановлен")
            else:
                logger.info("Процесс бота уже завершен")
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}")
        
        self.bot_process = None
    
    def check_bot_health(self):
        """Проверка состояния бота."""
        # Проверяем, запущен ли процесс
        if not self.bot_process or self.bot_process.poll() is not None:
            logger.warning("Процесс бота не запущен или завершился")
            return False
        
        # Проверяем время с последней активности
        current_time = time.time()
        inactivity_time = current_time - self.last_activity_time
        
        if inactivity_time > MAX_INACTIVITY:
            logger.warning(f"Бот неактивен в течение {inactivity_time:.1f} секунд (больше порога {MAX_INACTIVITY})")
            return False
        
        # Проверяем доступность Telegram API (проверка внешнего соединения)
        try:
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Telegram API недоступен: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Ошибка при проверке Telegram API: {e}")
            # Не считаем это критической ошибкой, так как может быть временная проблема с сетью
        
        logger.info(f"Бот работает нормально. Время с последней активности: {inactivity_time:.1f} сек.")
        return True
    
    def ping_bot(self):
        """Отправка запроса боту для проверки активности."""
        try:
            # Отправляем запрос к Telegram API, чтобы убедиться, что бот отвечает
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                logger.info("Успешный пинг бота через API")
                self.last_activity_time = time.time()  # Обновляем время активности
                return True
            else:
                logger.warning(f"Неуспешный пинг бота: код {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Ошибка при пинге бота: {e}")
            return False
    
    def run(self):
        """Основной цикл работы watchdog."""
        logger.info("Watchdog запущен")
        self.start_bot()
        
        try:
            while True:
                # Проверяем состояние бота
                if not self.check_bot_health() or self.restart_required:
                    logger.warning("Обнаружены проблемы с ботом. Перезапуск...")
                    self.stop_bot()
                    time.sleep(RESTART_DELAY)
                    self.start_bot()
                
                # Периодический пинг бота для поддержания активности
                if time.time() - self.last_activity_time > CHECK_INTERVAL // 2:
                    self.ping_bot()
                
                # Пауза перед следующей проверкой
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Watchdog остановлен пользователем")
        except Exception as e:
            logger.error(f"Неожиданная ошибка в watchdog: {e}")
        finally:
            self.stop_bot()
            logger.info("Watchdog завершил работу")


if __name__ == "__main__":
    try:
        # Проверяем наличие файла бота
        if not os.path.exists(BOT_COMMAND[1]):
            logger.error(f"Файл бота {BOT_COMMAND[1]} не найден")
            sys.exit(1)
        
        # Запускаем watchdog
        watchdog = BotWatchdog()
        watchdog.run()
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        sys.exit(1) 