import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    user = update.effective_user
    message_text = update.message.text
    logger.info(f"Пользователь {user.first_name} (ID: {user.id}) отправил сообщение: {message_text}")
    
    # Отправляем эхо
    await update.message.reply_text(f"Вы сказали: {message_text}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки."""
    query = update.callback_query
    user = query.from_user
    callback_data = query.data
    logger.info(f"Пользователь {user.first_name} (ID: {user.id}) нажал кнопку: {callback_data}")
    
    # Сообщаем Telegram, что мы обработали запрос
    await query.answer()
    
    # Отправляем ответ в зависимости от нажатой кнопки
    if callback_data == "info":
        await query.message.reply_text("Это тестовый бот для проекта DualAI.")
    elif callback_data == "test":
        await query.message.reply_text("Тестовое сообщение. Бот работает!")

def main():
    """Основная функция."""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 