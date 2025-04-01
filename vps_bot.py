import os
import sys
import logging
import traceback
import signal
from datetime import datetime
import time
import threading
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError, NetworkError, TimedOut

# Загружаем переменные окружения из .env файла
load_dotenv()

# Глобальные переменные
START_TIME = time.time()  # Время запуска бота
SHOULD_EXIT = False       # Флаг для корректного завершения работы

# Настройка логирования
LOG_FOLDER = "/var/log/dualai"
if not os.path.exists(LOG_FOLDER):
    try:
        os.makedirs(LOG_FOLDER)
    except PermissionError:
        LOG_FOLDER = "logs"  
        if not os.path.exists(LOG_FOLDER):
            os.makedirs(LOG_FOLDER)

LOG_FILE = os.path.join(LOG_FOLDER, f"bot_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
logger = logging.getLogger(__name__)

def setup_logging():
    """Настройка логирования с записью в файл и консоль."""
    logger.setLevel(logging.INFO)
    
    # Очистка существующих обработчиков
    logger.handlers = []
    
    # Создаем обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Создаем обработчик для записи в файл
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    
    # Создаем форматтер для логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Логирование настроено успешно. Лог-файл: {LOG_FILE}")
    logger.info(f"Версия VPS бота: 1.0.0 | Запущен на VPS с systemd")

# Статистика работы бота
STATS = {
    "start_time": datetime.now(),
    "messages_processed": 0,
    "callbacks_processed": 0,
    "errors_occurred": 0,
    "last_activity": datetime.now(),
    "active_users": set(),
    "last_connection_check": datetime.now(),
    "connection_errors": 0,
    "reconnection_attempts": 0
}

def get_bot_token():
    """Получение токена бота из переменных окружения."""
    token = os.environ.get("TEST_TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("Используется встроенный токен бота. Рекомендуется использовать переменную окружения TEST_TELEGRAM_BOT_TOKEN")
        token = "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"  # Fallback токен
    return token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    try:
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"Команда /start от пользователя {user.first_name} (ID: {user_id})")
        STATS["messages_processed"] += 1
        STATS["last_activity"] = datetime.now()
        STATS["active_users"].add(user_id)
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("📋 О боте", callback_data="info")],
            [InlineKeyboardButton("🛠️ Возможности", callback_data="features")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем приветственное сообщение
        message = await update.message.reply_text(
            f"# Добро пожаловать, {user.first_name}! 👋\n\n" +
            "Это главное меню DualAI бота.\n" +
            "Выберите интересующий вас раздел, нажав на соответствующую кнопку.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Сохраняем ID сообщения для возможного обновления в будущем
        context.user_data["last_menu_message_id"] = message.message_id
        
        logger.info(f"Отправлено приветственное сообщение пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}")
        logger.debug(traceback.format_exc())
        STATS["errors_occurred"] += 1
        if update.message:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    try:
        user = update.effective_user
        message_text = update.message.text
        
        logger.info(f"Сообщение от пользователя {user.first_name} (ID: {user.id}): {message_text}")
        STATS["messages_processed"] += 1
        STATS["last_activity"] = datetime.now()
        STATS["active_users"].add(user.id)
        
        # Проверяем, является ли сообщение командой
        if message_text.lower() == '/start' or message_text.lower() == '/menu':
            return await start(update, context)
        elif message_text.lower() == '/status':
            return await status_command(update, context)
        elif message_text.lower() == '/refresh':
            return await refresh_command(update, context)
        elif message_text.lower() == '/help':
            return await help_command(update, context)
        
        # Отправляем эхо
        await update.message.reply_text(f"Вы сказали: {message_text}")
        logger.info(f"Отправлен эхо-ответ пользователю {user.id}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике handle_message: {e}")
        logger.debug(traceback.format_exc())
        STATS["errors_occurred"] += 1
        if update.message:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    try:
        user = update.effective_user
        logger.info(f"Команда /help от пользователя {user.first_name} (ID: {user.id})")
        
        help_text = (
            "# Помощь ❓\n\n"
            "Доступные команды:\n"
            "`/start` - Запустить бота\n"
            "`/menu` - Показать главное меню\n"
            "`/status` - Показать статистику бота\n"
            "`/refresh` - Проверить соединение с Telegram\n"
            "`/help` - Показать эту справку\n\n"
            "Для навигации используйте кнопки внизу сообщений."
        )
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
        logger.info(f"Отправлена справка пользователю {user.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке справки: {e}")
        logger.debug(traceback.format_exc())
        STATS["errors_occurred"] += 1
        if update.message:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки."""
    try:
        query = update.callback_query
        user = query.from_user
        callback_data = query.data
        
        logger.info(f"Callback от пользователя {user.first_name} (ID: {user.id}): {callback_data}")
        STATS["callbacks_processed"] += 1
        STATS["last_activity"] = datetime.now()
        STATS["active_users"].add(user.id)
        
        # Сообщаем Telegram, что мы обработали запрос
        await query.answer()
        
        # Отправляем ответ в зависимости от нажатой кнопки
        if callback_data == "info":
            keyboard = [
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(
                "# О проекте DualAI 🚀\n\n" +
                "DualAI - это экспериментальный Telegram бот, разработанный для демонстрации возможностей VPS хостинга с long polling.\n\n" +
                "Версия: 1.0.0\n" +
                "Платформа: VPS + systemd\n" +
                "Технологии: Python, python-telegram-bot",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            logger.info(f"Отправлена информация о боте пользователю {user.id}")
        
        elif callback_data == "features":
            keyboard = [
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(
                "# Возможности бота 🛠️\n\n" +
                "- Стабильная работа через VPS\n" +
                "- Автоматический перезапуск через systemd\n" +
                "- Расширенное логирование\n" +
                "- Мониторинг состояния\n" +
                "- Сохранение статистики",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            logger.info(f"Отправлена информация о возможностях пользователю {user.id}")
        
        elif callback_data == "stats":
            # Расчет времени работы
            uptime = datetime.now() - STATS["start_time"]
            hours, remainder = divmod(uptime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="stats")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            stats_text = (
                "# Статистика 📊\n\n"
                f"⏱ Время работы: {int(hours)}ч {int(minutes)}м {int(seconds)}с\n"
                f"📨 Обработано сообщений: {STATS['messages_processed']}\n"
                f"🔄 Обработано callback: {STATS['callbacks_processed']}\n"
                f"⚠️ Ошибок: {STATS['errors_occurred']}\n"
                f"👥 Активных пользователей: {len(STATS['active_users'])}\n"
                f"🕒 Последняя активность: {STATS['last_activity'].strftime('%H:%M:%S')}\n"
                f"🔌 Попытки переподключения: {STATS['reconnection_attempts']}"
            )
            
            await query.message.edit_text(
                stats_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            logger.info(f"Отправлена статистика пользователю {user.id}")
        
        elif callback_data == "help":
            keyboard = [
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            help_text = (
                "# Помощь ❓\n\n"
                "Доступные команды:\n"
                "`/start` - Запустить бота\n"
                "`/menu` - Показать главное меню\n"
                "`/status` - Показать статистику бота\n"
                "`/refresh` - Проверить соединение с Telegram\n"
                "`/help` - Показать эту справку\n\n"
                "Для навигации используйте кнопки внизу сообщений."
            )
            
            await query.message.edit_text(
                help_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            logger.info(f"Отправлена справка пользователю {user.id}")
        
        elif callback_data == "menu":
            # Возвращаем главное меню
            keyboard = [
                [InlineKeyboardButton("📋 О боте", callback_data="info")],
                [InlineKeyboardButton("🛠️ Возможности", callback_data="features")],
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(
                f"# Добро пожаловать, {user.first_name}! 👋\n\n" +
                "Это главное меню DualAI бота.\n" +
                "Выберите интересующий вас раздел, нажав на соответствующую кнопку.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            logger.info(f"Пользователь {user.id} вернулся в главное меню")
    except Exception as e:
        logger.error(f"Ошибка в обработчике handle_callback: {str(e)}")
        logger.debug(traceback.format_exc())
        STATS["errors_occurred"] += 1
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    "Произошла ошибка при обработке запроса.\n"
                    "Пожалуйста, отправьте /start для перезапуска бота."
                )
        except:
            logger.error("Не удалось отправить сообщение об ошибке")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для проверки статуса бота"""
    try:
        user = update.effective_user
        logger.info(f"Команда /status от пользователя {user.first_name} (ID: {user.id})")
        
        # Расчет времени работы
        uptime = datetime.now() - STATS["start_time"]
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_text = (
            "# Статус бота 📊\n\n"
            f"⏱ Время работы: {int(hours)}ч {int(minutes)}м {int(seconds)}с\n"
            f"📨 Обработано сообщений: {STATS['messages_processed']}\n"
            f"🔄 Обработано callback: {STATS['callbacks_processed']}\n"
            f"⚠️ Ошибок: {STATS['errors_occurred']}\n"
            f"👥 Активных пользователей: {len(STATS['active_users'])}\n"
            f"🕒 Последняя активность: {STATS['last_activity'].strftime('%H:%M:%S')}\n"
            f"🔌 Попытки переподключения: {STATS['reconnection_attempts']}\n\n"
            f"🖥️ Лог-файл: {LOG_FILE}\n"
            f"🔧 Версия бота: 1.0.0 (VPS)"
        )
        
        await update.message.reply_text(status_text, parse_mode="Markdown")
        logger.info(f"Отправлен статус пользователю {user.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке статуса: {e}")
        logger.debug(traceback.format_exc())
        STATS["errors_occurred"] += 1
        if update.message:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для принудительного обновления соединения с Telegram"""
    try:
        user = update.effective_user
        logger.info(f"Команда /refresh от пользователя {user.first_name} (ID: {user.id})")
        
        await update.message.reply_text("🔄 Обновление соединения с серверами Telegram...")
        
        # Проверка соединения
        await context.bot.get_me()
        STATS["last_connection_check"] = datetime.now()
        
        await update.message.reply_text("✅ Соединение успешно обновлено! Бот работает нормально.")
        logger.info(f"Соединение обновлено по запросу пользователя {user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении соединения: {e}")
        logger.debug(traceback.format_exc())
        STATS["errors_occurred"] += 1
        STATS["connection_errors"] += 1
        if update.message:
            await update.message.reply_text("❌ Произошла ошибка при обновлении соединения. Пробую переподключиться...")
            try:
                # Повторная проверка
                await context.bot.get_me()
                await update.message.reply_text("✅ Переподключение успешно!")
            except:
                await update.message.reply_text("❌ Переподключение не удалось. Сообщите администратору.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    # Получаем информацию об ошибке
    error = context.error
    
    # Логируем ошибку
    logger.error(f"Ошибка при обработке обновления: {error}")
    logger.debug(traceback.format_exc())
    STATS["errors_occurred"] += 1
    
    # Обрабатываем разные типы ошибок
    if isinstance(error, NetworkError):
        logger.warning(f"Сетевая ошибка: {error}")
        STATS["connection_errors"] += 1
    elif isinstance(error, TimedOut):
        logger.warning(f"Таймаут соединения: {error}")
        STATS["connection_errors"] += 1
    else:
        logger.error(f"Необработанная ошибка: {error}")
    
    # Уведомляем пользователя, если возможно
    if update and hasattr(update, 'effective_chat'):
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Произошла ошибка при обработке вашего запроса. Попробуйте снова позже."
            )
        except:
            pass

async def periodic_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Задачи, выполняемые периодически"""
    try:
        # Проверяем соединение с Telegram API
        await check_connection_status(context)
        
        # Логируем статистику
        log_stats(context)
        
        # Проверяем флаг выхода
        if SHOULD_EXIT:
            logger.info("Получен сигнал завершения работы, останавливаю бота...")
            await context.application.stop()
            
    except Exception as e:
        logger.error(f"Ошибка в периодических задачах: {e}")
        logger.debug(traceback.format_exc())

async def check_connection_status(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет статус соединения с Telegram API"""
    try:
        # Проверяем соединение
        await context.bot.get_me()
        STATS["last_connection_check"] = datetime.now()
        logger.debug("Проверка соединения: OK")
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения: {e}")
        STATS["connection_errors"] += 1
        STATS["reconnection_attempts"] += 1

def log_stats(context):
    """Логирует текущую статистику"""
    uptime = datetime.now() - STATS["start_time"]
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    logger.info(
        f"Статистика бота: Uptime: {int(hours)}ч {int(minutes)}м, "
        f"Сообщений: {STATS['messages_processed']}, "
        f"Callback: {STATS['callbacks_processed']}, "
        f"Ошибок: {STATS['errors_occurred']}, "
        f"Активных пользователей: {len(STATS['active_users'])}, "
        f"Подключение: последняя проверка {STATS['last_connection_check'].strftime('%H:%M:%S')}, "
        f"ошибок: {STATS['connection_errors']}, "
        f"переподключений: {STATS['reconnection_attempts']}"
    )

def register_handlers(application):
    """Регистрирует обработчики команд и сообщений."""
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", start))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("refresh", refresh_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик нажатий на кнопки
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения бота"""
    global SHOULD_EXIT
    logger.info(f"Получен сигнал {sig}, инициирую завершение работы...")
    SHOULD_EXIT = True

def main():
    """Основная функция запуска бота."""
    try:
        # Настраиваем логирование
        setup_logging()
        
        # Настраиваем обработчики сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Получаем токен бота
        token = get_bot_token()
        if not token:
            logger.error("Не удалось получить токен бота. Завершаю работу.")
            return
        
        # Создаем экземпляр бота
        application = Application.builder().token(token).build()
        
        # Регистрируем обработчики
        register_handlers(application)
        
        # Добавляем периодические задачи
        job_queue = application.job_queue
        job_queue.run_repeating(periodic_tasks, interval=60, first=10)
        
        # Запускаем бота
        logger.info("Запускаю бота в режиме long polling...")
        application.run_polling(poll_interval=1.0, timeout=30, allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {str(e)}")
        logger.debug(traceback.format_exc())
        
    finally:
        logger.info("Бот завершил работу")

if __name__ == "__main__":
    main() 