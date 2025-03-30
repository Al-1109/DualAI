import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

# Импортируем функции из utils
from utils import load_content_file

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определяем окружение
IS_TEST_ENV = os.getenv("VERCEL_ENV") == "preview"
ENVIRONMENT = "test" if IS_TEST_ENV else "production"

# Список ID администраторов
ADMIN_IDS = [int(os.getenv("ADMIN_ID", "847964518"))]

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для админ-панели."""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id not in ADMIN_IDS:
        await query.message.reply_text("У вас нет прав для доступа к админ-панели.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📝 Управление контентом", callback_data="admin_content")],
        [InlineKeyboardButton("🔔 Уведомления", callback_data="admin_notifications")],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="admin_back_to_main")]
    ]
    
    await query.message.edit_text(
        "Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_switch_environment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик переключения между средами разработки и продакшн."""
    query = update.callback_query
    await query.answer()
    
    # Проверяем права администратора
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.message.reply_text("У вас нет прав для переключения окружения.")
        return
    
    # Получаем текущее окружение и переключаем его
    current_env = context.user_data.get('environment', 'production')
    new_env = 'development' if current_env == 'production' else 'production'
    
    # Сохраняем новое окружение
    context.user_data['environment'] = new_env
    
    # Показываем снова админ-панель (она отобразит новое окружение)
    await admin_panel_callback(update, context)
    
    # Логируем переключение
    logger.info(f"Администратор {user_id} переключил окружение с {current_env} на {new_env}")

async def admin_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для возврата в главное меню."""
    query = update.callback_query
    await query.answer()
    
    # Получаем язык пользователя
    language = context.user_data.get('language', 'en')
    is_admin = update.effective_user.id in ADMIN_IDS
    
    # Создаем клавиатуру главного меню
    keyboard = create_menu_keyboard(language, is_admin)
    
    await query.message.edit_text(
        "Главное меню",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Заглушки для будущих административных функций
async def admin_content_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для управления контентом."""
    query = update.callback_query
    await query.answer("В разработке")

async def admin_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для просмотра статистики."""
    query = update.callback_query
    await query.answer("В разработке")

async def admin_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для управления уведомлениями."""
    query = update.callback_query
    await query.answer("В разработке")

async def admin_test_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик тестовых команд (доступен только в тестовом окружении)."""
    query = update.callback_query
    await query.answer()
    
    # Проверяем права администратора
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.message.reply_text("У вас нет прав для доступа к тестовым командам.")
        return
    
    # Проверяем, что мы в тестовом окружении
    if not IS_TEST_ENV:
        await query.message.reply_text("Тестовые команды доступны только в тестовом окружении.")
        return
    
    # Получаем язык пользователя
    language = context.user_data.get('language', 'en')
    
    # Тексты для тестовых команд
    test_commands_text = {
        'en': """🧪 Test Commands

Available commands:
/test - Basic test command
/env - Show environment info
/ping - Check bot response
/echo [text] - Echo back your message
/admin - Show admin panel

Environment: TEST
Vercel: {vercel}
Admin ID: {admin_id}""",
        'ru': """🧪 Тестовые Команды

Доступные команды:
/test - Базовая тестовая команда
/env - Показать информацию об окружении
/ping - Проверить ответ бота
/echo [текст] - Отправить ваше сообщение обратно
/admin - Показать панель администратора

Окружение: ТЕСТ
Vercel: {vercel}
ID Админа: {admin_id}"""
    }
    
    # Кнопки
    button_texts = {
        'en': {
            'back': "🔙 Back to Admin Panel",
            'refresh': "🔄 Refresh Status",
            'send_test': "📤 Send Test Message"
        },
        'ru': {
            'back': "🔙 Вернуться в Панель Администратора",
            'refresh': "🔄 Обновить Статус",
            'send_test': "📤 Отправить Тестовое Сообщение"
        }
    }
    
    # Формируем текст с актуальными данными
    message = test_commands_text.get(language, test_commands_text['en']).format(
        vercel="YES" if os.getenv('VERCEL') else "NO",
        admin_id=ADMIN_ID
    )
    
    # Создаем клавиатуру
    keyboard = [
        [
            InlineKeyboardButton(
                button_texts.get(language, button_texts['en'])['refresh'],
                callback_data="admin_test_refresh"
            ),
            InlineKeyboardButton(
                button_texts.get(language, button_texts['en'])['send_test'],
                callback_data="admin_test_send"
            )
        ],
        [
            InlineKeyboardButton(
                button_texts.get(language, button_texts['en'])['back'],
                callback_data="admin_panel"
            )
        ]
    ]
    
    try:
            await query.edit_message_text(
            text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при отображении тестовых команд: {e}")
        await query.message.reply_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def admin_test_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обновление статуса тестового окружения."""
    query = update.callback_query
    await query.answer("Refreshing status...")
    await admin_test_commands(update, context)

async def admin_test_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка тестового сообщения."""
    query = update.callback_query
    await query.answer()
    
    test_message = f"""🧪 Test Message
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Environment: {ENVIRONMENT.upper()}
Vercel: {"YES" if os.getenv('VERCEL') else "NO"}
Admin ID: {ADMIN_ID}"""
    
    await query.message.reply_text(test_message)