import os
import sys
import time
import subprocess
import logging
from datetime import datetime

# Настройка логирования
LOG_FOLDER = "logs"
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

# Файл для логов
LOG_FILE = os.path.join(LOG_FOLDER, f"runner_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("BotRunner")

# Путь к интерпретатору Python
PYTHON_PATH = sys.executable  # Использует текущий интерпретатор Python

# Путь к файлу бота
BOT_SCRIPT = "vps_bot.py"

def main():
    """Основная функция запуска и мониторинга бота."""
    logger.info("Запуск системы мониторинга бота на Windows VPS")
    
    # Обеспечиваем наличие файла бота
    if not os.path.exists(BOT_SCRIPT):
        logger.error(f"Файл бота {BOT_SCRIPT} не найден! Завершаю работу.")
        return
    
    restart_count = 0
    max_restarts = 50  # Максимальное число перезапусков
    
    while restart_count < max_restarts:
        start_time = time.time()
        logger.info(f"Запуск бота (попытка {restart_count + 1}/{max_restarts})...")
        
        try:
            # Запускаем процесс бота
            process = subprocess.Popen(
                [PYTHON_PATH, BOT_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE  # Для Windows
            )
            
            logger.info(f"Бот запущен с PID: {process.pid}")
            
            # Ожидаем завершения процесса
            return_code = process.wait()
            
            # Проверяем, нормально ли завершился процесс
            if return_code == 0:
                logger.info("Бот завершил работу с кодом 0 (нормальное завершение)")
                break
            else:
                # Получаем ошибку из stderr
                _, stderr = process.communicate()
                logger.error(f"Бот завершил работу с ошибкой (код {return_code}): {stderr}")
                
                # Определяем время работы
                runtime = time.time() - start_time
                
                # Если бот проработал меньше минуты, увеличиваем паузу перед перезапуском
                if runtime < 60:
                    logger.warning(f"Бот проработал всего {runtime:.1f} секунд! Ожидаю 60 секунд перед перезапуском...")
                    time.sleep(60)
                else:
                    logger.info(f"Бот проработал {runtime:.1f} секунд")
                    time.sleep(5)  # Короткая пауза перед перезапуском
                
                restart_count += 1
        
        except Exception as e:
            logger.error(f"Ошибка при запуске/мониторинге бота: {e}")
            time.sleep(10)  # Пауза перед следующей попыткой
            restart_count += 1
    
    if restart_count >= max_restarts:
        logger.critical(f"Достигнуто максимальное число перезапусков ({max_restarts}). Завершаю работу.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Получено прерывание от пользователя (Ctrl+C). Завершаю работу.")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        logger.info("Система мониторинга завершила работу.") 