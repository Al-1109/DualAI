import os
import logging
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError, NetworkError

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.environ.get('TEST_TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    TELEGRAM_BOT_TOKEN = "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"  # Fallback токен

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    try:
        user = update.effective_user
        logger.info(f"Пользователь {user.first_name} (ID: {user.id}) отправил команду /start")
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("О боте", callback_data="info")],
            [InlineKeyboardButton("Тест", callback_data="test")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем приветственное сообщение
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\nЯ тестовый бот для проекта DualAI.",
            reply_markup=reply_markup
        )
        logger.info(f"Отправлено приветственное сообщение пользователю {user.id}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}")
        traceback.print_exc()
        if update.message:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    try:
        user = update.effective_user
        message_text = update.message.text
        logger.info(f"Пользователь {user.first_name} (ID: {user.id}) отправил сообщение: {message_text}")
        
        # Проверяем, является ли сообщение командой /start
        if message_text.lower() == '/start':
            return await start(update, context)
        
        # Отправляем эхо
        await update.message.reply_text(f"Вы сказали: {message_text}")
        logger.info(f"Отправлен эхо-ответ пользователю {user.id}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике handle_message: {e}")
        traceback.print_exc()
        if update.message:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова позже.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки."""
    try:
        query = update.callback_query
        user = query.from_user
        callback_data = query.data
        logger.info(f"Пользователь {user.first_name} (ID: {user.id}) нажал кнопку: {callback_data}")
        
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
            
            await query.message.reply_text(
                f"👋 Главное меню бота DualAI.\n\nВыберите опцию:",
                reply_markup=reply_markup
            )
            logger.info(f"Пользователь {user.id} вернулся в главное меню")
    except Exception as e:
        logger.error(f"Ошибка в обработчике handle_callback: {e}")
        traceback.print_exc()
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, отправьте /start для перезапуска бота.")
        except:
            logger.error("Не удалось отправить сообщение об ошибке")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error(f"Ошибка при обработке обновления: {context.error}")
    traceback.print_exc()
    
    try:
        # Отправляем сообщение об ошибке, если возможно
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Произошла ошибка при обработке вашего запроса.\n"
                "Пожалуйста, попробуйте отправить /start для перезапуска бота."
            )
    except:
        logger.error("Не удалось отправить сообщение об ошибке")

def main():
    """Основная функция."""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен!")
    
    # Запускаем с базовыми параметрами для стабильности
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True    # Игнорируем обновления, которые накопились когда бот был выключен
    )

if __name__ == "__main__":
    main() 