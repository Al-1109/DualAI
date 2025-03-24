import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Функция для загрузки содержимого файлов
def load_content_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return "Content file not found."

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    # Загружаем приветственное сообщение с выбором языка
    welcome_message = load_content_file("Telegram_content/welcome_message.md")
    
    # Создаем клавиатуру для выбора языка
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        ],
        [
            InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
        ],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем приветственное сообщение с клавиатурой
    await update.message.reply_text(
        text=welcome_message,
        reply_markup=reply_markup
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора языка."""
    query = update.callback_query
    await query.answer()
    
    # Получаем выбранный язык из данных колбэка
    language = query.data.split('_')[1]
    
    # Сохраняем выбранный язык в данных пользователя
    context.user_data['language'] = language
    
    # Загружаем главное меню для выбранного языка
    menu_content = load_content_file(f"Telegram_content/{language}/main_menu.md")
    
    # Создаем клавиатуру для главного меню (зависит от языка)
    if language == 'en':
        keyboard = [
            [InlineKeyboardButton("🏠 Properties", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Contact us", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 News", callback_data="menu_news")],
            [InlineKeyboardButton("🌍 Change language", callback_data="menu_language")]
        ]
    elif language == 'es':
        keyboard = [
            [InlineKeyboardButton("🏠 Propiedades", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Contáctenos", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 Noticias", callback_data="menu_news")],
            [InlineKeyboardButton("🌍 Cambiar idioma", callback_data="menu_language")]
        ]
    elif language == 'de':
        keyboard = [
            [InlineKeyboardButton("🏠 Immobilien", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Kontakt", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 Nachrichten", callback_data="menu_news")],
            [InlineKeyboardButton("🌍 Sprache ändern", callback_data="menu_language")]
        ]
    elif language == 'fr':
        keyboard = [
            [InlineKeyboardButton("🏠 Propriétés", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Contactez-nous", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 Actualités", callback_data="menu_news")],
            [InlineKeyboardButton("🌍 Changer de langue", callback_data="menu_language")]
        ]
    elif language == 'ru':
        keyboard = [
            [InlineKeyboardButton("🏠 Объекты", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Связаться с нами", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 Новости", callback_data="menu_news")],
            [InlineKeyboardButton("🌍 Изменить язык", callback_data="menu_language")]
        ]
    else:
        # По умолчанию английский
        keyboard = [
            [InlineKeyboardButton("🏠 Properties", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Contact us", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 News", callback_data="menu_news")],
            [InlineKeyboardButton("🌍 Change language", callback_data="menu_language")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Обновляем сообщение, добавляя клавиатуру
    await query.edit_message_text(
        text=menu_content,
        reply_markup=reply_markup
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора пункта меню."""
    query = update.callback_query
    await query.answer()
    
    # Получаем выбранный пункт меню и язык пользователя
    menu_item = query.data.split('_')[1]
    language = context.user_data.get('language', 'en')
    
    if menu_item == 'language':
        # Отправляем меню выбора языка
        welcome_message = load_content_file("Telegram_content/welcome_message.md")
        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
            ],
            [
                InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
                InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
            ],
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=welcome_message, reply_markup=reply_markup)
        return
    
    if menu_item == 'back':
        # Возвращаемся к главному меню с текущим языком
        menu_content = load_content_file(f"Telegram_content/{language}/main_menu.md")
        
        # Создаем клавиатуру для главного меню на текущем языке
        if language == 'en':
            keyboard = [
                [InlineKeyboardButton("🏠 Properties", callback_data="menu_properties")],
                [InlineKeyboardButton("📝 Contact us", callback_data="menu_contact")],
                [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
                [InlineKeyboardButton("📰 News", callback_data="menu_news")],
                [InlineKeyboardButton("🌍 Change language", callback_data="menu_language")]
            ]
        elif language == 'es':
            keyboard = [
                [InlineKeyboardButton("🏠 Propiedades", callback_data="menu_properties")],
                [InlineKeyboardButton("📝 Contáctenos", callback_data="menu_contact")],
                [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
                [InlineKeyboardButton("📰 Noticias", callback_data="menu_news")],
                [InlineKeyboardButton("🌍 Cambiar idioma", callback_data="menu_language")]
            ]
        elif language == 'de':
            keyboard = [
                [InlineKeyboardButton("🏠 Immobilien", callback_data="menu_properties")],
                [InlineKeyboardButton("📝 Kontakt", callback_data="menu_contact")],
                [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
                [InlineKeyboardButton("📰 Nachrichten", callback_data="menu_news")],
                [InlineKeyboardButton("🌍 Sprache ändern", callback_data="menu_language")]
            ]
        elif language == 'fr':
            keyboard = [
                [InlineKeyboardButton("🏠 Propriétés", callback_data="menu_properties")],
                [InlineKeyboardButton("📝 Contactez-nous", callback_data="menu_contact")],
                [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
                [InlineKeyboardButton("📰 Actualités", callback_data="menu_news")],
                [InlineKeyboardButton("🌍 Changer de langue", callback_data="menu_language")]
            ]
        elif language == 'ru':
            keyboard = [
                [InlineKeyboardButton("🏠 Объекты", callback_data="menu_properties")],
                [InlineKeyboardButton("📝 Связаться с нами", callback_data="menu_contact")],
                [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
                [InlineKeyboardButton("📰 Новости", callback_data="menu_news")],
                [InlineKeyboardButton("🌍 Изменить язык", callback_data="menu_language")]
            ]
        else:
            # По умолчанию английский
            keyboard = [
                [InlineKeyboardButton("🏠 Properties", callback_data="menu_properties")],
                [InlineKeyboardButton("📝 Contact us", callback_data="menu_contact")],
                [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
                [InlineKeyboardButton("📰 News", callback_data="menu_news")],
                [InlineKeyboardButton("🌍 Change language", callback_data="menu_language")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=menu_content, reply_markup=reply_markup)
        return
    
    # Заглушки для разных пунктов меню
    messages = {
        'properties': {
            'en': "Here are our available properties. This feature is coming soon.",
            'es': "Aquí están nuestras propiedades disponibles. Esta función estará disponible próximamente.",
            'de': "Hier sind unsere verfügbaren Immobilien. Diese Funktion wird in Kürze verfügbar sein.",
            'fr': "Voici nos propriétés disponibles. Cette fonctionnalité sera bientôt disponible.",
            'ru': "Вот наши доступные объекты. Эта функция скоро будет доступна."
        },
        'contact': {
            'en': "Contact our team. This feature is coming soon.",
            'es': "Contacte a nuestro equipo. Esta función estará disponible próximamente.",
            'de': "Kontaktieren Sie unser Team. Diese Funktion wird in Kürze verfügbar sein.",
            'fr': "Contactez notre équipe. Cette fonctionnalité sera bientôt disponible.",
            'ru': "Свяжитесь с нашей командой. Эта функция скоро будет доступна."
        },
        'faq': {
            'en': "Frequently Asked Questions. This feature is coming soon.",
            'es': "Preguntas Frecuentes. Esta función estará disponible próximamente.",
            'de': "Häufig gestellte Fragen. Diese Funktion wird in Kürze verfügbar sein.",
            'fr': "Foire Aux Questions. Cette fonctionnalité sera bientôt disponible.",
            'ru': "Часто задаваемые вопросы. Эта функция скоро будет доступна."
        },
        'news': {
            'en': "Latest news. This feature is coming soon.",
            'es': "Últimas noticias. Esta función estará disponible próximamente.",
            'de': "Neueste Nachrichten. Diese Funktion wird in Kürze verfügbar sein.",
            'fr': "Dernières actualités. Cette fonctionnalité sera bientôt disponible.",
            'ru': "Последние новости. Эта функция скоро будет доступна."
        }
    }
    
    # Получаем сообщение для выбранного пункта меню на выбранном языке
    message = messages.get(menu_item, {}).get(language, "Feature coming soon.")
    
    # Создаем кнопку возврата в главное меню
    back_button_text = {
        'en': "🔙 Back to Main Menu",
        'es': "🔙 Volver al Menú Principal",
        'de': "🔙 Zurück zum Hauptmenü",
        'fr': "🔙 Retour au Menu Principal",
        'ru': "🔙 Вернуться в Главное Меню"
    }
    
    keyboard = [[InlineKeyboardButton(back_button_text.get(language, "🔙 Back"), callback_data="menu_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем ответ
    await query.edit_message_text(text=message, reply_markup=reply_markup)