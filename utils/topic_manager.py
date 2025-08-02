
import asyncio
import logging
from typing import Dict, Optional
from aiogram import Bot
from database.database import async_session
from database.queries import DatabaseQueries
from config import config

logger = logging.getLogger(__name__)

class TopicManager:
    """Класс для управления темами в супергруппах"""
    
    # Кэш информации о темах {chat_id: topic_info}
    _topic_cache: Dict[int, Dict] = {}
    
    # Очередь обновлений тем для батчевой обработки
    _update_queue: Dict[int, Dict] = {}
    
    # Флаг для предотвращения множественных обновлений
    _update_in_progress = False
    
    @classmethod
    async def create_topic(cls, bot: Bot, group_id: int, chat_data) -> Optional[int]:
        """
        Создание новой темы для чата
        
        Args:
            bot: Экземпляр бота
            group_id: ID группы
            chat_data: Данные чата
            
        Returns:
            ID созданной темы или None в случае ошибки
        """
        try:
            topic_name = cls._generate_topic_name(chat_data)
            
            # Создаем тему
            topic = await bot.create_forum_topic(
                chat_id=group_id,
                name=topic_name
            )
            
            topic_id = topic.message_thread_id
            
            # Обновляем в БД
            async with async_session() as session:
                db = DatabaseQueries(session)
                await db.update_chat_topic(chat_data.id, topic_id)
            
            # Кэшируем информацию о теме
            cls._topic_cache[chat_data.id] = {
                'topic_id': topic_id,
                'name': topic_name,
                'group_id': group_id,
                'status': chat_data.status
            }
            
            logger.info(f"Создана тема {topic_id} для чата {chat_data.id}")
            return topic_id
            
        except Exception as e:
            logger.error(f"Ошибка при создании темы: {e}")
            return None
    
    @classmethod
    async def update_topic_name(cls, bot: Bot, chat_data, group_id: int):
        """
        Обновление названия темы (с батчевой обработкой)
        
        Args:
            bot: Экземпляр бота
            chat_data: Данные чата
            group_id: ID группы
        """
        if not chat_data.topic_id:
            logger.debug(f"Тема не создана для чата {chat_data.id}, пропускаем обновление")
            return
        
        try:
            new_name = cls._generate_topic_name(chat_data)
            
            # Проверяем кэш - нужно ли обновление
            cached_info = cls._topic_cache.get(chat_data.id)
            if cached_info and cached_info.get('name') == new_name:
                logger.debug(f"Название темы {chat_data.topic_id} не изменилось: {new_name}")
                return  # Название не изменилось
            
            # Проверяем, что тема существует
            try:
                # Пытаемся получить информацию о теме
                await bot.get_chat(group_id)  # Проверяем доступ к группе
            except Exception as e:
                logger.error(f"Нет доступа к группе {group_id}: {e}")
                return
            
            # Добавляем в очередь обновлений
            cls._update_queue[chat_data.id] = {
                'topic_id': chat_data.topic_id,
                'new_name': new_name,
                'group_id': group_id,
                'bot': bot
            }
            
            # Обновляем кэш
            cls._topic_cache[chat_data.id] = {
                'topic_id': chat_data.topic_id,
                'name': new_name,
                'group_id': group_id,
                'status': chat_data.status
            }
            
            logger.debug(f"Запланировано обновление темы {chat_data.topic_id} на: {new_name}")
            
            # Запускаем батчевое обновление
            if not cls._update_in_progress:
                asyncio.create_task(cls._process_topic_updates())
                
        except Exception as e:
            logger.error(f"Ошибка при подготовке обновления темы: {e}")
    
    @classmethod
    async def _process_topic_updates(cls):
        """Батчевая обработка обновлений тем"""
        if cls._update_in_progress:
            return
        
        cls._update_in_progress = True
        
        try:
            # Ждем немного, чтобы собрать больше обновлений
            await asyncio.sleep(1)
            
            # Обрабатываем все накопленные обновления
            updates_to_process = dict(cls._update_queue)
            cls._update_queue.clear()
            
            for chat_id, update_info in updates_to_process.items():
                try:
                    await update_info['bot'].edit_forum_topic(
                        chat_id=update_info['group_id'],
                        message_thread_id=update_info['topic_id'],
                        name=update_info['new_name'],

                    )
                    
                    logger.debug(f"Обновлено название темы {update_info['topic_id']}: {update_info['new_name']}")
                    
                except Exception as e:
                    logger.error(f"Ошибка при обновлении темы {update_info['topic_id']}: {e}")
                
                # Небольшая задержка между обновлениями
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Ошибка при батчевом обновлении тем: {e}")
        finally:
            cls._update_in_progress = False
    
    @classmethod
    def _generate_topic_name(cls, chat_data) -> str:
        """
        Генерация названия темы
        
        Args:
            chat_data: Данные чата
            
        Returns:
            Название темы
        """
        name = chat_data.first_name or "Пользователь"
        if chat_data.username:
            name += f" (@{chat_data.username})"
        
        emoji = config.STATUS_EMOJIS.get(chat_data.status, '⏳')
        return f"{emoji} {name}"
    
    @classmethod
    def get_cached_topic_info(cls, chat_id: int) -> Optional[Dict]:
        """
        Получение кэшированной информации о теме
        
        Args:
            chat_id: ID чата
            
        Returns:
            Информация о теме или None
        """
        return cls._topic_cache.get(chat_id)
    
    @classmethod
    def clear_cache(cls, chat_id: Optional[int] = None):
        """
        Очистка кэша тем
        
        Args:
            chat_id: ID чата для очистки (если None - очищает весь кэш)
        """
        if chat_id:
            cls._topic_cache.pop(chat_id, None)
        else:
            cls._topic_cache.clear()
    
    @classmethod
    async def ensure_topic_exists(cls, bot: Bot, chat_data, group_id: int) -> Optional[int]:
        """
        Убеждается, что тема существует, создает если нет
        
        Args:
            bot: Экземпляр бота
            chat_data: Данные чата
            group_id: ID группы
            
        Returns:
            ID темы или None в случае ошибки
        """
        if chat_data.topic_id:
            return chat_data.topic_id
        
        return await cls.create_topic(bot, group_id, chat_data)
