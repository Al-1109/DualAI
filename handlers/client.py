import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Импортируем функции из utils вместо bot
from utils import send_to_channel, CHANNEL_ID, load_content_file

# ID администратора из переменных окружения
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Функция для создания языковых кнопок
def create_language_buttons():
    """Создает стандартные кнопки выбора языка"""
    return [
        [
            InlineKeyboardButton("🇬🇧", callback_data="lang_en_current"),
            InlineKeyboardButton("🇪🇸", callback_data="lang_es_current"),
            InlineKeyboardButton("🇩🇪", callback_data="lang_de_current"),
            InlineKeyboardButton("🇫🇷", callback_data="lang_fr_current"),
            InlineKeyboardButton("🇷🇺", callback_data="lang_ru_current"),
        ]
    ]

# Функция для создания клавиатуры меню на нужном языке
def create_menu_keyboard(language):
    """Создает клавиатуру для главного меню на нужном языке"""
    if language == 'en':
        keyboard = [
            [InlineKeyboardButton("🏠 Properties", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Contact us", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 News", callback_data="menu_news")],
        ]
    elif language == 'es':
        keyboard = [
            [InlineKeyboardButton("🏠 Propiedades", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Contáctenos", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 Noticias", callback_data="menu_news")],
        ]
    elif language == 'de':
        keyboard = [
            [InlineKeyboardButton("🏠 Immobilien", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Kontakt", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 Nachrichten", callback_data="menu_news")],
        ]
    elif language == 'fr':
        keyboard = [
            [InlineKeyboardButton("🏠 Propriétés", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Contactez-nous", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 Actualités", callback_data="menu_news")],
        ]
    elif language == 'ru':
        keyboard = [
            [InlineKeyboardButton("🏠 Объекты", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Связаться с нами", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 Новости", callback_data="menu_news")],
        ]
    else:
        # По умолчанию английский
        keyboard = [
            [InlineKeyboardButton("🏠 Properties", callback_data="menu_properties")],
            [InlineKeyboardButton("📝 Contact us", callback_data="menu_contact")],
            [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
            [InlineKeyboardButton("📰 News", callback_data="menu_news")],
        ]
    
    # Добавляем языковые кнопки в нижнюю часть меню
    keyboard.extend(create_language_buttons())
    
    return keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    # Проверяем наличие параметра языка
    args = context.args
    if args and args[0].startswith('lang_'):
        # Получаем код языка из параметра
        language = args[0].split('_')[1]
        # Загружаем контент главного меню
        content = load_content_file(f"Telegram_content/{language}/main_menu.md")
        # Создаем клавиатуру меню
        keyboard = create_menu_keyboard(language)
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Сохраняем язык и страницу
        context.user_data['language'] = language
        context.user_data['current_page'] = 'main_menu'
        # Отправляем фото с меню
        with open('media/images/photo.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=content,
                reply_markup=reply_markup
            )
    else:
        # Первый вход - показываем выбор языка
        welcome_message = load_content_file("Telegram_content/welcome_message.md")
        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 Start in English", callback_data="lang_en_main"),
                InlineKeyboardButton("🇪🇸 Comenzar en Español", callback_data="lang_es_main"),
            ],
            [
                InlineKeyboardButton("🇩🇪 Auf Deutsch starten", callback_data="lang_de_main"),
                InlineKeyboardButton("🇫🇷 Commencer en Français", callback_data="lang_fr_main"),
            ],
            [
                InlineKeyboardButton("🇷🇺 Начать на русском", callback_data="lang_ru_main"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['current_page'] = 'welcome'
        # Отправляем фото с приветствием
        with open('media/images/photo.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=welcome_message,
                reply_markup=reply_markup
            )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора языка."""
    query = update.callback_query
    await query.answer()
    
    # Получаем выбранный язык и режим из данных колбэка (lang_XX_YY где XX - язык, YY - режим)
    callback_parts = query.data.split('_')
    language = callback_parts[1]
    mode = callback_parts[2] if len(callback_parts) > 2 else 'main'
    
    # Сохраняем выбранный язык в данных пользователя
    context.user_data['language'] = language
    
    # Определяем текущую страницу пользователя
    current_page = context.user_data.get('current_page', 'welcome')
    
    # Если режим 'current' - это смена языка из меню
    if mode == 'current':
        # Если мы находимся в подменю, остаемся на той же странице
        if current_page in ['properties', 'contact', 'faq', 'news']:
            # Отображаем соответствующую страницу на новом языке
            await show_submenu_page(query, context, current_page, language)
            return
    
    # Создаем базовую клавиатуру с кнопками меню
    keyboard = [
        [InlineKeyboardButton("🏠 Объекты", callback_data="menu_properties")],
        [InlineKeyboardButton("📝 Связаться с нами", callback_data="menu_contact")],
        [InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")],
        [InlineKeyboardButton("📰 Новости", callback_data="menu_news")],
    ]
    
    # Проверяем, является ли пользователь администратором бота
    chat_member = await context.bot.get_chat_member(query.message.chat.id, query.from_user.id)
    if chat_member.status in ['creator', 'administrator']:
        keyboard.append([InlineKeyboardButton("⚙️ Панель Администратора", callback_data="menu_admin")])
    
    # Добавляем языковые кнопки в нижнюю часть меню
    keyboard.append([
        InlineKeyboardButton("🇬🇧", callback_data="lang_en_current"),
        InlineKeyboardButton("🇪🇸", callback_data="lang_es_current"),
        InlineKeyboardButton("🇩🇪", callback_data="lang_de_current"),
        InlineKeyboardButton("🇫🇷", callback_data="lang_fr_current"),
        InlineKeyboardButton("🇷🇺", callback_data="lang_ru_current"),
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Загружаем контент главного меню на выбранном языке
    content = load_content_file(f"Telegram_content/{language}/main_menu.md")
    
    # Обновляем текущую страницу
    context.user_data['current_page'] = 'main_menu'
    
    # Отправляем новое сообщение с фото и удаляем старое
    with open('media/images/photo.jpg', 'rb') as photo:
        await query.message.reply_photo(
            photo=photo,
            caption=content,
            reply_markup=reply_markup
        )
    await query.message.delete()

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора пункта меню."""
    query = update.callback_query
    await query.answer()
    
    # Получаем выбранный пункт меню и язык пользователя
    menu_item = query.data.split('_')[1]
    language = context.user_data.get('language', 'en')
    
    # Обновляем текущую страницу пользователя
    context.user_data['current_page'] = menu_item
    
    # Показываем соответствующую страницу
    await show_submenu_page(query, context, menu_item, language)

async def show_submenu_page(query, context, page, language):
    """Показывает подменю на выбранном языке"""
    
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
    message = messages.get(page, {}).get(language, "Feature coming soon.")
    
    # Создаем кнопку возврата в главное меню
    back_button_text = {
        'en': "🔙 Back to Main Menu",
        'es': "🔙 Volver al Menú Principal",
        'de': "🔙 Zurück zum Hauptmenü",
        'fr': "🔙 Retour au Menu Principal",
        'ru': "🔙 Вернуться в Главное Меню"
    }
    
    keyboard = [[InlineKeyboardButton(back_button_text.get(language, "🔙 Back"), callback_data=f"lang_{language}_main")]]
    
    # Добавляем языковые кнопки внизу
    keyboard.extend(create_language_buttons())
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Создаем уникальный ключ для этого типа сообщения
    message_key = f"{page}_{language}"
    
    # Проверяем, является ли это сообщение сообщением канала
    if query.message.chat.id == CHANNEL_ID:
        # Используем функцию send_to_channel для обновления сообщения в канале
        await send_to_channel(context, message, reply_markup, message_key)
    else:
        # Это личный чат с пользователем, обновляем сообщение напрямую
        await query.edit_message_text(text=message, reply_markup=reply_markup)