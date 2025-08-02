import logging
from aiogram.types import Message, MessageEntity, BufferedInputFile
from aiogram import Bot
from database.database import async_session
from database.queries import DatabaseQueries
from utils.topic_manager import TopicManager
from config import config
import io

logger = logging.getLogger(__name__)

class MessageHandler:
    @staticmethod
    async def send_to_main_bot(message: Message, chat_data, main_bot: Bot):
        """Отправка сообщения главному боту для обработки"""
        try:
            # Получаем данные бота из chat_data
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
            
            # Формируем информацию о пользователе с экранированием
            from utils.markdown_utils import escape_md
            user_info = f"👤 {escape_md(chat_data.first_name or 'Пользователь')}"
            if chat_data.username:
                user_info += f" \\(@{escape_md(chat_data.username)}\\)"
            user_info += f"\n🤖 Бот: @{escape_md(bot_data.bot_username)}"
            
            # Пересылаем сообщение в зависимости от типа
            if message.text:
                # Сначала отправляем информацию о пользователе
                from aiogram.enums import ParseMode
                
                await main_bot.send_message(
                    chat_id=bot_data.group_id,
                    text=user_info,
                    message_thread_id=chat_data.topic_id,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                # Затем отправляем текстовое сообщение с форматированием
                from utils.text_formatter import TextFormatter
                
                # Преобразуем entities в Markdown V2 формат
                formatted_text = TextFormatter.format_text_with_entities(
                    message.text,
                    [entity.model_dump() for entity in (message.entities or [])]
                )
                
                await main_bot.send_message(
                    chat_id=bot_data.group_id,
                    text=formatted_text,
                    message_thread_id=chat_data.topic_id,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                # Для медиа сначала отправляем информацию о пользователе
                from aiogram.enums import ParseMode
                
                await main_bot.send_message(
                    chat_id=bot_data.group_id,
                    text=user_info,
                    message_thread_id=chat_data.topic_id,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                # Затем отправляем медиа через скачивание и повторную отправку
                await MessageHandler._forward_media_message(
                    source_message=message,
                    target_bot=main_bot,
                    target_chat_id=bot_data.group_id,
                    message_thread_id=chat_data.topic_id
                )
            
            # Сохраняем в БД
            async with async_session() as session:
                db = DatabaseQueries(session)
                await db.create_message(
                    chat_id=chat_data.id,
                    message_id=message.message_id,
                    from_user=True,
                    content=message.text or message.caption,
                    message_type=MessageHandler.get_message_type(message)
                )
            
            logger.info(f"Сообщение типа {MessageHandler.get_message_type(message)} переслано в группу")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке главному боту: {e}")

    @staticmethod
    async def _forward_media_message(source_message: Message, target_bot: Bot, target_chat_id: int, message_thread_id: int):
        """Пересылка медиа сообщения через скачивание файла"""
        try:
            if source_message.photo:
                # Фото
                file_info = await source_message.bot.get_file(source_message.photo[-1].file_id)
                file_bytes = await source_message.bot.download_file(file_info.file_path)
                
                await target_bot.send_photo(
                    chat_id=target_chat_id,
                    photo=BufferedInputFile(file_bytes.read(), filename="photo.jpg"),
                    caption=source_message.caption,
                    caption_entities=source_message.caption_entities,
                    message_thread_id=message_thread_id
                )
            elif source_message.video:
                # Видео
                file_info = await source_message.bot.get_file(source_message.video.file_id)
                file_bytes = await source_message.bot.download_file(file_info.file_path)
                
                await target_bot.send_video(
                    chat_id=target_chat_id,
                    video=BufferedInputFile(file_bytes.read(), filename="video.mp4"),
                    caption=source_message.caption,
                    caption_entities=source_message.caption_entities,
                    message_thread_id=message_thread_id,
                    duration=source_message.video.duration,
                    width=source_message.video.width,
                    height=source_message.video.height
                )
            elif source_message.document:
                # Документ
                file_info = await source_message.bot.get_file(source_message.document.file_id)
                file_bytes = await source_message.bot.download_file(file_info.file_path)
                
                filename = source_message.document.file_name or "document"
                await target_bot.send_document(
                    chat_id=target_chat_id,
                    document=BufferedInputFile(file_bytes.read(), filename=filename),
                    caption=source_message.caption,
                    caption_entities=source_message.caption_entities,
                    message_thread_id=message_thread_id
                )
            elif source_message.voice:
                # Голосовое сообщение
                file_info = await source_message.bot.get_file(source_message.voice.file_id)
                file_bytes = await source_message.bot.download_file(file_info.file_path)
                
                await target_bot.send_voice(
                    chat_id=target_chat_id,
                    voice=BufferedInputFile(file_bytes.read(), filename="voice.ogg"),
                    message_thread_id=message_thread_id,
                    duration=source_message.voice.duration
                )
            elif source_message.video_note:
                # Видео-заметка (кружочек)
                file_info = await source_message.bot.get_file(source_message.video_note.file_id)
                file_bytes = await source_message.bot.download_file(file_info.file_path)
                
                await target_bot.send_video_note(
                    chat_id=target_chat_id,
                    video_note=BufferedInputFile(file_bytes.read(), filename="video_note.mp4"),
                    message_thread_id=message_thread_id,
                    duration=source_message.video_note.duration,
                    length=source_message.video_note.length
                )
            elif source_message.sticker:
                # Стикер
                file_info = await source_message.bot.get_file(source_message.sticker.file_id)
                file_bytes = await source_message.bot.download_file(file_info.file_path)
                
                await target_bot.send_sticker(
                    chat_id=target_chat_id,
                    sticker=BufferedInputFile(file_bytes.read(), filename="sticker.webp"),
                    message_thread_id=message_thread_id
                )
            elif source_message.animation:
                # GIF анимация
                file_info = await source_message.bot.get_file(source_message.animation.file_id)
                file_bytes = await source_message.bot.download_file(file_info.file_path)
                
                await target_bot.send_animation(
                    chat_id=target_chat_id,
                    animation=BufferedInputFile(file_bytes.read(), filename="animation.gif"),
                    caption=source_message.caption,
                    caption_entities=source_message.caption_entities,
                    message_thread_id=message_thread_id,
                    duration=source_message.animation.duration,
                    width=source_message.animation.width,
                    height=source_message.animation.height
                )
            elif source_message.audio:
                # Аудио
                file_info = await source_message.bot.get_file(source_message.audio.file_id)
                file_bytes = await source_message.bot.download_file(file_info.file_path)
                
                await target_bot.send_audio(
                    chat_id=target_chat_id,
                    audio=BufferedInputFile(file_bytes.read(), filename="audio.mp3"),
                    caption=source_message.caption,
                    caption_entities=source_message.caption_entities,
                    message_thread_id=message_thread_id,
                    duration=source_message.audio.duration,
                    performer=source_message.audio.performer,
                    title=source_message.audio.title
                )
            elif source_message.location:
                # Геолокация
                await target_bot.send_location(
                    chat_id=target_chat_id,
                    latitude=source_message.location.latitude,
                    longitude=source_message.location.longitude,
                    message_thread_id=message_thread_id,
                    live_period=source_message.location.live_period,
                    heading=source_message.location.heading,
                    proximity_alert_radius=source_message.location.proximity_alert_radius
                )
            elif source_message.contact:
                # Контакт
                await target_bot.send_contact(
                    chat_id=target_chat_id,
                    phone_number=source_message.contact.phone_number,
                    first_name=source_message.contact.first_name,
                    last_name=source_message.contact.last_name,
                    vcard=source_message.contact.vcard,
                    message_thread_id=message_thread_id
                )
            elif source_message.venue:
                # Место
                await target_bot.send_venue(
                    chat_id=target_chat_id,
                    latitude=source_message.venue.location.latitude,
                    longitude=source_message.venue.location.longitude,
                    title=source_message.venue.title,
                    address=source_message.venue.address,
                    foursquare_id=source_message.venue.foursquare_id,
                    foursquare_type=source_message.venue.foursquare_type,
                    message_thread_id=message_thread_id
                )
            else:
                # Для неизвестных типов отправляем текстовое сообщение
                from utils.markdown_utils import escape_md
                from aiogram.enums import ParseMode
                
                await target_bot.send_message(
                    chat_id=target_chat_id,
                    text=f"📎 Получено сообщение типа: {escape_md(MessageHandler.get_message_type(source_message))}",
                    message_thread_id=message_thread_id,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
        except Exception as e:
            logger.error(f"Ошибка при пересылке медиа: {e}")

    @staticmethod
    async def forward_to_user(message: Message, chat_data, user_bot: Bot):
        """Пересылка сообщения пользователю"""
        try:
            # Проверяем, что сообщение не пустое
            if not MessageHandler._has_content(message):
                logger.info(f"Пропуск пустого сообщения: {message.message_id}")
                return
            
            # Пересылаем сообщение пользователю через скачивание файлов
            if message.text:
                # Текстовое сообщение с форматированием в Markdown V2
                from utils.text_formatter import TextFormatter
                from aiogram.enums import ParseMode
                
                # Преобразуем entities в Markdown V2 формат
                formatted_text = TextFormatter.format_text_with_entities(
                    message.text,
                    [entity.model_dump() for entity in (message.entities or [])]
                )
                
                await user_bot.send_message(
                    chat_id=chat_data.user_id,
                    text=formatted_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                # Медиа сообщения
                await MessageHandler._forward_media_message(
                    source_message=message,
                    target_bot=user_bot,
                    target_chat_id=chat_data.user_id,
                    message_thread_id=None
                )
            
            # Сохраняем в БД
            async with async_session() as session:
                db = DatabaseQueries(session)
                await db.create_message(
                    chat_id=chat_data.id,
                    message_id=message.message_id,
                    from_user=False,
                    content=message.text or message.caption,
                    message_type=MessageHandler.get_message_type(message)
                )
            
            logger.info(f"Сообщение типа {MessageHandler.get_message_type(message)} успешно переслано пользователю {chat_data.user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при пересылке пользователю: {e}")
            logger.error(f"Тип сообщения: {getattr(message, 'content_type', 'unknown')}")
            logger.error(f"Chat ID: {chat_data.user_id}")
            logger.error(f"Message ID: {message.message_id}")

    @staticmethod
    def get_message_type(message: Message) -> str:
        """Определение типа сообщения"""
        if message.text:
            return 'text'
        elif message.photo:
            return 'photo'
        elif message.video:
            return 'video'
        elif message.document:
            return 'document'
        elif message.voice:
            return 'voice'
        elif message.video_note:
            return 'video_note'
        elif message.sticker:
            return 'sticker'
        elif message.animation:
            return 'animation'
        elif message.audio:
            return 'audio'
        elif message.location:
            return 'location'
        elif message.contact:
            return 'contact'
        elif message.poll:
            return 'poll'
        elif message.venue:
            return 'venue'
        else:
            return 'other'

    @staticmethod
    def get_topic_name(chat_data) -> str:
        """Формирование имени темы"""
        # Имена тем не нужно экранировать, так как они не используют Markdown
        name = chat_data.first_name or "Пользователь"
        if chat_data.username:
            name += f" (@{chat_data.username})"
        
        emoji = config.STATUS_EMOJIS.get(chat_data.status, '⏳')
        return f"{emoji} {name}"

    @staticmethod
    async def update_topic_name(chat_data, group_bot: Bot, group_id: int):
        """Обновление имени темы"""
        await TopicManager.update_topic_name(group_bot, chat_data, group_id)

    @staticmethod
    def _has_content(message: Message) -> bool:
        """Проверка, содержит ли сообщение какой-либо контент"""
        return any([
            message.text,
            message.photo,
            message.video,
            message.document,
            message.voice,
            message.video_note,
            message.sticker,
            message.animation,
            message.audio,
            message.location,
            message.contact,
            message.poll,
            message.venue,
            message.caption
        ])