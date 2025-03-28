import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Импортируем функции из utils
from utils import load_content_file

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Список администраторов (ID пользователей Telegram)
# В будущем этот список можно перенести в файл конфигурации или БД
ADMIN_IDS = [8178580481]  # ID бота

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
    
    # Получаем текущее окружение (по умолчанию 'production')
    environment = context.user_data.get('environment', 'production')
    
    # Тексты панели на разных языках
    panel_title = {
        'en': "⚙️ Administrative Panel",
        'es': "⚙️ Panel de Administración",
        'de': "⚙️ Administrationsbereich",
        'fr': "⚙️ Panneau d'Administration",
        'ru': "⚙️ Панель Администратора"
    }
    
    env_status = {
        'en': f"Current Environment: {'PRODUCTION' if environment == 'production' else 'DEVELOPMENT'}",
        'es': f"Entorno Actual: {'PRODUCCIÓN' if environment == 'production' else 'DESARROLLO'}",
        'de': f"Aktuelle Umgebung: {'PRODUKTION' if environment == 'production' else 'ENTWICKLUNG'}",
        'fr': f"Environnement Actuel: {'PRODUCTION' if environment == 'production' else 'DÉVELOPPEMENT'}",
        'ru': f"Текущее окружение: {'ПРОДАКШН' if environment == 'production' else 'РАЗРАБОТКА'}"
    }
    
    # Создаем сообщение панели администратора
    message = f"{panel_title.get(language, '⚙️ Administrative Panel')}\n\n{env_status.get(language, '')}"
    
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
        'switch_env': {
            'en': "🔄 Switch to " + ("DEVELOPMENT" if environment == 'production' else "PRODUCTION"),
            'es': "🔄 Cambiar a " + ("DESARROLLO" if environment == 'production' else "PRODUCCIÓN"),
            'de': "🔄 Wechseln zu " + ("ENTWICKLUNG" if environment == 'production' else "PRODUKTION"),
            'fr': "🔄 Passer à " + ("DÉVELOPPEMENT" if environment == 'production' else "PRODUCTION"),
            'ru': "🔄 Переключить на " + ("РАЗРАБОТКУ" if environment == 'production' else "ПРОДАКШН")
        },
        'back': {
            'en': "🔙 Back to Main Menu",
            'es': "🔙 Volver al Menú Principal",
            'de': "🔙 Zurück zum Hauptmenü",
            'fr': "🔙 Retour au Menu Principal",
            'ru': "🔙 Вернуться в Главное Меню"
        }
    }
    
    # Формируем клавиатуру
    keyboard = [
        [InlineKeyboardButton(button_texts['content'].get(language, button_texts['content']['en']), 
                             callback_data="admin_content")],
        [InlineKeyboardButton(button_texts['stats'].get(language, button_texts['stats']['en']), 
                             callback_data="admin_stats")],
        [InlineKeyboardButton(button_texts['notifications'].get(language, button_texts['notifications']['en']), 
                             callback_data="admin_notifications")],
        [InlineKeyboardButton(button_texts['switch_env'].get(language, button_texts['switch_env']['en']), 
                             callback_data="admin_switch_env")],
        [InlineKeyboardButton(button_texts['back'].get(language, button_texts['back']['en']), 
                             callback_data="admin_back_to_main")]
    ]
    
    # Обновляем сообщение
    await query.edit_message_text(
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
    
    await query.edit_message_text(
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
    
    await query.edit_message_text(
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
    
    await query.edit_message_text(
        text=message.get(language, message['en']),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )