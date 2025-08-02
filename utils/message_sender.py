import logging
import base64
from typing import Dict, Any, List, Optional
from aiogram import Bot
from aiogram.types import MessageEntity
from utils.message_storage import MessageStorage
from utils.file_handler import FileHandler
from utils.redis_manager import redis_manager

logger = logging.getLogger(__name__)

class MessageSender:
    """Класс для восстановления и отправки сообщений из Redis"""
    

    
    @staticmethod
    def _restore_entities(entities_data: List[Dict]) -> List[MessageEntity]:
        """Восстановление entities из сохраненных данных"""
        if not entities_data:
            return []
        
        entities = []
        for entity_data in entities_data:
            try:
                # Создаем базовый MessageEntity
                entity = MessageEntity(
                    type=entity_data['type'],
                    offset=entity_data['offset'],
                    length=entity_data['length']
                )
                
                # Добавляем дополнительные поля если есть
                if 'url' in entity_data:
                    entity.url = entity_data['url']
                if 'language' in entity_data:
                    entity.language = entity_data['language']
                if 'custom_emoji_id' in entity_data:
                    entity.custom_emoji_id = entity_data['custom_emoji_id']
                
                entities.append(entity)
                
            except Exception as e:
                logger.warning(f"Не удалось восстановить entity: {e}")
                continue
        
        return entities
    
    @staticmethod
    async def _get_file_bytes_from_redis(file_key: str) -> Optional[bytes]:
        """Получение файла из Redis и декодирование из base64"""
        try:
            file_base64 = await redis_manager.get(file_key)
            if file_base64 and isinstance(file_base64, str):
                # Декодируем из base64
                file_bytes = base64.b64decode(file_base64)
                return file_bytes
            else:
                logger.error(f"Файл не найден в Redis по ключу {file_key}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении файла из Redis: {e}")
            return None
    
    @staticmethod
    async def send_message_from_storage(bot: Bot, message_id: str, target_chat_id: int, 
                                      message_thread_id: Optional[int] = None) -> bool:
        """
        Отправка сообщения из хранилища
        
        Args:
            bot: Бот для отправки
            message_id: ID сообщения в хранилище
            target_chat_id: ID целевого чата
            message_thread_id: ID темы (для групп)
            
        Returns:
            True если успешно отправлено
        """
        try:
            # Получаем данные сообщения
            message_data = await MessageStorage.get_message(message_id)
            if not message_data:
                logger.error(f"Сообщение {message_id} не найдено в хранилище")
                return False
            
            message_type = message_data.get('type', 'unknown')
            
            # Обрабатываем разные типы сообщений
            if message_type == 'text':
                from utils.text_formatter import TextFormatter
                
                # Преобразуем entities в Markdown V2 формат
                formatted_text = TextFormatter.format_text_with_entities(
                    message_data['text'],
                    message_data.get('entities', [])
                )
                
                from aiogram.enums import ParseMode
                
                await bot.send_message(
                    chat_id=target_chat_id,
                    text=formatted_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    message_thread_id=message_thread_id
                )
                
            elif message_type == 'photo':
                file_key = message_data.get('file_key')
                if file_key:
                    file_bytes = await MessageSender._get_file_bytes_from_redis(file_key)
                    if file_bytes:
                        from utils.text_formatter import TextFormatter
                        
                        # Преобразуем подпись с entities в Markdown V2
                        formatted_caption = TextFormatter.format_caption_with_entities(
                            message_data.get('caption'),
                            message_data.get('caption_entities', [])
                        )
                        
                        success = await FileHandler.send_photo_from_bytes(
                            bot=bot,
                            chat_id=target_chat_id,
                            file_bytes=file_bytes,
                            filename=message_data.get('filename', 'photo.jpg'),
                            caption=formatted_caption,
                            caption_entities=None,  # Не передаем entities, так как уже в Markdown
                            message_thread_id=message_thread_id,
                            use_parse_mode=True  # Используем parse_mode для Markdown V2
                        )
                        if success:
                            # Удаляем файл из Redis
                            await redis_manager.delete(file_key)
                        else:
                            raise Exception("Не удалось отправить фото")
                    else:
                        raise Exception("Не удалось получить файл фото из Redis")
                else:
                    raise Exception("Нет ключа файла для фото")
                    
            elif message_type == 'video':
                file_key = message_data.get('file_key')
                if file_key:
                    file_bytes = await MessageSender._get_file_bytes_from_redis(file_key)
                    if file_bytes:
                        from utils.text_formatter import TextFormatter
                        
                        # Преобразуем подпись с entities в Markdown V2
                        formatted_caption = TextFormatter.format_caption_with_entities(
                            message_data.get('caption'),
                            message_data.get('caption_entities', [])
                        )
                        
                        success = await FileHandler.send_video_from_bytes(
                            bot=bot,
                            chat_id=target_chat_id,
                            file_bytes=file_bytes,
                            filename=message_data.get('filename', 'video.mp4'),
                            caption=formatted_caption,
                            caption_entities=None,  # Не передаем entities, так как уже в Markdown
                            message_thread_id=message_thread_id,
                            duration=message_data.get('duration'),
                            width=message_data.get('width'),
                            height=message_data.get('height'),
                            use_parse_mode=True  # Используем parse_mode для Markdown V2
                        )
                        if success:
                            # Удаляем файл из Redis
                            await redis_manager.delete(file_key)
                        else:
                            raise Exception("Не удалось отправить видео")
                    else:
                        raise Exception("Не удалось получить файл видео из Redis")
                else:
                    raise Exception("Нет ключа файла для видео")
                    
            elif message_type == 'voice':
                file_key = message_data.get('file_key')
                if file_key:
                    file_bytes = await MessageSender._get_file_bytes_from_redis(file_key)
                    if file_bytes:
                        from utils.text_formatter import TextFormatter
                        
                        # Преобразуем подпись с entities в Markdown V2
                        formatted_caption = TextFormatter.format_caption_with_entities(
                            message_data.get('caption'),
                            message_data.get('caption_entities', [])
                        )
                        
                        success = await FileHandler.send_voice_from_bytes(
                            bot=bot,
                            chat_id=target_chat_id,
                            file_bytes=file_bytes,
                            filename=message_data.get('filename', 'voice.ogg'),
                            caption=formatted_caption,
                            caption_entities=None,  # Не передаем entities, так как уже в Markdown
                            message_thread_id=message_thread_id,
                            duration=message_data.get('duration'),
                            use_parse_mode=True  # Используем parse_mode для Markdown V2
                        )
                        if success:
                            # Удаляем файл из Redis
                            await redis_manager.delete(file_key)
                        else:
                            raise Exception("Не удалось отправить голосовое")
                    else:
                        raise Exception("Не удалось получить файл голосового из Redis")
                else:
                    raise Exception("Нет ключа файла для голосового")
                    
            elif message_type == 'video_note':
                file_key = message_data.get('file_key')
                if file_key:
                    file_bytes = await MessageSender._get_file_bytes_from_redis(file_key)
                    if file_bytes:
                        success = await FileHandler.send_video_note_from_bytes(
                            bot=bot,
                            chat_id=target_chat_id,
                            file_bytes=file_bytes,
                            filename=message_data.get('filename', 'video_note.mp4'),
                            message_thread_id=message_thread_id,
                            duration=message_data.get('duration'),
                            length=message_data.get('length')
                        )
                        if success:
                            # Удаляем файл из Redis
                            await redis_manager.delete(file_key)
                        else:
                            raise Exception("Не удалось отправить видеокружок")
                    else:
                        raise Exception("Не удалось получить файл видеокружка из Redis")
                else:
                    raise Exception("Нет ключа файла для видеокружка")
                    
            elif message_type == 'document':
                file_key = message_data.get('file_key')
                if file_key:
                    file_bytes = await MessageSender._get_file_bytes_from_redis(file_key)
                    if file_bytes:
                        from utils.text_formatter import TextFormatter
                        
                        # Преобразуем подпись с entities в Markdown V2
                        formatted_caption = TextFormatter.format_caption_with_entities(
                            message_data.get('caption'),
                            message_data.get('caption_entities', [])
                        )
                        
                        success = await FileHandler.send_document_from_bytes(
                            bot=bot,
                            chat_id=target_chat_id,
                            file_bytes=file_bytes,
                            filename=message_data.get('filename', 'document'),
                            caption=formatted_caption,
                            caption_entities=None,  # Не передаем entities, так как уже в Markdown
                            message_thread_id=message_thread_id,
                            use_parse_mode=True  # Используем parse_mode для Markdown V2
                        )
                        if success:
                            # Удаляем файл из Redis
                            await redis_manager.delete(file_key)
                        else:
                            raise Exception("Не удалось отправить документ")
                    else:
                        raise Exception("Не удалось получить файл документа из Redis")
                else:
                    raise Exception("Нет ключа файла для документа")
                    
            else:
                logger.warning(f"Неподдерживаемый тип сообщения: {message_type}")
                return False
            
            logger.info(f"Сообщение типа {message_type} успешно отправлено")
            
            # Удаляем сообщение из хранилища после успешной отправки
            await MessageStorage.delete_message(message_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения {message_id}: {e}")
            return False
    
    @staticmethod
    async def send_media_group_from_storage(bot: Bot, media_group_id: str, target_chat_id: int,
                                          message_thread_id: Optional[int] = None) -> bool:
        """
        Отправка медиагруппы из хранилища
        
        Args:
            bot: Бот для отправки
            media_group_id: ID медиагруппы
            target_chat_id: ID целевого чата
            message_thread_id: ID темы (для групп)
            
        Returns:
            True если успешно отправлено
        """
        try:
            # Получаем данные медиагруппы
            group_data = await MessageStorage.get_media_group(media_group_id)
            if not group_data:
                logger.error(f"Медиагруппа {media_group_id} не найдена в хранилище")
                return False
            
            messages = group_data.get('messages', [])
            if not messages:
                logger.warning(f"Медиагруппа {media_group_id} пуста")
                return False
            
            # Отправляем каждое сообщение медиагруппы отдельно
            sent_count = 0
            for message_data in messages:
                try:
                    message_type = message_data.get('type')
                    file_key = message_data.get('file_key')
                    
                    if not file_key:
                        logger.warning(f"Нет ключа файла для сообщения в медиагруппе")
                        continue
                    
                    file_bytes = await MessageSender._get_file_bytes_from_redis(file_key)
                    if not file_bytes:
                        logger.warning(f"Не удалось получить файл из Redis для медиагруппы")
                        continue
                    
                    # Подпись только для первого элемента, преобразованная в Markdown V2
                    formatted_caption = None
                    if sent_count == 0:
                        from utils.text_formatter import TextFormatter
                        formatted_caption = TextFormatter.format_caption_with_entities(
                            message_data.get('caption'),
                            message_data.get('caption_entities', [])
                        )
                    
                    success = False
                    if message_type == 'photo':
                        success = await FileHandler.send_photo_from_bytes(
                            bot=bot,
                            chat_id=target_chat_id,
                            file_bytes=file_bytes,
                            filename=message_data.get('filename', 'photo.jpg'),
                            caption=formatted_caption,
                            caption_entities=None,  # Не передаем entities, так как уже в Markdown
                            message_thread_id=message_thread_id,
                            use_parse_mode=True  # Используем parse_mode для Markdown V2
                        )
                    elif message_type == 'video':
                        success = await FileHandler.send_video_from_bytes(
                            bot=bot,
                            chat_id=target_chat_id,
                            file_bytes=file_bytes,
                            filename=message_data.get('filename', 'video.mp4'),
                            caption=formatted_caption,
                            caption_entities=None,  # Не передаем entities, так как уже в Markdown
                            message_thread_id=message_thread_id,
                            duration=message_data.get('duration'),
                            width=message_data.get('width'),
                            height=message_data.get('height'),
                            use_parse_mode=True  # Используем parse_mode для Markdown V2
                        )
                    elif message_type == 'document':
                        success = await FileHandler.send_document_from_bytes(
                            bot=bot,
                            chat_id=target_chat_id,
                            file_bytes=file_bytes,
                            filename=message_data.get('filename', 'document'),
                            caption=formatted_caption,
                            caption_entities=None,  # Не передаем entities, так как уже в Markdown
                            message_thread_id=message_thread_id,
                            use_parse_mode=True  # Используем parse_mode для Markdown V2
                        )
                    
                    if success:
                        sent_count += 1
                        # Удаляем файл из Redis
                        await redis_manager.delete(file_key)
                    
                except Exception as msg_error:
                    logger.error(f"Ошибка отправки сообщения из медиагруппы: {msg_error}")
                    continue
            
            if sent_count > 0:
                logger.info(f"Медиагруппа {media_group_id}: отправлено {sent_count} из {len(messages)} сообщений")
                
                # Удаляем медиагруппу из хранилища
                await MessageStorage.delete_media_group(media_group_id)
                return True
            else:
                logger.error(f"Не удалось отправить ни одного сообщения из медиагруппы {media_group_id}")
                return False
            
        except Exception as e:
            logger.error(f"Ошибка при отправке медиагруппы {media_group_id}: {e}")
            return False
    
    @staticmethod
    async def send_user_info_message(bot: Bot, chat_data, target_chat_id: int, 
                                   message_thread_id: Optional[int] = None) -> bool:
        """
        Отправка информационного сообщения о пользователе
        
        Args:
            bot: Бот для отправки
            chat_data: Данные чата
            target_chat_id: ID целевого чата
            message_thread_id: ID темы
            
        Returns:
            True если успешно отправлено
        """
        try:
            from utils.markdown_utils import MarkdownV2Utils
            
            # Формируем информацию о пользователе с правильным форматированием
            bot_username = None
            if hasattr(chat_data, 'bot') and chat_data.bot:
                bot_username = chat_data.bot.bot_username
            
            user_info = MarkdownV2Utils.format_user_info(
                first_name=chat_data.first_name,
                username=chat_data.username,
                bot_username=bot_username
            )
            
            # Отправляем сообщение
            from aiogram.enums import ParseMode
            
            await bot.send_message(
                chat_id=target_chat_id,
                text=user_info,
                parse_mode=ParseMode.MARKDOWN_V2,
                message_thread_id=message_thread_id
            )
            
            logger.info(f"Информационное сообщение о пользователе {chat_data.user_id} отправлено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке информационного сообщения: {e}")
            return False