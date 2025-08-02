from database.database import async_session
from database.queries import DatabaseQueries
from database.models import Chat
from utils.topic_manager import TopicManager
from config import config
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class StatusManager:
    @staticmethod
    async def update_status(chat_id: int, new_status: str, group_bot=None):
        """Обновление статуса чата"""
        async with async_session() as session:
            db = DatabaseQueries(session)
            
            # Log the status update
            stmt = select(Chat).where(Chat.id == chat_id)
            result = await session.execute(stmt)
            chat_data = result.scalar_one_or_none()
            old_status = chat_data.status if chat_data else "Unknown"
            logger.info(f"Status update for chat {chat_id}: {old_status} -> {new_status}")
            

            stmt = select(Chat).options(selectinload(Chat.bot)).where(Chat.id == chat_id)
            result = await session.execute(stmt)
            chat_data = result.scalar_one_or_none()
            
            if not chat_data:
                logger.warning(f"Чат с ID {chat_id} не найден")
                return
            

            await db.update_chat_status(chat_id, new_status)
            

            chat_data.status = new_status
            

            if group_bot and chat_data.bot and chat_data.bot.group_id and chat_data.topic_id:
                try:
                    # Update topic name for all relevant statuses
                    if new_status in [config.STATUS_WAITING, config.STATUS_ANSWERED, config.STATUS_HOLD, config.STATUS_BANNED, config.STATUS_ENDED]:
                        await TopicManager.update_topic_name(group_bot, chat_data, chat_data.bot.group_id)
                    else:
                        logger.info(f"Preserving topic name for status {new_status}")
                except Exception as e:
                    logger.error(f"Ошибка при обновлении названия темы: {e}")

    @staticmethod
    def get_status_emoji(status: str) -> str:
        """Получение эмодзи для статуса"""
        return config.STATUS_EMOJIS.get(status, '⏳')
