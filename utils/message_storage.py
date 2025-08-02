import json
import logging
import uuid
import base64
from typing import Dict, Any, Optional, List
from aiogram.types import Message, MessageEntity
from utils.redis_manager import redis_manager

logger = logging.getLogger(__name__)

class MessageStorage:
    """Класс для сохранения и восстановления сообщений через Redis"""
    
    @staticmethod
    def _serialize_entities(entities: List[MessageEntity]) -> List[Dict]:
        """Сериализация entities для сохранения"""
        if not entities:
            return []
        
        result = []
        for entity in entities:
            entity_dict = {
                'type': entity.type,
                'offset': entity.offset,
                'length': entity.length
            }
            
            # Добавляем дополнительные поля если есть
            if hasattr(entity, 'url') and entity.url:
                entity_dict['url'] = entity.url
            if hasattr(entity, 'user') and entity.user:
                entity_dict['user'] = {
                    'id': entity.user.id,
                    'first_name': entity.user.first_name,
                    'username': entity.user.username
                }
            if hasattr(entity, 'language') and entity.language:
                entity_dict['language'] = entity.language
            if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
                entity_dict['custom_emoji_id'] = entity.custom_emoji_id
                
            result.append(entity_dict)
        
        return result
    
    @staticmethod
    async def save_message(message: Message, chat_data, direction: str = "to_group") -> str:
        """
        Сохранение сообщения в Redis
        
        Args:
            message: Объект сообщения
            chat_data: Данные чата
            direction: "to_group" или "to_user"
            
        Returns:
            Уникальный ID сохраненного сообщения
        """
        try:
            message_id = str(uuid.uuid4())
            
            # Базовая информация о сообщении
            message_data = {
                'message_id': message.message_id,
                'chat_id': message.chat.id,
                'original_chat_id': message.chat.id,  # Для fallback
                'from_user_id': message.from_user.id if message.from_user else None,
                'date': message.date.timestamp() if message.date else None,
                'direction': direction,
                'chat_data_id': chat_data.id,
                'user_id': chat_data.user_id,
                'bot_id': chat_data.bot_id if hasattr(chat_data, 'bot_id') else None
            }
            
            # Определяем тип сообщения и сохраняем соответствующие данные
            if message.text:
                message_data.update({
                    'type': 'text',
                    'text': message.text,
                    'entities': MessageStorage._serialize_entities(message.entities)
                })
                
            elif message.photo:
                from utils.file_handler import FileHandler
                
                photo = message.photo[-1]  # Берем фото наибольшего размера
                
                # Скачиваем файл и сохраняем в Redis
                file_bytes = await FileHandler.download_file(message.bot, photo.file_id)
                if file_bytes:
                    # Кодируем в base64 для сохранения в Redis
                    file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                    file_key = f"file:{message_id}"
                    await redis_manager.set(file_key, file_base64, expire=3600)
                    
                    message_data.update({
                        'type': 'photo',
                        'file_key': file_key,
                        'file_id': photo.file_id,
                        'file_unique_id': photo.file_unique_id,
                        'width': photo.width,
                        'height': photo.height,
                        'file_size': photo.file_size,
                        'filename': f"photo_{message_id}.jpg",
                        'caption': message.caption,
                        'caption_entities': MessageStorage._serialize_entities(message.caption_entities)
                    })
                else:
                    logger.error(f"Не удалось скачать фото {photo.file_id}")
                    return None
                
            elif message.video:
                from utils.file_handler import FileHandler
                
                # Скачиваем файл и сохраняем в Redis
                file_bytes = await FileHandler.download_file(message.bot, message.video.file_id)
                if file_bytes:
                    # Кодируем в base64 для сохранения в Redis
                    file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                    file_key = f"file:{message_id}"
                    await redis_manager.set(file_key, file_base64, expire=3600)
                    
                    message_data.update({
                        'type': 'video',
                        'file_key': file_key,
                        'file_id': message.video.file_id,
                        'file_unique_id': message.video.file_unique_id,
                        'width': message.video.width,
                        'height': message.video.height,
                        'duration': message.video.duration,
                        'file_size': message.video.file_size,
                        'filename': message.video.file_name or f"video_{message_id}.mp4",
                        'mime_type': message.video.mime_type,
                        'caption': message.caption,
                        'caption_entities': MessageStorage._serialize_entities(message.caption_entities)
                    })
                else:
                    logger.error(f"Не удалось скачать видео {message.video.file_id}")
                    return None
                
            elif message.voice:
                from utils.file_handler import FileHandler
                
                # Скачиваем файл и сохраняем в Redis
                file_bytes = await FileHandler.download_file(message.bot, message.voice.file_id)
                if file_bytes:
                    # Кодируем в base64 для сохранения в Redis
                    file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                    file_key = f"file:{message_id}"
                    await redis_manager.set(file_key, file_base64, expire=3600)
                    
                    message_data.update({
                        'type': 'voice',
                        'file_key': file_key,
                        'file_id': message.voice.file_id,
                        'file_unique_id': message.voice.file_unique_id,
                        'duration': message.voice.duration,
                        'file_size': message.voice.file_size,
                        'filename': f"voice_{message_id}.ogg",
                        'mime_type': message.voice.mime_type,
                        'caption': message.caption,
                        'caption_entities': MessageStorage._serialize_entities(message.caption_entities)
                    })
                else:
                    logger.error(f"Не удалось скачать голосовое {message.voice.file_id}")
                    return None
                
            elif message.video_note:
                from utils.file_handler import FileHandler
                
                # Скачиваем файл и сохраняем в Redis
                file_bytes = await FileHandler.download_file(message.bot, message.video_note.file_id)
                if file_bytes:
                    # Кодируем в base64 для сохранения в Redis
                    file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                    file_key = f"file:{message_id}"
                    await redis_manager.set(file_key, file_base64, expire=3600)
                    
                    message_data.update({
                        'type': 'video_note',
                        'file_key': file_key,
                        'file_id': message.video_note.file_id,
                        'file_unique_id': message.video_note.file_unique_id,
                        'length': message.video_note.length,
                        'duration': message.video_note.duration,
                        'filename': f"video_note_{message_id}.mp4",
                        'file_size': message.video_note.file_size
                    })
                else:
                    logger.error(f"Не удалось скачать видеокружок {message.video_note.file_id}")
                    return None
                
            elif message.audio:
                message_data.update({
                    'type': 'audio',
                    'file_id': message.audio.file_id,
                    'file_unique_id': message.audio.file_unique_id,
                    'duration': message.audio.duration,
                    'performer': message.audio.performer,
                    'title': message.audio.title,
                    'file_name': message.audio.file_name,
                    'mime_type': message.audio.mime_type,
                    'file_size': message.audio.file_size,
                    'caption': message.caption,
                    'caption_entities': MessageStorage._serialize_entities(message.caption_entities)
                })
                
            elif message.document:
                from utils.file_handler import FileHandler
                
                # Скачиваем файл и сохраняем в Redis
                file_bytes = await FileHandler.download_file(message.bot, message.document.file_id)
                if file_bytes:
                    # Кодируем в base64 для сохранения в Redis
                    file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                    file_key = f"file:{message_id}"
                    await redis_manager.set(file_key, file_base64, expire=3600)
                    
                    message_data.update({
                        'type': 'document',
                        'file_key': file_key,
                        'file_id': message.document.file_id,
                        'file_unique_id': message.document.file_unique_id,
                        'filename': message.document.file_name or f"document_{message_id}",
                        'mime_type': message.document.mime_type,
                        'file_size': message.document.file_size,
                        'caption': message.caption,
                        'caption_entities': MessageStorage._serialize_entities(message.caption_entities)
                    })
                else:
                    logger.error(f"Не удалось скачать документ {message.document.file_id}")
                    return None
                
            elif message.sticker:
                message_data.update({
                    'type': 'sticker',
                    'file_id': message.sticker.file_id,
                    'file_unique_id': message.sticker.file_unique_id,
                    'width': message.sticker.width,
                    'height': message.sticker.height,
                    'is_animated': message.sticker.is_animated,
                    'is_video': message.sticker.is_video,
                    'emoji': message.sticker.emoji,
                    'set_name': message.sticker.set_name,
                    'file_size': message.sticker.file_size
                })
                
            elif message.animation:
                message_data.update({
                    'type': 'animation',
                    'file_id': message.animation.file_id,
                    'file_unique_id': message.animation.file_unique_id,
                    'width': message.animation.width,
                    'height': message.animation.height,
                    'duration': message.animation.duration,
                    'file_name': message.animation.file_name,
                    'mime_type': message.animation.mime_type,
                    'file_size': message.animation.file_size,
                    'caption': message.caption,
                    'caption_entities': MessageStorage._serialize_entities(message.caption_entities)
                })
                
            elif message.location:
                message_data.update({
                    'type': 'location',
                    'latitude': message.location.latitude,
                    'longitude': message.location.longitude,
                    'live_period': message.location.live_period,
                    'heading': message.location.heading,
                    'proximity_alert_radius': message.location.proximity_alert_radius
                })
                
            elif message.contact:
                message_data.update({
                    'type': 'contact',
                    'phone_number': message.contact.phone_number,
                    'first_name': message.contact.first_name,
                    'last_name': message.contact.last_name,
                    'user_id': message.contact.user_id,
                    'vcard': message.contact.vcard
                })
                
            elif message.poll:
                options = [{'text': opt.text, 'voter_count': opt.voter_count} for opt in message.poll.options]
                message_data.update({
                    'type': 'poll',
                    'id': message.poll.id,
                    'question': message.poll.question,
                    'options': options,
                    'total_voter_count': message.poll.total_voter_count,
                    'is_closed': message.poll.is_closed,
                    'is_anonymous': message.poll.is_anonymous,
                    'type_poll': message.poll.type,
                    'allows_multiple_answers': message.poll.allows_multiple_answers
                })
                
            elif message.venue:
                message_data.update({
                    'type': 'venue',
                    'location': {
                        'latitude': message.venue.location.latitude,
                        'longitude': message.venue.location.longitude
                    },
                    'title': message.venue.title,
                    'address': message.venue.address,
                    'foursquare_id': message.venue.foursquare_id,
                    'foursquare_type': message.venue.foursquare_type,
                    'google_place_id': message.venue.google_place_id,
                    'google_place_type': message.venue.google_place_type
                })
                
            else:
                message_data.update({
                    'type': 'other',
                    'content_type': str(message.content_type) if hasattr(message, 'content_type') else 'unknown'
                })
            
            # Сохраняем медиагруппу если есть
            if message.media_group_id:
                message_data['media_group_id'] = message.media_group_id
            
            # Сохраняем в Redis с TTL 1 час
            key = f"message:{message_id}"
            success = await redis_manager.set(key, message_data, expire=3600)
            
            if success:
                logger.info(f"Сообщение {message_data['type']} сохранено в Redis с ID {message_id}")
                return message_id
            else:
                logger.error(f"Не удалось сохранить сообщение в Redis")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения: {e}")
            return None
    
    @staticmethod
    async def get_message(message_id: str) -> Optional[Dict[str, Any]]:
        """Получение сообщения из Redis"""
        try:
            key = f"message:{message_id}"
            message_data = await redis_manager.get(key)
            
            if message_data:
                logger.debug(f"Сообщение {message_id} получено из Redis")
                return message_data
            else:
                logger.warning(f"Сообщение {message_id} не найдено в Redis")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении сообщения {message_id}: {e}")
            return None
    
    @staticmethod
    async def delete_message(message_id: str) -> bool:
        """Удаление сообщения из Redis"""
        try:
            key = f"message:{message_id}"
            success = await redis_manager.delete(key)
            
            if success:
                logger.debug(f"Сообщение {message_id} удалено из Redis")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения {message_id}: {e}")
            return False
    
    @staticmethod
    async def save_media_group(messages: List[Message], chat_data, direction: str = "to_group") -> List[str]:
        """Сохранение медиагруппы в Redis"""
        message_ids = []
        
        for message in messages:
            message_id = await MessageStorage.save_message(message, chat_data, direction)
            if message_id:
                message_ids.append(message_id)
        
        # Сохраняем информацию о медиагруппе
        if message_ids and messages[0].media_group_id:
            group_key = f"media_group:{messages[0].media_group_id}"
            group_data = {
                'message_ids': message_ids,
                'chat_data_id': chat_data.id,
                'direction': direction,
                'created_at': messages[0].date.timestamp() if messages[0].date else None
            }
            
            await redis_manager.set(group_key, group_data, expire=3600)
            logger.info(f"Медиагруппа {messages[0].media_group_id} сохранена с {len(message_ids)} сообщениями")
        
        return message_ids
    
    @staticmethod
    async def get_media_group(media_group_id: str) -> Optional[Dict[str, Any]]:
        """Получение медиагруппы из Redis"""
        try:
            group_key = f"media_group:{media_group_id}"
            group_data = await redis_manager.get(group_key)
            
            if not group_data:
                return None
            
            # Получаем все сообщения группы
            messages = []
            for message_id in group_data.get('message_ids', []):
                message_data = await MessageStorage.get_message(message_id)
                if message_data:
                    messages.append(message_data)
            
            group_data['messages'] = messages
            return group_data
            
        except Exception as e:
            logger.error(f"Ошибка при получении медиагруппы {media_group_id}: {e}")
            return None
    
    @staticmethod
    async def delete_media_group(media_group_id: str) -> bool:
        """Удаление медиагруппы из Redis"""
        try:
            # Получаем данные группы
            group_data = await MessageStorage.get_media_group(media_group_id)
            if not group_data:
                return True
            
            # Удаляем все сообщения группы
            for message_id in group_data.get('message_ids', []):
                await MessageStorage.delete_message(message_id)
            
            # Удаляем саму группу
            group_key = f"media_group:{media_group_id}"
            success = await redis_manager.delete(group_key)
            
            logger.info(f"Медиагруппа {media_group_id} удалена")
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при удалении медиагруппы {media_group_id}: {e}")
            return False