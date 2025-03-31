import os
import logging
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.environ.get('TEST_TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    BOT_TOKEN = "7513434644:AAECYxIDIkmZRjGgUDrP8ur2cZIni53Qy0E"  # Fallback токен

# Простая "база данных" для демонстрации
USERS_DB = {}
PROPERTIES_DB = [
    {"id": 1, "title": "Двухкомнатная квартира", "price": "$150,000", "location": "Центр города", "description": "Уютная квартира с хорошим ремонтом"},
    {"id": 2, "title": "Трехкомнатная квартира", "price": "$250,000", "location": "Зеленый район", "description": "Просторная квартира с видом на парк"},
    {"id": 3, "title": "Студия", "price": "$80,000", "location": "Новостройка", "description": "Современная студия в новом доме"}
]

# Функции для работы с пользователями
def save_user_data(user_id, data):
    """Сохраняет данные пользователя"""
    if user_id not in USERS_DB:
        USERS_DB[user_id] = {}
    
    USERS_DB[user_id].update(data)
    logger.info(f"Данные для пользователя {user_id} обновлены: {data}")

def get_user_data(user_id):
    """Возвращает данные пользователя"""
    return USERS_DB.get(user_id, {})

# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    # Сохраняем информацию о пользователе
    save_user_data(user_id, {
        "first_name": user.first_name,
        "username": user.username,
        "language_code": user.language_code,
        "last_command": "/start"
    })
    
    # Создаем клавиатуру для главного меню
    keyboard = [
        [InlineKeyboardButton("🏠 Объекты недвижимости", callback_data="properties")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), 
         InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем приветственное сообщение
    await update.message.reply_text(
        f"👋 Здравствуйте, {user.first_name}!\n\n"
        f"Добро пожаловать в тренировочного бота для работы с недвижимостью. "
        f"Выберите интересующий вас раздел:",
        reply_markup=reply_markup
    )
    logger.info(f"Пользователю {user_id} отправлено приветствие")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user_id = update.effective_user.id
    save_user_data(user_id, {"last_command": "/help"})
    
    help_text = (
        "📱 *Доступные команды:*\n\n"
        "/start - Перезапустить бота\n"
        "/help - Показать эту справку\n"
        "/properties - Показать объекты недвижимости\n"
        "/settings - Настройки пользователя\n\n"
        "Вы также можете использовать интерактивные кнопки в сообщениях."
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")
    logger.info(f"Пользователю {user_id} отправлена справка")

async def properties_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /properties"""
    user_id = update.effective_user.id
    save_user_data(user_id, {"last_command": "/properties"})
    
    await show_properties_list(update.message)
    logger.info(f"Пользователю {user_id} отправлен список объектов")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings"""
    user_id = update.effective_user.id
    save_user_data(user_id, {"last_command": "/settings"})
    
    await show_settings(update.message)
    logger.info(f"Пользователю {user_id} отправлены настройки")

# Вспомогательные функции для отображения данных
async def show_properties_list(message):
    """Показывает список объектов недвижимости"""
    # Создаем клавиатуру с кнопками для каждого объекта
    keyboard = []
    for prop in PROPERTIES_DB:
        keyboard.append([InlineKeyboardButton(
            f"{prop['title']} - {prop['price']}", 
            callback_data=f"property_{prop['id']}"
        )])
    keyboard.append([InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        "🏠 *Доступные объекты недвижимости:*\n\n"
        "Выберите объект для просмотра подробной информации:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_property_details(message, property_id):
    """Показывает детальную информацию об объекте"""
    property_id = int(property_id)
    property_data = next((p for p in PROPERTIES_DB if p["id"] == property_id), None)
    
    if not property_data:
        await message.reply_text("Объект не найден")
        return
    
    # Создаем клавиатуру для возврата
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад к списку", callback_data="properties")],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    details = (
        f"🏠 *{property_data['title']}*\n\n"
        f"💰 Цена: {property_data['price']}\n"
        f"📍 Расположение: {property_data['location']}\n"
        f"📝 Описание: {property_data['description']}"
    )
    
    await message.reply_text(details, reply_markup=reply_markup, parse_mode="Markdown")

async def show_settings(message):
    """Показывает настройки пользователя"""
    user_id = message.chat.id
    user_data = get_user_data(user_id)
    
    # Создаем клавиатуру для настроек
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить профиль", callback_data="update_profile")],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    settings_text = (
        "⚙️ *Ваши настройки:*\n\n"
        f"👤 Имя: {user_data.get('first_name', 'Не указано')}\n"
        f"🔤 Язык: {user_data.get('language_code', 'Не указан')}\n\n"
        f"Последняя команда: {user_data.get('last_command', 'Нет')}"
    )
    
    await message.reply_text(settings_text, reply_markup=reply_markup, parse_mode="Markdown")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Логируем сообщение
    logger.info(f"Получено сообщение от {user_id}: {message_text}")
    
    # Проверяем, не является ли сообщение командой
    if message_text.lower() == '/start':
        return await start_command(update, context)
    elif message_text.lower() == '/help':
        return await help_command(update, context)
    elif message_text.lower() == '/properties':
        return await properties_command(update, context)
    elif message_text.lower() == '/settings':
        return await settings_command(update, context)
    
    # Если не команда, отправляем эхо
    await update.message.reply_text(
        f"Вы написали: {message_text}\n\n"
        "Используйте команду /help для просмотра списка доступных команд."
    )

# Обработчик callback-запросов (нажатия на кнопки)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на inline-кнопки"""
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data
    
    # Логируем callback
    logger.info(f"Получен callback от {user_id}: {callback_data}")
    
    # Сообщаем Telegram, что мы обработали нажатие
    await query.answer()
    
    # Обрабатываем различные callback
    if callback_data == "menu":
        # Главное меню
        keyboard = [
            [InlineKeyboardButton("🏠 Объекты недвижимости", callback_data="properties")],
            [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), 
             InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            "🏢 *Главное меню*\n\n"
            "Выберите интересующий вас раздел:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif callback_data == "properties":
        # Список объектов
        keyboard = []
        for prop in PROPERTIES_DB:
            keyboard.append([InlineKeyboardButton(
                f"{prop['title']} - {prop['price']}", 
                callback_data=f"property_{prop['id']}"
            )])
        keyboard.append([InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            "🏠 *Доступные объекты недвижимости:*\n\n"
            "Выберите объект для просмотра подробной информации:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif callback_data.startswith("property_"):
        # Детали объекта
        property_id = int(callback_data.split("_")[1])
        property_data = next((p for p in PROPERTIES_DB if p["id"] == property_id), None)
        
        if not property_data:
            await query.message.edit_text("Объект не найден")
            return
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад к списку", callback_data="properties")],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        details = (
            f"🏠 *{property_data['title']}*\n\n"
            f"💰 Цена: {property_data['price']}\n"
            f"📍 Расположение: {property_data['location']}\n"
            f"📝 Описание: {property_data['description']}"
        )
        
        await query.message.edit_text(details, reply_markup=reply_markup, parse_mode="Markdown")
        
    elif callback_data == "about":
        # О боте
        keyboard = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        about_text = (
            "ℹ️ *О боте*\n\n"
            "Этот тренировочный бот создан для демонстрации работы с Telegram API "
            "и разработки функциональности для основного проекта DualAI.\n\n"
            "Бот позволяет просматривать объекты недвижимости и управлять настройками пользователя."
        )
        
        await query.message.edit_text(about_text, reply_markup=reply_markup, parse_mode="Markdown")
        
    elif callback_data == "settings":
        # Настройки
        user_data = get_user_data(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить профиль", callback_data="update_profile")],
            [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = (
            "⚙️ *Ваши настройки:*\n\n"
            f"👤 Имя: {user_data.get('first_name', 'Не указано')}\n"
            f"🔤 Язык: {user_data.get('language_code', 'Не указан')}\n\n"
            f"Последняя команда: {user_data.get('last_command', 'Нет')}"
        )
        
        await query.message.edit_text(settings_text, reply_markup=reply_markup, parse_mode="Markdown")
        
    elif callback_data == "update_profile":
        # Обновление профиля
        keyboard = [[InlineKeyboardButton("⬅️ Назад в настройки", callback_data="settings")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Обновляем данные пользователя
        user = query.from_user
        save_user_data(user_id, {
            "first_name": user.first_name,
            "username": user.username,
            "language_code": user.language_code,
            "updated_at": "Сейчас"
        })
        
        await query.message.edit_text(
            "✅ Ваш профиль успешно обновлен!",
            reply_markup=reply_markup
        )

# Обработчик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ошибки"""
    logger.error(f"Произошла ошибка: {context.error}")
    
    try:
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Произошла ошибка при обработке вашего запроса.\n"
                "Пожалуйста, попробуйте позже или используйте команду /start для перезапуска."
            )
    except:
        logger.error("Не удалось отправить сообщение об ошибке")

def main():
    """Основная функция для запуска бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("properties", properties_command))
    application.add_handler(CommandHandler("settings", settings_command))
    
    # Регистрируем обработчики сообщений и callback
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Тренировочный бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main() 