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

# Список администраторов из переменных окружения
ADMIN_ID = os.getenv("ADMIN_ID")
ADMIN_IDS = [int(ADMIN_ID)] if ADMIN_ID else [847964518]

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик вызова административной панели."""
    query = update.callback_query
    await query.answer()
    
    # Проверяем права администратора
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.message.reply_text("У вас нет прав для доступа к административной панели.")
        return
    
    # Получаем язык пользователя
    language = context.user_data.get('language', 'en')
    
    # Тексты панели на разных языках
    panel_title = {
        'en': f"⚙️ Administrative Panel ({ENVIRONMENT.upper()})",
        'es': f"⚙️ Panel de Administración ({ENVIRONMENT.upper()})",
        'de': f"⚙️ Administrationsbereich ({ENVIRONMENT.upper()})",
        'fr': f"⚙️ Panneau d'Administration ({ENVIRONMENT.upper()})",
        'ru': f"⚙️ Панель Администратора ({ENVIRONMENT.upper()})"
    }
    
    env_info = {
        'en': f"Environment: {ENVIRONMENT.upper()}\nVercel Deployment: {'YES' if os.getenv('VERCEL') else 'NO'}\nAdmin ID: {ADMIN_ID}",
        'es': f"Entorno: {ENVIRONMENT.upper()}\nDespliegue Vercel: {'SÍ' if os.getenv('VERCEL') else 'NO'}\nID Admin: {ADMIN_ID}",
        'de': f"Umgebung: {ENVIRONMENT.upper()}\nVercel Deployment: {'JA' if os.getenv('VERCEL') else 'NEIN'}\nAdmin ID: {ADMIN_ID}",
        'fr': f"Environnement: {ENVIRONMENT.upper()}\nDéploiement Vercel: {'OUI' if os.getenv('VERCEL') else 'NON'}\nID Admin: {ADMIN_ID}",
        'ru': f"Окружение: {ENVIRONMENT.upper()}\nРазвёртывание Vercel: {'ДА' if os.getenv('VERCEL') else 'НЕТ'}\nID Админа: {ADMIN_ID}"
    }
    
    # Создаем сообщение панели администратора
    message = f"{panel_title.get(language, panel_title['en'])}\n\n{env_info.get(language, env_info['en'])}"
    
    # Создаем клавиатуру для административной панели
    # Названия кнопок на разных языках
    button_texts = {
        'content': {
            'en': "📝 Content Management",
            'es': "📝 Gestión de Contenido",
            'de': "📝 Inhaltsverwaltung",
            'fr': "📝 Gestion de Contenu",
            'ru': "📝 Управление Контентом"
        },
        'stats': {
            'en': "📊 Statistics",
            'es': "📊 Estadísticas",
            'de': "📊 Statistiken",
            'fr': "📊 Statistiques",
            'ru': "📊 Статистика"
        },
        'notifications': {
            'en': "🔔 Notifications",
            'es': "🔔 Notificaciones",
            'de': "🔔 Benachrichtigungen",
            'fr': "🔔 Notifications",
            'ru': "🔔 Уведомления"
        },
        'test_commands': {
            'en': "🧪 Test Commands",
            'es': "🧪 Comandos de Prueba",
            'de': "🧪 Testbefehle",
            'fr': "🧪 Commandes de Test",
            'ru': "🧪 Тестовые Команды"
        },
        'back': {
            'en': "🔙 Back to Main Menu",
            'es': "🔙 Volver al Menú Principal",
            'de': "🔙 Zurück zum Hauptmenü",
            'fr': "🔙 Retour au Menu Principal",
            'ru': "🔙 Вернуться в Главное Меню"
        }
    }
    
    # Формируем базовую клавиатуру
    keyboard = [
        [InlineKeyboardButton(button_texts['content'].get(language, button_texts['content']['en']), 
                             callback_data="admin_content")],
        [InlineKeyboardButton(button_texts['stats'].get(language, button_texts['stats']['en']), 
                             callback_data="admin_stats")],
        [InlineKeyboardButton(button_texts['notifications'].get(language, button_texts['notifications']['en']), 
                             callback_data="admin_notifications")]
    ]
    
    # Добавляем кнопку тестовых команд только в тестовом окружении
    if IS_TEST_ENV:
        keyboard.append([InlineKeyboardButton(button_texts['test_commands'].get(language, button_texts['test_commands']['en']), 
                                            callback_data="admin_test_commands")])
    
    # Добавляем кнопку возврата
    keyboard.append([InlineKeyboardButton(button_texts['back'].get(language, button_texts['back']['en']), 
                                        callback_data="admin_back_to_main")])
    
    # Проверяем, содержит ли сообщение фото
    has_photo = hasattr(query.message, 'photo') and query.message.photo
    
    try:
        if has_photo:
            # Если сообщение с фото, редактируем подпись
            await query.edit_message_caption(
                caption=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Если обычное текстовое сообщение, редактируем текст
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при обновлении админ-панели: {e}")
        # В случае ошибки отправляем новое сообщение
        await query.message.reply_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    # Обновляем текущую страницу пользователя
    context.user_data['current_page'] = 'admin_panel'

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
    """Обработчик возврата из админ-панели в главное меню."""
    query = update.callback_query
    await query.answer()
    
    # Получаем язык пользователя
    language = context.user_data.get('language', 'en')
    
    # Импортируем функцию show_main_menu из client.py
    from handlers.client import show_main_menu
    
    # Возвращаемся в главное меню
    await show_main_menu(query, context, language)

# Заглушки для будущих административных функций
async def admin_content_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Заглушка для управления контентом."""
    query = update.callback_query
    await query.answer()
    
    # Получаем язык пользователя
    language = context.user_data.get('language', 'en')
    
    # Тексты заглушки на разных языках
    message = {
        'en': "Content Management will be available soon.",
        'es': "La gestión de contenido estará disponible pronto.",
        'de': "Inhaltsverwaltung wird in Kürze verfügbar sein.",
        'fr': "La gestion de contenu sera bientôt disponible.",
        'ru': "Управление контентом будет доступно в ближайшее время."
    }
    
    # Кнопка возврата
    back_text = {
        'en': "🔙 Back to Admin Panel",
        'es': "🔙 Volver al Panel de Administración",
        'de': "🔙 Zurück zum Admin-Panel",
        'fr': "🔙 Retour au Panneau d'Administration",
        'ru': "🔙 Вернуться в Панель Администратора"
    }
    
    keyboard = [[InlineKeyboardButton(
        back_text.get(language, back_text['en']), 
        callback_data="admin_panel"
    )]]
    
    # Проверяем, содержит ли сообщение фото
    has_photo = hasattr(query.message, 'photo') and query.message.photo
    
    try:
        if has_photo:
            # Если сообщение с фото, редактируем подпись
            await query.edit_message_caption(
                caption=message.get(language, message['en']),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Если обычное текстовое сообщение, редактируем текст
            await query.edit_message_text(
                text=message.get(language, message['en']),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при обновлении страницы управления контентом: {e}")
        # В случае ошибки отправляем новое сообщение
        await query.message.reply_text(
            text=message.get(language, message['en']),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def admin_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Заглушка для статистики."""
    query = update.callback_query
    await query.answer()
    
    # Получаем язык пользователя
    language = context.user_data.get('language', 'en')
    
    # Тексты заглушки на разных языках
    message = {
        'en': "Statistics will be available soon.",
        'es': "Las estadísticas estarán disponibles pronto.",
        'de': "Statistiken werden in Kürze verfügbar sein.",
        'fr': "Les statistiques seront bientôt disponibles.",
        'ru': "Статистика будет доступна в ближайшее время."
    }
    
    # Кнопка возврата
    back_text = {
        'en': "🔙 Back to Admin Panel",
        'es': "🔙 Volver al Panel de Administración",
        'de': "🔙 Zurück zum Admin-Panel",
        'fr': "🔙 Retour au Panneau d'Administration",
        'ru': "🔙 Вернуться в Панель Администратора"
    }
    
    keyboard = [[InlineKeyboardButton(
        back_text.get(language, back_text['en']), 
        callback_data="admin_panel"
    )]]
    
    # Проверяем, содержит ли сообщение фото
    has_photo = hasattr(query.message, 'photo') and query.message.photo
    
    try:
        if has_photo:
            # Если сообщение с фото, редактируем подпись
            await query.edit_message_caption(
                caption=message.get(language, message['en']),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Если обычное текстовое сообщение, редактируем текст
            await query.edit_message_text(
                text=message.get(language, message['en']),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при обновлении страницы статистики: {e}")
        # В случае ошибки отправляем новое сообщение
        await query.message.reply_text(
            text=message.get(language, message['en']),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def admin_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Заглушка для управления уведомлениями."""
    query = update.callback_query
    await query.answer()
    
    # Получаем язык пользователя
    language = context.user_data.get('language', 'en')
    
    # Тексты заглушки на разных языках
    message = {
        'en': "Notification management will be available soon.",
        'es': "La gestión de notificaciones estará disponible pronto.",
        'de': "Benachrichtigungsverwaltung wird in Kürze verfügbar sein.",
        'fr': "La gestion des notifications sera bientôt disponible.",
        'ru': "Управление уведомлениями будет доступно в ближайшее время."
    }
    
    # Кнопка возврата
    back_text = {
        'en': "🔙 Back to Admin Panel",
        'es': "🔙 Volver al Panel de Administración",
        'de': "🔙 Zurück zum Admin-Panel",
        'fr': "🔙 Retour au Panneau d'Administration",
        'ru': "🔙 Вернуться в Панель Администратора"
    }
    
    keyboard = [[InlineKeyboardButton(
        back_text.get(language, back_text['en']), 
        callback_data="admin_panel"
    )]]
    
    # Проверяем, содержит ли сообщение фото
    has_photo = hasattr(query.message, 'photo') and query.message.photo
    
    try:
        if has_photo:
            # Если сообщение с фото, редактируем подпись
            await query.edit_message_caption(
                caption=message.get(language, message['en']),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Если обычное текстовое сообщение, редактируем текст
            await query.edit_message_text(
                text=message.get(language, message['en']),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при обновлении страницы уведомлений: {e}")
        # В случае ошибки отправляем новое сообщение
        await query.message.reply_text(
            text=message.get(language, message['en']),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

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