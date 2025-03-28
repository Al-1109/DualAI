import os
import logging
import time
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

# Импорт ID администраторов
from handlers.admin import ADMIN_IDS

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
def create_menu_keyboard(language, is_admin=False):
    """
    Создает клавиатуру для главного меню на нужном языке.
    Добавляет административные кнопки, если пользователь является администратором.
    
    Args:
        language (str): Код языка ('en', 'ru', 'es', 'de', 'fr')
        is_admin (bool): Флаг, указывающий, является ли пользователь администратором
    """
    # Базовые кнопки меню для разных языков
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
    
    # Добавляем административные кнопки для администраторов
    if is_admin:
        admin_button_text = {
            'en': "⚙️ Admin Panel",
            'es': "⚙️ Panel de Administración",
            'de': "⚙️ Admin-Panel",
            'fr': "⚙️ Panneau d'Administration",
            'ru': "⚙️ Панель Администратора"
        }
        
        # Добавляем кнопку админ-панели
        keyboard.append([InlineKeyboardButton(
            admin_button_text.get(language, "⚙️ Admin Panel"), 
            callback_data="admin_panel"
        )])
    
    # Добавляем языковые кнопки в нижнюю часть меню
    keyboard.extend(create_language_buttons())
    
    return keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start с поддержкой параметра языка.
    Учитывает переход из канала с выбранным языком.
    """
    # Проверяем, передан ли параметр языка (например, /start lang_ru)
    args = context.args
    language = 'en'  # Язык по умолчанию
    
    if args and args[0].startswith('lang_'):
        # Извлекаем код языка из параметра
        language = args[0].split('_')[1]  # например, 'ru' из 'lang_ru'
        # Сохраняем выбранный язык в данных пользователя
        context.user_data['language'] = language
        logger.info(f"Пользователь выбрал язык: {language} через параметр /start")
    else:
        # Если язык не передан, используем сохраненный или английский по умолчанию
        language = context.user_data.get('language', 'en')
    
    # Получаем ID пользователя для проверки админских прав
    user_id = update.effective_user.id
    
    # Проверяем, является ли пользователь администратором
    is_admin = user_id in ADMIN_IDS
    
    # Сохраняем статус администратора в данных пользователя
    context.user_data['is_admin'] = is_admin
    
    # Устанавливаем режим работы (по умолчанию 'production')
    if 'environment' not in context.user_data:
        context.user_data['environment'] = 'production'
    
    # Загружаем главное меню на выбранном языке
    menu_content = load_content_file(f"Telegram_content/{language}/main_menu.md")
    keyboard = create_menu_keyboard(language, is_admin)
    
    # Обновляем текущую страницу пользователя
    context.user_data['current_page'] = 'main_menu'
    
    try:
        # Отправляем фото с текстом в подписи
        with open(WELCOME_IMAGE_PATH, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=menu_content,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке изображения: {e}")
        # В случае ошибки отправляем обычное текстовое сообщение
        await update.message.reply_text(
            text=menu_content,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def send_welcome_to_channel(context):
    """
    Отправка приветственного сообщения с кнопками перехода к боту на разных языках.
    Это сообщение будет закреплено в канале.
    """
    logger.info("Отправляем приветственное сообщение с кнопками перехода к боту...")
    welcome_message = load_content_file("Telegram_content/welcome_message.md")
    
    # Получаем имя бота из контекста
    bot_username = context.bot.username
    
    # Создаем кнопки перехода к боту с выбором языка
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 Start in English", url=f"https://t.me/{bot_username}?start=lang_en"),
            InlineKeyboardButton("🇪🇸 Comenzar en Español", url=f"https://t.me/{bot_username}?start=lang_es"),
        ],
        [
            InlineKeyboardButton("🇩🇪 Auf Deutsch starten", url=f"https://t.me/{bot_username}?start=lang_de"),
            InlineKeyboardButton("🇫🇷 Commencer en Français", url=f"https://t.me/{bot_username}?start=lang_fr"),
        ],
        [
            InlineKeyboardButton("🇷🇺 Начать на русском", url=f"https://t.me/{bot_username}?start=lang_ru"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Получаем текущие сообщения
    message_ids = load_message_ids()
    pinned_message_id = message_ids.get("pinned_welcome")
    
    try:
        # Проверяем, существует ли уже закрепленное сообщение
        if pinned_message_id:
            try:
                # Пытаемся редактировать существующее сообщение
                if "welcome_has_photo" in message_ids and message_ids["welcome_has_photo"]:
                    # Если у нас есть фото, то редактируем подпись
                    await context.bot.edit_message_caption(
                        chat_id=CHANNEL_ID,
                        message_id=pinned_message_id,
                        caption=welcome_message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Обновлено закрепленное сообщение с ID: {pinned_message_id}")
                    return pinned_message_id
                else:
                    # Если нет фото, редактируем текст
                    await context.bot.edit_message_text(
                        chat_id=CHANNEL_ID,
                        message_id=pinned_message_id,
                        text=welcome_message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Обновлено закрепленное сообщение с ID: {pinned_message_id}")
                    return pinned_message_id
            except Exception as e:
                logger.error(f"Не удалось отредактировать закрепленное сообщение: {e}")
                # Продолжаем и создаем новое сообщение
        
        # Отправляем новое сообщение с изображением
        try:
            with open(WELCOME_IMAGE_PATH, "rb") as photo:
                message = await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo,
                    caption=welcome_message,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                    disable_notification=True
                )
                
                # Отмечаем, что сообщение содержит фото
                message_ids["welcome_has_photo"] = True
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            # Если не удалось отправить изображение, отправляем обычное текстовое сообщение
            message = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=welcome_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
                disable_notification=True
            )
            message_ids["welcome_has_photo"] = False
        
        # Закрепляем сообщение
        await context.bot.pin_chat_message(
            chat_id=CHANNEL_ID,
            message_id=message.message_id,
            disable_notification=True
        )
        
        # Сохраняем ID нового сообщения
        message_ids["pinned_welcome"] = message.message_id
        
        # Добавляем в список всех сообщений
        if "all_messages" not in message_ids:
            message_ids["all_messages"] = []
        
        if message.message_id not in message_ids["all_messages"]:
            message_ids["all_messages"].append(message.message_id)
        
        save_message_ids(message_ids)
        
        # Удаляем все другие сообщения канала, кроме закрепленного
        # Но только если это новый pin, а не обновление существующего
        if not pinned_message_id or pinned_message_id != message.message_id:
            await clean_all_channel_messages(context, message.message_id, True)
        
        logger.info(f"Отправлено и закреплено приветственное сообщение (ID: {message.message_id})")
        return message.message_id
            
    except Exception as e:
        logger.error(f"Ошибка при работе с приветственным сообщением: {e}")
        return None

# НОВАЯ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ДЛЯ ВСЕХ ТИПОВ ПЕРЕХОДОВ
async def send_menu_update(context, chat_id, old_message_id, content, keyboard, message_key, use_photo=False):
    """
    Функция перехода без мерцания для Android и других клиентов.
    Использует метод "сначала отправить, потом удалить" с минимальными задержками.
    
    Args:
        context: Контекст бота
        chat_id: ID чата/канала
        old_message_id: ID старого сообщения для удаления
        content: Содержимое нового сообщения
        keyboard: Клавиатура для нового сообщения
        message_key: Ключ для сохранения ID сообщения
        use_photo: Использовать фото (True) или только текст (False)
    """
    message_ids = load_message_ids()
    reply_markup = InlineKeyboardMarkup(keyboard)
    new_message = None
    
    try:
        # 1. СНАЧАЛА отправляем новое сообщение
        if use_photo:
            with open(WELCOME_IMAGE_PATH, "rb") as photo_file:
                new_message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=content,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                    disable_notification=True
                )
        else:
            new_message = await context.bot.send_message(
                chat_id=chat_id,
                text=content,
                reply_markup=reply_markup,
                parse_mode="Markdown",
                disable_notification=True
            )
        
        # 2. Сразу сохраняем ID нового сообщения
        if new_message:
            new_message_id = new_message.message_id
            message_ids[message_key] = new_message_id
            
            if "all_messages" not in message_ids:
                message_ids["all_messages"] = []
            
            if new_message_id not in message_ids["all_messages"]:
                message_ids["all_messages"].append(new_message_id)
            
            # Сохраняем обновленную структуру до удаления
            save_message_ids(message_ids)
        
        # 3. ТОЛЬКО ПОСЛЕ этого удаляем старое сообщение
        if old_message_id and new_message and old_message_id != new_message.message_id:
            try:
                # Пытаемся удалить старое сообщение
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=old_message_id
                )
                
                # Обновляем структуру после удаления
                if old_message_id in message_ids.get("all_messages", []):
                    message_ids["all_messages"].remove(old_message_id)
                    save_message_ids(message_ids)
            except Exception as e:
                # Просто логируем ошибку, не прерывая работу
                logger.error(f"Ошибка при удалении сообщения {old_message_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении меню: {e}")
    
    return new_message

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора языка."""
    query = update.callback_query
    await query.answer()  # Мгновенно отвечаем, чтобы убрать спиннер
    
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
    """Показывает главное меню на выбранном языке с фотографией."""
    # Загружаем контент для главного меню
    menu_content = load_content_file(f"Telegram_content/{language}/main_menu.md")
    
    # Проверяем, является ли пользователь администратором
    is_admin = context.user_data.get('is_admin', False)
    
    keyboard = create_menu_keyboard(language, is_admin)
    
    # Обновляем текущую страницу
    context.user_data['current_page'] = 'main_menu'
    
    # Проверяем, является ли это сообщение сообщением канала
    is_channel = query.message.chat.type == 'channel' or (
        query.message.chat.username and CHANNEL_ID.replace("@", "") == query.message.chat.username
    )
    
    if is_channel:
        # Для канала используем универсальную функцию с фото
        message_key = f"main_menu_{language}"
        chat_id = CHANNEL_ID
        old_message_id = query.message.message_id
        
        # Используем универсальную функцию (всегда с фото для главного меню)
        await send_menu_update(
            context=context,
            chat_id=chat_id,
            old_message_id=old_message_id,
            content=menu_content,
            keyboard=keyboard,
            message_key=message_key,
            use_photo=True  # Главное меню всегда с фото
        )
    else:
        # Это личный чат с пользователем
        try:
            # Отправляем новое сообщение с фото и удаляем старое
            with open(WELCOME_IMAGE_PATH, "rb") as photo:
                new_message = await query.message.reply_photo(
                    photo=photo,
                    caption=menu_content,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            # Удаляем предыдущее сообщение после отправки нового
            await query.message.delete()
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения в чате: {e}")
            try:
                await query.edit_message_text(
                    text=menu_content,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            except Exception:
                await query.message.reply_text(
                    text=menu_content,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора пункта меню."""
    query = update.callback_query
    await query.answer()  # Мгновенно отвечаем, чтобы убрать спиннер
    
    # Получаем выбранный пункт меню и язык пользователя
    menu_item = query.data.split('_')[1]
    language = context.user_data.get('language', 'en')
    
    # Обновляем текущую страницу пользователя
    context.user_data['current_page'] = menu_item
    
    # Показываем соответствующую страницу
    await show_submenu_page(query, context, menu_item, language)

async def show_submenu_page(query, context, page, language):
    """Показывает подменю на выбранном языке."""
    
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
    
    # Создаем уникальный ключ для этого типа сообщения
    message_key = f"{page}_{language}"
    
    # Проверяем, является ли это сообщение сообщением канала
    is_channel = query.message.chat.type == 'channel' or (
        query.message.chat.username and CHANNEL_ID.replace("@", "") == query.message.chat.username
    )
    
    if is_channel:
        # Для канала используем универсальную функцию без фото
        chat_id = CHANNEL_ID
        old_message_id = query.message.message_id
        
        # Используем универсальную функцию (без фото для подменю)
        await send_menu_update(
            context=context,
            chat_id=chat_id,
            old_message_id=old_message_id,
            content=message,
            keyboard=keyboard,
            message_key=message_key,
            use_photo=False  # Подменю всегда без фото
        )
    else:
        # Это личный чат с пользователем - используем edit_message_text
        try:
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения: {e}")
            # Запасной вариант
            await query.message.reply_text(
                text=message, 
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )