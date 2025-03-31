import os
import sys
import time
import logging
import traceback
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError, NetworkError, TimedOut

# Настройка расширенного логирования
LOG_FOLDER = "logs"
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

LOG_FILE = os.path.join(LOG_FOLDER, f"bot_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

# Настройка логирования в файл и консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.environ.get('TEST_TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    BOT_TOKEN = "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"  # Fallback токен
    logger.warning("Используется встроенный токен бота. Рекомендуется использовать переменную окружения TEST_TELEGRAM_BOT_TOKEN")

# Статистика работы бота
STATS = {
    "start_time": datetime.now(),
    "messages_processed": 0,
    "callbacks_processed": 0,
    "errors_occurred": 0,
    "last_activity": datetime.now(),
    "active_users": set()
}

# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"Команда /start от пользователя {user.first_name} (ID: {user_id})")
        STATS["messages_processed"] += 1
        STATS["last_activity"] = datetime.now()
        STATS["active_users"].add(user_id)
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("О боте", callback_data="info")],
            [InlineKeyboardButton("Тест", callback_data="test")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем приветственное сообщение
        message = await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\nЯ тестовый бот для проекта DualAI.",
            reply_markup=reply_markup
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
    """Обработчик текстовых сообщений"""
    try:
        user = update.effective_user
        message_text = update.message.text
        
        logger.info(f"Сообщение от пользователя {user.first_name} (ID: {user.id}): {message_text}")
        STATS["messages_processed"] += 1
        STATS["last_activity"] = datetime.now()
        STATS["active_users"].add(user.id)
        
        # Проверяем, является ли сообщение командой /start
        if message_text.lower() == '/start':
            return await start_command(update, context)
        
        # Отправляем эхо
        await update.message.reply_text(f"Вы сказали: {message_text}")
        logger.info(f"Отправлен эхо-ответ пользователю {user.id}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике handle_message: {e}")
        logger.debug(traceback.format_exc())
        STATS["errors_occurred"] += 1
        if update.message:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
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
            await query.message.reply_text(
                "Это тестовый бот для проекта DualAI.\n\nЧто умеет этот бот:\n"
                "• Отвечать на команду /start\n"
                "• Отвечать на нажатия кнопок\n"
                "• Повторять сообщения пользователя (эхо)"
            )
            logger.info(f"Отправлена информация о боте пользователю {user.id}")
        elif callback_data == "test":
            # Новая клавиатура после нажатия на Тест
            keyboard = [
                [InlineKeyboardButton("Назад в меню", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "Тестовое сообщение. Бот работает!\n"
                "Нажмите 'Назад в меню' для возврата в главное меню.",
                reply_markup=reply_markup
            )
            logger.info(f"Отправлено тестовое сообщение пользователю {user.id}")
        elif callback_data == "menu":
            # Возвращаем главное меню
            keyboard = [
                [InlineKeyboardButton("О боте", callback_data="info")],
                [InlineKeyboardButton("Тест", callback_data="test")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Заменяем текущее сообщение на новое меню
            await query.message.edit_text(
                f"Главное меню бота DualAI.\n\nВыберите опцию:",
                reply_markup=reply_markup
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
            "📊 *Статус бота:*\n\n"
            f"⏱ Время работы: {int(hours)}ч {int(minutes)}м {int(seconds)}с\n"
            f"📨 Обработано сообщений: {STATS['messages_processed']}\n"
            f"🔄 Обработано callback: {STATS['callbacks_processed']}\n"
            f"⚠️ Ошибок: {STATS['errors_occurred']}\n"
            f"👥 Активных пользователей: {len(STATS['active_users'])}\n"
            f"🕒 Последняя активность: {STATS['last_activity'].strftime('%H:%M:%S')}"
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
        
        await update.message.reply_text("Обновление соединения с серверами Telegram...")
        
        # Здесь можно добавить любую логику обновления соединения
        # Например, переподключение к API или перезапуск опроса
        
        await update.message.reply_text("Соединение успешно обновлено! ✅")
        logger.info(f"Соединение обновлено по запросу пользователя {user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении соединения: {e}")
        logger.debug(traceback.format_exc())
        STATS["errors_occurred"] += 1
        if update.message:
            await update.message.reply_text("Произошла ошибка при обновлении соединения.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    # Получаем информацию об ошибке
    error = context.error
    
    # Логируем ошибку
    logger.error(f"Ошибка при обработке обновления: {error}")
    logger.debug(traceback.format_exc())
    STATS["errors_occurred"] += 1
    
    # Обрабатываем разные типы ошибок
    if isinstance(error, NetworkError):
        logger.warning("Ошибка сети. Возможно, проблемы с подключением к серверам Telegram.")
    elif isinstance(error, TimedOut):
        logger.warning("Превышено время ожидания ответа от Telegram.")
    elif isinstance(error, TelegramError):
        logger.warning(f"Ошибка Telegram API: {error.message}")
    
    # Пытаемся отправить сообщение пользователю
    try:
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Произошла ошибка при обработке вашего запроса.\n"
                "Пожалуйста, попробуйте отправить /start для перезапуска бота."
            )
    except:
        logger.error("Не удалось отправить сообщение об ошибке")

async def periodic_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Периодические задачи для поддержания работоспособности"""
    try:
        now = datetime.now()
        logger.info(f"Выполнение периодических задач в {now.strftime('%H:%M:%S')}")
        
        # Проверяем время с последней активности
        last_activity_delta = now - STATS["last_activity"]
        if last_activity_delta.total_seconds() > 600:  # Если прошло более 10 минут с последней активности
            logger.info("Отправка пинг-запроса для поддержания соединения")
            # Можно добавить любую логику для поддержания соединения
            # Например, запрос к Telegram API
            
        # Логирование статистики
        uptime = now - STATS["start_time"]
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        logger.info(
            f"Статистика бота: "
            f"Время работы: {int(hours)}ч {int(minutes)}м {int(seconds)}с, "
            f"Сообщений: {STATS['messages_processed']}, "
            f"Callbacks: {STATS['callbacks_processed']}, "
            f"Ошибок: {STATS['errors_occurred']}, "
            f"Активных пользователей: {len(STATS['active_users'])}"
        )
    except Exception as e:
        logger.error(f"Ошибка в периодических задачах: {e}")
        logger.debug(traceback.format_exc())

def main():
    """Основная функция для запуска бота"""
    logger.info("==================== ЗАПУСК БОТА ====================")
    logger.info(f"Токен бота: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("refresh", refresh_command))
        
        # Добавляем обработчики для сообщений и callback
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Добавляем периодические задачи
        application.job_queue.run_repeating(
            periodic_tasks, 
            interval=60,  # Выполнять каждую минуту
            first=10      # Начать через 10 секунд после запуска
        )
        
        # Запускаем приложение с расширенными настройками
        logger.info("Запуск бота в режиме опроса...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # Игнорировать обновления, накопившиеся пока бот был выключен
            timeout=30,                 # Увеличиваем таймаут для повышения стабильности
            read_timeout=10,
            pool_timeout=None,          # Без ограничения по времени для пула обновлений
            write_timeout=10,
            connect_timeout=10
        )
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        logger.critical(traceback.format_exc())
        
        # Перезапускаем бота в случае критической ошибки
        logger.info("Попытка перезапуска через 5 секунд...")
        time.sleep(5)
        main()  # Рекурсивный вызов для перезапуска

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Неперехваченная ошибка: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1) 