import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Импортируем функции из utils
from utils import (
    send_to_channel, 
    CHANNEL_ID, 
    load_content_file, 
    save_message_ids, 
    load_message_ids,
    clean_all_channel_messages,
    send_photo_to_channel
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы для путей
WELCOME_IMAGE_PATH = "media/images/photo.jpg"

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
    # Загружаем приветственное сообщение с выбором языка
    welcome_message = load_content_file("Telegram_content/welcome_message.md")
    
    # Создаем клавиатуру для выбора языка
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en_main"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es_main"),
        ],
        [
            InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de_main"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr_main"),
        ],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru_main"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Сбрасываем текущую страницу пользователя
    context.user_data['current_page'] = 'welcome'
    
    try:
        # Отправляем фото с текстом в подписи
        with open(WELCOME_IMAGE_PATH, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=welcome_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке изображения: {e}")
        # В случае ошибки отправляем обычное текстовое сообщение
        await update.message.reply_text(
            text=welcome_message,
            reply_markup=reply_markup
        )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора языка."""
    query = update.callback_query
    await query.answer()
    
    # Получаем выбранный язык и режим из данных колбэка
    callback_parts = query.data.split('_')
    language = callback_parts[1]
    mode = callback_parts[2] if len(callback_parts) > 2 else 'main'
    
    # Сохраняем выбранный язык в данных пользователя
    context.user_data['language'] = language
    
    # Определяем текущую страницу пользователя
    current_page = context.user_data.get('current_page', 'welcome')
    
    # Если режим 'current', сохраняем текущую страницу
    if mode == 'current':
        # Если мы находимся в подменю, остаемся на той же странице
        if current_page in ['properties', 'contact', 'faq', 'news']:
            # Отображаем соответствующую страницу на новом языке
            await show_submenu_page(query, context, current_page, language)
            return
    
    # В остальных случаях показываем главное меню
    await show_main_menu(query, context, language)

async def show_main_menu(query, context, language):
    """Показывает главное меню на выбранном языке с фотографией (унифицированный быстрый переход)"""
    menu_content = load_content_file(f"Telegram_content/{language}/main_menu.md")
    keyboard = create_menu_keyboard(language)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Обновляем текущую страницу
    context.user_data['current_page'] = 'main_menu'
    
    # Проверяем, является ли это сообщение сообщением канала
    is_channel = query.message.chat.type == 'channel' or (
        query.message.chat.username and CHANNEL_ID.replace("@", "") == query.message.chat.username
    )
    
    if is_channel:
        # УНИФИЦИРОВАННЫЙ ПОДХОД: Новое сообщение всегда с фото, отправка выполняется сразу, 
        # потом удаление старого для всех типов переходов
        message_ids = load_message_ids()
        message_key = f"main_menu_{language}"
        
        try:
            # Создаем и отправляем сообщение с изображением без уведомления
            with open(WELCOME_IMAGE_PATH, "rb") as photo_file:
                message = await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo_file,
                    caption=menu_content,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                    disable_notification=True  # Отключаем уведомления
                )
            
            # Сохраняем ID нового сообщения сразу
            message_ids[message_key] = message.message_id
            if "all_messages" not in message_ids:
                message_ids["all_messages"] = []
            if message.message_id not in message_ids["all_messages"]:
                message_ids["all_messages"].append(message.message_id)
            save_message_ids(message_ids)  # Важно сохранить до удаления старого
            
            # Теперь удаляем старое сообщение
            try:
                old_message_id = query.message.message_id
                if old_message_id != message.message_id:  # Проверка чтобы не удалять то же самое
                    await context.bot.delete_message(
                        chat_id=CHANNEL_ID,
                        message_id=old_message_id
                    )
                    
                    # Обновляем список всех сообщений
                    if old_message_id in message_ids["all_messages"]:
                        message_ids["all_messages"].remove(old_message_id)
                    save_message_ids(message_ids)
            except Exception as e:
                logger.error(f"Ошибка при удалении старого сообщения: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке фото в канал: {e}")
            # Резервный вариант с обычным сообщением
            message = await send_to_channel(context, menu_content, reply_markup, message_key)
            
    else:
        # Это личный чат с пользователем
        try:
            # Отправляем новое сообщение с фото и удаляем старое
            with open(WELCOME_IMAGE_PATH, "rb") as photo:
                new_message = await query.message.reply_photo(
                    photo=photo,
                    caption=menu_content,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            # Удаляем предыдущее сообщение ПОСЛЕ отправки нового
            await query.message.delete()
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения в чате: {e}")
            try:
                await query.edit_message_text(
                    text=menu_content,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            except Exception:
                await query.message.reply_text(
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
    
    # Обновляем текущую страницу пользователя
    context.user_data['current_page'] = menu_item
    
    # Показываем соответствующую страницу
    await show_submenu_page(query, context, menu_item, language)

async def show_submenu_page(query, context, page, language):
    """Показывает подменю на выбранном языке (унифицированный быстрый переход)"""
    
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
    
    # Используем тот же lang_{language}_main для совместимости
    keyboard = [[InlineKeyboardButton(back_button_text.get(language, "🔙 Back"), callback_data=f"lang_{language}_main")]]
    
    # Добавляем языковые кнопки внизу
    keyboard.extend(create_language_buttons())
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Создаем уникальный ключ для этого типа сообщения
    message_key = f"{page}_{language}"
    
    # Проверяем, является ли это сообщение сообщением канала
    is_channel = query.message.chat.type == 'channel' or (
        query.message.chat.username and CHANNEL_ID.replace("@", "") == query.message.chat.username
    )
    
    if is_channel:
        # УНИФИЦИРОВАННЫЙ ПОДХОД: Быстро отправляем новое, потом удаляем старое
        message_ids = load_message_ids()
        
        # 1. Сначала создаем и отправляем новое сообщение без уведомления
        new_message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_notification=True  # Важно: отключаем уведомления всегда
        )
        
        # 2. Сразу сохраняем ID нового сообщения в структуру, чтобы оно не было удалено случайно
        message_ids[message_key] = new_message.message_id
        if "all_messages" not in message_ids:
            message_ids["all_messages"] = []
        if new_message.message_id not in message_ids["all_messages"]:
            message_ids["all_messages"].append(new_message.message_id)
        save_message_ids(message_ids)  # Важно сохранить до удаления старого
        
        # 3. Теперь можно удалить старое сообщение
        old_message_id = query.message.message_id
        if old_message_id != new_message.message_id:  # Проверка чтобы не удалять то же самое
            try:
                await context.bot.delete_message(
                    chat_id=CHANNEL_ID,
                    message_id=old_message_id
                )
                
                # Обновляем список всех сообщений после успешного удаления
                if old_message_id in message_ids["all_messages"]:
                    message_ids["all_messages"].remove(old_message_id)
                    save_message_ids(message_ids)
            except Exception as e:
                logger.error(f"Ошибка при удалении старого сообщения: {e}")
    else:
        # Это личный чат с пользователем - используем edit_message_text
        try:
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения: {e}")
            # Запасной вариант
            await query.message.reply_text(
                text=message, 
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )