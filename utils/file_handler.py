import logging
import aiohttp
import io
from typing import Optional, Dict, Any
from aiogram import Bot
from aiogram.types import Message, BufferedInputFile

logger = logging.getLogger(__name__)

class FileHandler:
    """Класс для работы с файлами - скачивание и отправка"""
    
    @staticmethod
    async def download_file(bot: Bot, file_id: str) -> Optional[bytes]:
        """
        Скачивание файла по file_id
        
        Args:
            bot: Бот для скачивания
            file_id: ID файла
            
        Returns:
            Содержимое файла в байтах или None
        """
        try:
            # Получаем информацию о файле
            file_info = await bot.get_file(file_id)
            
            # Скачиваем файл
            file_content = await bot.download_file(file_info.file_path)
            
            if isinstance(file_content, io.BytesIO):
                return file_content.getvalue()
            else:
                return file_content
                
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла {file_id}: {e}")
            return None
    
    @staticmethod
    async def send_photo_from_bytes(bot: Bot, chat_id: int, file_bytes: bytes, 
                                  filename: str = "photo.jpg", caption: str = None,
                                  caption_entities=None, message_thread_id: int = None,
                                  use_parse_mode: bool = False) -> bool:
        """Отправка фото из байтов"""
        try:
            input_file = BufferedInputFile(file_bytes, filename=filename)
            
            kwargs = {
                'chat_id': chat_id,
                'photo': input_file,
                'caption': caption
            }
            
            # Если нужно использовать parse_mode, не передаем caption_entities
            if use_parse_mode:
                from aiogram.enums import ParseMode
                kwargs['parse_mode'] = ParseMode.MARKDOWN_V2
            else:
                kwargs['caption_entities'] = caption_entities
            
            if message_thread_id:
                kwargs['message_thread_id'] = message_thread_id
            
            await bot.send_photo(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {e}")
            return False
    
    @staticmethod
    async def send_video_from_bytes(bot: Bot, chat_id: int, file_bytes: bytes,
                                  filename: str = "video.mp4", caption: str = None,
                                  caption_entities=None, message_thread_id: int = None,
                                  duration: int = None, width: int = None, height: int = None,
                                  use_parse_mode: bool = False) -> bool:
        """Отправка видео из байтов"""
        try:
            input_file = BufferedInputFile(file_bytes, filename=filename)
            
            kwargs = {
                'chat_id': chat_id,
                'video': input_file,
                'caption': caption
            }
            
            # Если нужно использовать parse_mode, не передаем caption_entities
            if use_parse_mode:
                from aiogram.enums import ParseMode
                kwargs['parse_mode'] = ParseMode.MARKDOWN_V2
            else:
                kwargs['caption_entities'] = caption_entities
            
            if message_thread_id:
                kwargs['message_thread_id'] = message_thread_id
            if duration:
                kwargs['duration'] = duration
            if width:
                kwargs['width'] = width
            if height:
                kwargs['height'] = height
            
            await bot.send_video(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке видео: {e}")
            return False
    
    @staticmethod
    async def send_voice_from_bytes(bot: Bot, chat_id: int, file_bytes: bytes,
                                  filename: str = "voice.ogg", caption: str = None,
                                  caption_entities=None, message_thread_id: int = None,
                                  duration: int = None, use_parse_mode: bool = False) -> bool:
        """Отправка голосового из байтов"""
        try:
            input_file = BufferedInputFile(file_bytes, filename=filename)
            
            kwargs = {
                'chat_id': chat_id,
                'voice': input_file,
                'caption': caption
            }
            
            # Если нужно использовать parse_mode, не передаем caption_entities
            if use_parse_mode:
                from aiogram.enums import ParseMode
                kwargs['parse_mode'] = ParseMode.MARKDOWN_V2
            else:
                kwargs['caption_entities'] = caption_entities
            
            if message_thread_id:
                kwargs['message_thread_id'] = message_thread_id
            if duration:
                kwargs['duration'] = duration
            
            await bot.send_voice(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке голосового: {e}")
            return False
    
    @staticmethod
    async def send_video_note_from_bytes(bot: Bot, chat_id: int, file_bytes: bytes,
                                       filename: str = "video_note.mp4", message_thread_id: int = None,
                                       duration: int = None, length: int = None) -> bool:
        """Отправка видеокружка из байтов"""
        try:
            input_file = BufferedInputFile(file_bytes, filename=filename)
            
            kwargs = {
                'chat_id': chat_id,
                'video_note': input_file
            }
            
            if message_thread_id:
                kwargs['message_thread_id'] = message_thread_id
            if duration:
                kwargs['duration'] = duration
            if length:
                kwargs['length'] = length
            
            await bot.send_video_note(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке видеокружка: {e}")
            return False
    
    @staticmethod
    async def send_document_from_bytes(bot: Bot, chat_id: int, file_bytes: bytes,
                                     filename: str, caption: str = None,
                                     caption_entities=None, message_thread_id: int = None,
                                     use_parse_mode: bool = False) -> bool:
        """Отправка документа из байтов"""
        try:
            input_file = BufferedInputFile(file_bytes, filename=filename)
            
            kwargs = {
                'chat_id': chat_id,
                'document': input_file,
                'caption': caption
            }
            
            # Если нужно использовать parse_mode, не передаем caption_entities
            if use_parse_mode:
                from aiogram.enums import ParseMode
                kwargs['parse_mode'] = ParseMode.MARKDOWN_V2
            else:
                kwargs['caption_entities'] = caption_entities
            
            if message_thread_id:
                kwargs['message_thread_id'] = message_thread_id
            
            await bot.send_document(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке документа: {e}")
            return False
    
    @staticmethod
    async def send_audio_from_bytes(bot: Bot, chat_id: int, file_bytes: bytes,
                                  filename: str = "audio.mp3", caption: str = None,
                                  caption_entities=None, message_thread_id: int = None,
                                  duration: int = None, performer: str = None, title: str = None) -> bool:
        """Отправка аудио из байтов"""
        try:
            input_file = BufferedInputFile(file_bytes, filename=filename)
            
            kwargs = {
                'chat_id': chat_id,
                'audio': input_file,
                'caption': caption,
                'caption_entities': caption_entities
            }
            
            if message_thread_id:
                kwargs['message_thread_id'] = message_thread_id
            if duration:
                kwargs['duration'] = duration
            if performer:
                kwargs['performer'] = performer
            if title:
                kwargs['title'] = title
            
            await bot.send_audio(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке аудио: {e}")
            return False
    
    @staticmethod
    async def send_animation_from_bytes(bot: Bot, chat_id: int, file_bytes: bytes,
                                      filename: str = "animation.gif", caption: str = None,
                                      caption_entities=None, message_thread_id: int = None,
                                      duration: int = None, width: int = None, height: int = None) -> bool:
        """Отправка анимации из байтов"""
        try:
            input_file = BufferedInputFile(file_bytes, filename=filename)
            
            kwargs = {
                'chat_id': chat_id,
                'animation': input_file,
                'caption': caption,
                'caption_entities': caption_entities
            }
            
            if message_thread_id:
                kwargs['message_thread_id'] = message_thread_id
            if duration:
                kwargs['duration'] = duration
            if width:
                kwargs['width'] = width
            if height:
                kwargs['height'] = height
            
            await bot.send_animation(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке анимации: {e}")
            return False