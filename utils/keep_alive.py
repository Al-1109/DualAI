import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Bot

logger = logging.getLogger(__name__)

async def keep_alive():
    """Поддерживает активность бота, отправляя периодические запросы."""
    bot_token = os.getenv("TEST_TELEGRAM_BOT_TOKEN") if os.getenv("VERCEL_ENV") == "preview" else os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Bot token not configured")
        return

    bot = Bot(token=bot_token)
    last_activity = datetime.now()

    while True:
        try:
            # Проверяем, прошло ли 5 минут с последней активности
            if datetime.now() - last_activity > timedelta(minutes=5):
                # Отправляем запрос getMe для поддержания активности
                await bot.get_me()
                last_activity = datetime.now()
                logger.info("Keep-alive request sent")
            
            # Ждем 1 минуту перед следующей проверкой
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error in keep-alive: {e}")
            await asyncio.sleep(60)  # Ждем минуту перед повторной попыткой 