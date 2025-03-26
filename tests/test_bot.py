import pytest
from unittest.mock import AsyncMock, patch
from src.bot import handle_message, unknown_command
from src.handlers.client import start_command, language_callback, menu_callback

@pytest.mark.asyncio
async def test_unknown_command():
    """Тест обработки неизвестных команд"""
    update = AsyncMock()
    context = AsyncMock()
    
    await unknown_command(update, context)
    update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_message():
    """Тест обработки текстовых сообщений"""
    update = AsyncMock()
    context = AsyncMock()
    
    await handle_message(update, context)
    update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_start_command():
    """Тест команды /start"""
    update = AsyncMock()
    context = AsyncMock()
    
    await start_command(update, context)
    update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_language_callback():
    """Тест обработки выбора языка"""
    update = AsyncMock()
    context = AsyncMock()
    update.callback_query.data = "lang_en_main"
    
    await language_callback(update, context)
    update.callback_query.answer.assert_called_once()

@pytest.mark.asyncio
async def test_menu_callback():
    """Тест обработки выбора пункта меню"""
    update = AsyncMock()
    context = AsyncMock()
    update.callback_query.data = "menu_properties"
    
    await menu_callback(update, context)
    update.callback_query.answer.assert_called_once() 