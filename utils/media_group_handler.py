import asyncio
import logging
from typing import Dict, List
from aiogram.types import Message
from utils.message_storage import MessageStorage
from utils.message_sender import MessageSender
from utils.topic_manager import TopicManager

logger = logging.getLogger(__name__)

class MediaGroupHandler:
    """Класс для обработки медиагрупп (альбомов) через Redis"""
    
    def __init__(self):
        # Словарь для хранения временных данных медиагрупп
        # Ключ: media_group_id, Значение: {'messages': [], 'timer': asyncio.Task}
        self._media_groups: Dict[str, Dict] = {}
        self._timeout = 1.0  # Таймаут ожидания завершения медиагруппы в секундах
    
    async def handle_message(self, message: Message, chat_data, main_bot, is_from_user: bool = True):
        """
        Обработка сообщения, которое может быть частью медиагруппы
        
        Args:
            message: Сообщение
            chat_data: Данные чата
            main_bot: Главный бот
            is_from_user: True если от пользователя, False если от оператора
        """
        if not message.media_group_id:
            # Обычное сообщение, не часть медиагруппы
            await self._handle_single_message(message, chat_data, main_bot, is_from_user)
            return
        
        # Сообщение является частью медиагруппы
        media_group_id = message.media_group_id
        
        if media_group_id not in self._media_groups:
            # Создаем новую медиагруппу
            self._media_groups[media_group_id] = {
                'messages': [],
                'chat_data': chat_data,
                'main_bot': main_bot,
                'is_from_user': is_from_user,
                'timer': None
            }
        
        # Добавляем сообщение в медиагруппу
        self._media_groups[media_group_id]['messages'].append(message)
        
        # Отменяем предыдущий таймер если он был
        if self._media_groups[media_group_id]['timer']:
            self._media_groups[media_group_id]['timer'].cancel()
        
        # Создаем новый таймер
        self._media_groups[media_group_id]['timer'] = asyncio.create_task(
            self._process_media_group_after_timeout(media_group_id)
        )
        
        logger.debug(f"Добавлено сообщение в медиагруппу {media_group_id}, всего сообщений: {len(self._media_groups[media_group_id]['messages'])}")
    
    async def _handle_single_message(self, message: Message, chat_data, main_bot, is_from_user: bool):
        """Обработка одиночного сообщения"""
        try:
            if is_from_user:
                # Сообщение от пользователя в группу
                direction = "to_group"
                
                # Сохраняем сообщение в Redis
                message_id = await MessageStorage.save_message(message, chat_data, direction)
                if not message_id:
                    logger.error("Не удалось сохранить сообщение в Redis")
                    return
                
                # Получаем данные бота
                bot_data = chat_data.bot
                if not bot_data.group_id:
                    logger.warning(f"Бот {bot_data.id} не привязан к группе")
                    return
                
                # Убеждаемся, что тема существует
                topic_id = await TopicManager.ensure_topic_exists(main_bot, chat_data, bot_data.group_id)
                if not topic_id:
                    logger.error(f"Не удалось создать/найти тему для чата {chat_data.id}")
                    return
                
                chat_data.topic_id = topic_id
                
                # Отправляем информацию о пользователе
                await MessageSender.send_user_info_message(
                    main_bot, chat_data, bot_data.group_id, topic_id
                )
                
                # Отправляем сообщение из хранилища
                success = await MessageSender.send_message_from_storage(
                    main_bot, message_id, bot_data.group_id, topic_id
                )
                
                if success:
                    # Сохраняем в БД
                    await self._save_to_database(message, chat_data, from_user=True)
                    logger.info(f"Сообщение от пользователя {chat_data.user_id} успешно переслано в группу")
                else:
                    logger.error("Не удалось отправить сообщение в группу")
                
            else:
                # Сообщение от оператора пользователю
                direction = "to_user"
                
                # Сохраняем сообщение в Redis
                message_id = await MessageStorage.save_message(message, chat_data, direction)
                if not message_id:
                    logger.error("Не удалось сохранить сообщение в Redis")
                    return
                
                # Получаем бота пользователя
                from utils.bot_manager import bot_manager
                user_bot = await bot_manager.get_bot(chat_data.bot_id)
                if not user_bot:
                    logger.error("Бот пользователя недоступен")
                    return
                
                # Отправляем сообщение пользователю
                success = await MessageSender.send_message_from_storage(
                    user_bot, message_id, chat_data.user_id
                )
                
                if success:
                    # Сохраняем в БД
                    await self._save_to_database(message, chat_data, from_user=False)
                    logger.info(f"Сообщение оператора успешно переслано пользователю {chat_data.user_id}")
                else:
                    logger.error("Не удалось отправить сообщение пользователю")
                    
        except Exception as e:
            logger.error(f"Ошибка при обработке одиночного сообщения: {e}")
    
    async def _process_media_group_after_timeout(self, media_group_id: str):
        """Обработка медиагруппы после таймаута"""
        try:
            await asyncio.sleep(self._timeout)
            
            if media_group_id not in self._media_groups:
                return
            
            group_data = self._media_groups[media_group_id]
            messages = group_data['messages']
            chat_data = group_data['chat_data']
            main_bot = group_data['main_bot']
            is_from_user = group_data['is_from_user']
            
            logger.info(f"Обрабатываем медиагруппу {media_group_id} с {len(messages)} сообщениями")
            
            if is_from_user:
                # Медиагруппа от пользователя в группу
                await self._handle_media_group_to_group(messages, chat_data, main_bot, media_group_id)
            else:
                # Медиагруппа от оператора пользователю
                await self._handle_media_group_to_user(messages, chat_data, main_bot, media_group_id)
            
            # Удаляем обработанную медиагруппу
            del self._media_groups[media_group_id]
            
        except asyncio.CancelledError:
            # Таймер был отменен, это нормально
            pass
        except Exception as e:
            logger.error(f"Ошибка при обработке медиагруппы {media_group_id}: {e}")
            # Удаляем медиагруппу в случае ошибки
            if media_group_id in self._media_groups:
                del self._media_groups[media_group_id]
    
    async def _handle_media_group_to_group(self, messages: List[Message], chat_data, main_bot, media_group_id: str):
        """Обработка медиагруппы от пользователя в группу"""
        try:
            # Сохраняем медиагруппу в Redis
            message_ids = await MessageStorage.save_media_group(messages, chat_data, "to_group")
            if not message_ids:
                logger.error("Не удалось сохранить медиагруппу в Redis")
                return
            
            # Получаем данные бота
            bot_data = chat_data.bot
            if not bot_data.group_id:
                logger.warning(f"Бот {bot_data.id} не привязан к группе")
                return
            
            # Убеждаемся, что тема существует
            topic_id = await TopicManager.ensure_topic_exists(main_bot, chat_data, bot_data.group_id)
            if not topic_id:
                logger.error(f"Не удалось создать/найти тему для чата {chat_data.id}")
                return
            
            chat_data.topic_id = topic_id
            
            # Отправляем информацию о пользователе
            await MessageSender.send_user_info_message(
                main_bot, chat_data, bot_data.group_id, topic_id
            )
            
            # Отправляем медиагруппу из хранилища
            success = await MessageSender.send_media_group_from_storage(
                main_bot, media_group_id, bot_data.group_id, topic_id
            )
            
            if success:
                # Сохраняем в БД каждое сообщение
                for message in messages:
                    await self._save_to_database(message, chat_data, from_user=True)
                
                logger.info(f"Медиагруппа от пользователя {chat_data.user_id} успешно переслана в группу")
            else:
                logger.error("Не удалось отправить медиагруппу в группу")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке медиагруппы в группу: {e}")
    
    async def _handle_media_group_to_user(self, messages: List[Message], chat_data, main_bot, media_group_id: str):
        """Обработка медиагруппы от оператора пользователю"""
        try:
            # Сохраняем медиагруппу в Redis
            message_ids = await MessageStorage.save_media_group(messages, chat_data, "to_user")
            if not message_ids:
                logger.error("Не удалось сохранить медиагруппу в Redis")
                return
            
            # Получаем бота пользователя
            from utils.bot_manager import bot_manager
            user_bot = await bot_manager.get_bot(chat_data.bot_id)
            if not user_bot:
                logger.error("Бот пользователя недоступен")
                return
            
            # Отправляем медиагруппу пользователю
            success = await MessageSender.send_media_group_from_storage(
                user_bot, media_group_id, chat_data.user_id
            )
            
            if success:
                # Сохраняем в БД каждое сообщение
                for message in messages:
                    await self._save_to_database(message, chat_data, from_user=False)
                
                logger.info(f"Медиагруппа оператора успешно переслана пользователю {chat_data.user_id}")
            else:
                logger.error("Не удалось отправить медиагруппу пользователю")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке медиагруппы пользователю: {e}")
    
    async def _save_to_database(self, message: Message, chat_data, from_user: bool):
        """Сохранение сообщения в базу данных"""
        try:
            from database.database import async_session
            from database.queries import DatabaseQueries
            from utils.message_handler import MessageHandler
            
            async with async_session() as session:
                db = DatabaseQueries(session)
                await db.create_message(
                    chat_id=chat_data.id,
                    message_id=message.message_id,
                    from_user=from_user,
                    content=message.text or message.caption,
                    message_type=MessageHandler.get_message_type(message)
                )
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении в БД: {e}")

# Глобальный экземпляр обработчика медиагрупп
media_group_handler = MediaGroupHandler()