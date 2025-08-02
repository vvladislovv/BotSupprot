import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config import config
from database.database import init_db, drop_db
from handlers.main_bot import router as main_router
from handlers.operator import router as operator_router
from middlewares.language import LanguageMiddleware
from utils.bot_manager import bot_manager
from utils.redis_manager import redis_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    # Подключаемся к Redis
    await redis_manager.connect()

    await drop_db()
    await init_db()

    main_bot = Bot(
        token=config.MAIN_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
    )
    
    # Используем Redis для хранения состояний FSM
    storage = RedisStorage.from_url(config.REDIS_URL)
    dp = Dispatcher(storage=storage)
    

    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())
    

    dp.include_router(main_router)
    dp.include_router(operator_router)
    

    await bot_manager.load_existing_bots()
    

    bot_manager.connected_bots[0] = main_bot
    
    logging.info("Бот запущен")
    
    try:

        await dp.start_polling(main_bot, skip_updates=True)
    finally:
        # Закрываем соединения
        await main_bot.session.close()
        await redis_manager.disconnect()
        await storage.close()
        

        for task in bot_manager.bot_tasks.values():
            task.cancel()
        
        for bot in bot_manager.connected_bots.values():
            if bot != main_bot:
                await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())