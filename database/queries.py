from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .models import ConnectedBot, Chat, Message, BannedUser

class DatabaseQueries:
    def __init__(self, session: AsyncSession):
        self.session = session

    # Методы для работы с подключенными ботами
    async def create_connected_bot(self, user_id: int, bot_token: str, 
                                   bot_username: str, bot_id: int) -> ConnectedBot:
        """Создание нового подключенного бота"""
        bot = ConnectedBot(
            user_id=user_id,
            bot_token=bot_token,
            bot_username=bot_username,
            bot_id=bot_id
        )
        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        return bot

    async def get_connected_bot_by_token(self, bot_token: str) -> Optional[ConnectedBot]:
        """Получение бота по токену"""
        result = await self.session.execute(
            select(ConnectedBot).where(ConnectedBot.bot_token == bot_token)
        )
        return result.scalar_one_or_none()

    async def get_connected_bot_by_id(self, bot_id: int) -> Optional[ConnectedBot]:
        """Получение бота по bot_id"""
        result = await self.session.execute(
            select(ConnectedBot).where(ConnectedBot.bot_id == bot_id)
        )
        return result.scalar_one_or_none()

    async def get_user_bots(self, user_id: int) -> List[ConnectedBot]:
        """Получение всех ботов пользователя"""
        result = await self.session.execute(
            select(ConnectedBot).where(
                ConnectedBot.user_id == user_id,
                ConnectedBot.is_active == True
            )
        )
        return result.scalars().all()

    async def update_bot_group(self, bot_id: int, group_id: int):
        """Обновление группы бота"""
        await self.session.execute(
            update(ConnectedBot)
            .where(ConnectedBot.id == bot_id)
            .values(group_id=group_id)
        )
        await self.session.commit()

    async def update_bot_settings(self, bot_id: int, **kwargs):
        """Обновление настроек бота"""
        await self.session.execute(
            update(ConnectedBot)
            .where(ConnectedBot.id == bot_id)
            .values(**kwargs)
        )
        await self.session.commit()

    async def deactivate_bot(self, bot_id: int):
        """Деактивация бота"""
        await self.session.execute(
            update(ConnectedBot)
            .where(ConnectedBot.id == bot_id)
            .values(is_active=False)
        )
        await self.session.commit()

    async def delete_bot(self, bot_id: int):
        """Удаление бота"""
        await self.session.execute(
            delete(ConnectedBot).where(ConnectedBot.id == bot_id)
        )
        await self.session.commit()

    # Методы для работы с чатами
    async def create_chat(self, bot_id: int, user_id: int, username: str = None,
                         first_name: str = None, last_name: str = None) -> Chat:
        """Создание нового чата"""
        from config import config
        
        chat = Chat(
            bot_id=bot_id,
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            status=config.STATUS_WAITING  # Устанавливаем начальный статус
        )
        self.session.add(chat)
        await self.session.commit()
        await self.session.refresh(chat)
        return chat

    async def get_chat(self, bot_id: int, user_id: int) -> Optional[Chat]:
        """Получение чата"""
        result = await self.session.execute(
            select(Chat).where(
                Chat.bot_id == bot_id,
                Chat.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_chat_by_topic(self, topic_id: int) -> Optional[Chat]:
        """Получение чата по ID темы"""
        result = await self.session.execute(
            select(Chat).where(Chat.topic_id == topic_id)
        )
        return result.scalar_one_or_none()

    async def update_chat_topic(self, chat_id: int, topic_id: int):
        """Обновление ID темы чата"""
        await self.session.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(topic_id=topic_id)
        )
        await self.session.commit()

    async def update_chat_status(self, chat_id: int, status: str):
        """Обновление статуса чата"""
        await self.session.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(status=status)
        )
        await self.session.commit()

    # Методы для работы с сообщениями
    async def create_message(self, chat_id: int, message_id: int, from_user: bool,
                           content: str = None, message_type: str = 'text') -> Message:
        """Создание нового сообщения"""
        message = Message(
            chat_id=chat_id,
            message_id=message_id,
            from_user=from_user,
            content=content,
            message_type=message_type
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    # Методы для работы с банами
    async def ban_user(self, bot_id: int, user_id: int):
        """Бан пользователя"""
        ban = BannedUser(bot_id=bot_id, user_id=user_id)
        self.session.add(ban)
        await self.session.commit()

    async def is_user_banned(self, bot_id: int, user_id: int) -> bool:
        """Проверка, забанен ли пользователь"""
        result = await self.session.execute(
            select(BannedUser).where(
                BannedUser.bot_id == bot_id,
                BannedUser.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def unban_user(self, bot_id: int, user_id: int):
        """Разбан пользователя"""
        await self.session.execute(
            delete(BannedUser).where(
                BannedUser.bot_id == bot_id,
                BannedUser.user_id == user_id
            )
        )
        await self.session.commit()
