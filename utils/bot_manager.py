import asyncio
import logging
from typing import Dict, Optional
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from database.database import async_session
from database.queries import DatabaseQueries
from database.models import ConnectedBot
from handlers.connected_bot_handlers import ConnectedBotHandlers
from sqlalchemy.future import select
from aiogram.fsm.storage.redis import RedisStorage
from config import config

logger = logging.getLogger(__name__)


class BotManager:
    def __init__(self):
        self.connected_bots: Dict[int, Bot] = {}
        self.bot_dispatchers: Dict[int, Dispatcher] = {}
        self.bot_tasks: Dict[int, asyncio.Task] = {}

    async def add_bot(self, bot_data) -> Optional[Bot]:
        try:
            bot = Bot(
                token=bot_data.bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
            )

            await bot.get_me()
            storage = RedisStorage.from_url(config.REDIS_URL)
            dp = Dispatcher(storage=storage)

            router = ConnectedBotHandlers.create_handlers(bot_data.id)
            dp.include_router(router)

            self.connected_bots[bot_data.id] = bot
            self.bot_dispatchers[bot_data.id] = dp

            task = asyncio.create_task(dp.start_polling(bot))
            self.bot_tasks[bot_data.id] = task

            return bot

        except Exception as e:
            logger.error(f"Ошибка при добавлении бота: {e}")
            return None

    async def remove_bot(self, bot_id: int):
        await self.stop_bot(bot_id)

    async def get_bot(self, bot_id: int) -> Optional[Bot]:
        return self.connected_bots.get(bot_id)

    async def stop_bot(self, bot_id: int):
        """Правильная мягкая остановка бота"""
        if bot_id not in self.bot_dispatchers:
            logger.warning(f"Dispatcher для бота {bot_id} не найден")
            return

        dp = self.bot_dispatchers[bot_id]

        if bot_id in self.bot_tasks:
            await dp.stop_polling()
            await self.bot_tasks[bot_id]
            logger.info(f"Polling задача для бота {bot_id} завершена")
            del self.bot_tasks[bot_id]

        await dp.storage.close()
        logger.info(f"FSM storage для бота {bot_id} закрыт")

        if bot_id in self.connected_bots:
            del self.connected_bots[bot_id]
        if bot_id in self.bot_dispatchers:
            del self.bot_dispatchers[bot_id]

        logger.info(f"Бот {bot_id} удалён из менеджера")

    async def start_bot(self, bot_id: int):
        """Запуск бота заново"""
        async with async_session() as session:
            db = DatabaseQueries(session)
            stmt = select(ConnectedBot).where(ConnectedBot.id == bot_id)
            result = await session.execute(stmt)
            bot_data = result.scalars().first()

            if not bot_data:
                logger.error(f"Бот {bot_id} не найден")
                return

            if bot_id not in self.connected_bots:
                bot = Bot(
                    token=bot_data.bot_token,
                    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
                )
                await bot.get_me()
                storage = RedisStorage.from_url(config.REDIS_URL)
                dp = Dispatcher(storage=storage)
                router = ConnectedBotHandlers.create_handlers(bot_data.id)
                dp.include_router(router)
                self.connected_bots[bot_id] = bot
                self.bot_dispatchers[bot_id] = dp
                logger.info(f"Бот {bot_id} восстановлен")

            if bot_id in self.bot_tasks:
                logger.info(f"Останавливаю старую задачу для бота {bot_id}")
                self.bot_tasks[bot_id].cancel()
                try:
                    await self.bot_tasks[bot_id]
                except asyncio.CancelledError:
                    pass
                await self.bot_tasks.pop(bot_id, None)

            # Закрываем старую сессию если вдруг осталась
            bot = self.connected_bots[bot_id]
            if hasattr(bot, 'session') and hasattr(bot.session, 'client_session'):
                if not bot.session.client_session.closed:
                    await bot.session.client_session.close()

            # Создаем новую задачу polling
            dp = self.bot_dispatchers[bot_id]
            task = asyncio.create_task(dp.start_polling(bot, skip_updates=True))
            self.bot_tasks[bot_id] = task
            logger.info(f"Polling для бота {bot_id} запущен")

    async def load_existing_bots(self):
        async with async_session() as session:
            db = DatabaseQueries(session)
            stmt = select(ConnectedBot).where(ConnectedBot.is_active == True)
            result = await session.execute(stmt)
            bots = result.scalars().all()

            for bot in bots:
                await self.add_bot(bot)


bot_manager = BotManager()
