import asyncio
from asyncio.events import BaseDefaultEventLoopPolicy
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from fluentogram import TranslatorHub, TranslatorRunner

import middlewares
from utils import TranslatorHub, create_translator_hub
from middlewares import TranslatorRunnerMiddleware, BlacklistMiddleware
from handlers import (main_router, devices_router, payment_router, 
                      admin_router, another_router, unknown_router)
from config import get_config, BotConfig
from services.services import on_startup


logger = logging.getLogger(__name__)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s'
    )
    logger.info('Starting Bot')

    # Init Bot in Dispatcher
    bot_config = get_config(BotConfig, "bot")
    
    if not bot_config.token:
        logger.error("Bot token is missing in the configuration.")
        return
    
    bot = Bot(token=bot_config.token.get_secret_value(),
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # i18n init
    translator_hub: TranslatorHub = create_translator_hub()

    # Routers, dialogs, middlewares
    dp.include_routers(main_router, devices_router, payment_router, admin_router, another_router, unknown_router)
    dp.update.middleware(TranslatorRunnerMiddleware())
    dp.message.middleware(BlacklistMiddleware())
    dp.callback_query.middleware(BlacklistMiddleware())
    dp.startup.register(on_startup)
 
    # Skipping old updates
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted, ready for polling.")
    
    await dp.start_polling(bot, _translator_hub=translator_hub)
    return bot

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error while starting bot: {e}")
