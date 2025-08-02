import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums.content_type import ContentType
from aiogram.enums import ParseMode

from database.database import async_session
from database.queries import DatabaseQueries

from utils.message_handler import MessageHandler
from utils.status_manager import StatusManager
from utils.bot_manager import bot_manager
from utils.markdown_utils import MarkdownV2Utils, escape_md, bold, code
from config import config

logger = logging.getLogger(__name__)
router = Router()



@router.message(Command("help"))
async def help_command(message: Message):
    """Показать доступные команды операторов"""
    if not message.message_thread_id:
        await message.reply(MarkdownV2Utils.format_error_message("Команда должна выполняться в теме чата"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    help_text = MarkdownV2Utils.format_command_help()
    
    await message.reply(help_text, parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command("hold"))
async def hold_chat(message: Message):
    """Пометить диалог как 'на удержании'"""

    if not message.message_thread_id:
        await message.reply(MarkdownV2Utils.format_error_message("Команда должна выполняться в теме чата"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    try:
        async with async_session() as session:
            db = DatabaseQueries(session)
            
            logger.info(f"Attempting to set hold status for thread {message.message_thread_id}")
            

            chat_data = await db.get_chat_by_topic(message.message_thread_id)
            if not chat_data:
                await message.reply(MarkdownV2Utils.format_error_message("Чат не найден"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            if chat_data.status == config.STATUS_HOLD:
                await message.reply(MarkdownV2Utils.format_info_message("Диалог уже на удержании"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            
            if chat_data.status in [config.STATUS_ENDED, config.STATUS_BANNED]:
                await message.reply(MarkdownV2Utils.format_error_message("Нельзя поставить на удержание завершенный или заблокированный диалог"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            main_bot = await bot_manager.get_bot(0)
            if not main_bot:
                await message.reply(MarkdownV2Utils.format_error_message("Главный бот недоступен"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            await StatusManager.update_status(chat_data.id, config.STATUS_HOLD, main_bot)
            
            await message.reply(f"🟡 Диалог помечен как {bold('на удержании')}", parse_mode=ParseMode.MARKDOWN_V2)
            
    except Exception as e:
        await message.reply(MarkdownV2Utils.format_error_message(f"Ошибка при постановке на удержание: {str(e)}"), parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command("ban"))
async def ban_user(message: Message):
    """Забанить пользователя"""

    if not message.message_thread_id:
        await message.reply(MarkdownV2Utils.format_error_message("Команда должна выполняться в теме чата"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    try:
        async with async_session() as session:
            db = DatabaseQueries(session)
            

            chat_data = await db.get_chat_by_topic(message.message_thread_id)
            if not chat_data:
                await message.reply(MarkdownV2Utils.format_error_message("Чат не найден"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            is_banned = await db.is_user_banned(chat_data.bot_id, chat_data.user_id)
            if is_banned:
                await message.reply(MarkdownV2Utils.format_info_message("Пользователь уже забанен"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            if chat_data.status == config.STATUS_BANNED:
                await message.reply(MarkdownV2Utils.format_info_message("Диалог уже заблокирован"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            await db.ban_user(chat_data.bot_id, chat_data.user_id)
            

            main_bot = await bot_manager.get_bot(0)
            if not main_bot:
                await message.reply(MarkdownV2Utils.format_error_message("Главный бот недоступен"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            await StatusManager.update_status(chat_data.id, config.STATUS_BANNED, main_bot)
            
            await message.reply(f"🔒 Пользователь {code(str(chat_data.user_id))} {bold('забанен')}", parse_mode=ParseMode.MARKDOWN_V2)
            
    except Exception as e:
        await message.reply(MarkdownV2Utils.format_error_message(f"Ошибка при блокировке пользователя: {str(e)}"), parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command("unhold"))
async def unhold_chat(message: Message):
    """Снять диалог с удержания"""

    if not message.message_thread_id:
        await message.reply(MarkdownV2Utils.format_error_message("Команда должна выполняться в теме чата"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    try:
        async with async_session() as session:
            db = DatabaseQueries(session)
            
            chat_data = await db.get_chat_by_topic(message.message_thread_id)
            if not chat_data:
                await message.reply(MarkdownV2Utils.format_error_message("Чат не найден"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            
            if chat_data.status != config.STATUS_HOLD:
                await message.reply(MarkdownV2Utils.format_info_message("Диалог не находится на удержании"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            
            main_bot = await bot_manager.get_bot(0)
            if not main_bot:
                await message.reply(MarkdownV2Utils.format_error_message("Главный бот недоступен"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            
            await StatusManager.update_status(chat_data.id, config.STATUS_WAITING, main_bot)
            
            await message.reply(f"🟢 Диалог {bold('снят с удержания')}", parse_mode=ParseMode.MARKDOWN_V2)
            
    except Exception as e:
        await message.reply(MarkdownV2Utils.format_error_message(f"Ошибка при снятии с удержания: {str(e)}"), parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command("unban"))
async def unban_user(message: Message):
    """Разбанить пользователя"""
    # Проверяем, что команда выполняется в теме
    if not message.message_thread_id:
        await message.reply(MarkdownV2Utils.format_error_message("Команда должна выполняться в теме чата"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    try:
        async with async_session() as session:
            db = DatabaseQueries(session)
            

            chat_data = await db.get_chat_by_topic(message.message_thread_id)
            if not chat_data:
                await message.reply(MarkdownV2Utils.format_error_message("Чат не найден"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            is_banned = await db.is_user_banned(chat_data.bot_id, chat_data.user_id)
            if not is_banned:
                await message.reply(MarkdownV2Utils.format_info_message("Пользователь не забанен"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            await db.unban_user(chat_data.bot_id, chat_data.user_id)
            

            main_bot = await bot_manager.get_bot(0)
            if not main_bot:
                await message.reply(MarkdownV2Utils.format_error_message("Главный бот недоступен"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            await StatusManager.update_status(chat_data.id, config.STATUS_WAITING, main_bot)
            
            await message.reply(f"🔓 Пользователь {code(str(chat_data.user_id))} {bold('разбанен')}", parse_mode=ParseMode.MARKDOWN_V2)
            
    except Exception as e:
        await message.reply(MarkdownV2Utils.format_error_message(f"Ошибка при разбане пользователя: {str(e)}"), parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command("end"))
async def end_chat(message: Message):
    """Завершить диалог"""

    if not message.message_thread_id:
        await message.reply(MarkdownV2Utils.format_error_message("Команда должна выполняться в теме чата"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    try:
        async with async_session() as session:
            db = DatabaseQueries(session)
            

            chat_data = await db.get_chat_by_topic(message.message_thread_id)
            if not chat_data:
                await message.reply(MarkdownV2Utils.format_error_message("Чат не найден"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            main_bot = await bot_manager.get_bot(0)
            if not main_bot:
                await message.reply(MarkdownV2Utils.format_error_message("Главный бот недоступен"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            

            await StatusManager.update_status(chat_data.id, config.STATUS_ENDED, main_bot)
            
            await message.reply(f"❌ Диалог {bold('завершен')}", parse_mode=ParseMode.MARKDOWN_V2)
            
    except Exception as e:
        await message.reply(MarkdownV2Utils.format_error_message(f"Ошибка при завершении диалога: {str(e)}"), parse_mode=ParseMode.MARKDOWN_V2)

@router.message(F.message_thread_id)
async def operator_reply(message: Message):
    """Ответ оператора пользователю"""
    # Пропускаем команды и системные сообщения
    if (message.text and message.text.startswith('/')) or message.content_type == ContentType.FORUM_TOPIC_EDITED:
        return
    
    # Пропускаем сообщения без контента
    if not any([
        message.text, message.photo, message.video, message.document,
        message.voice, message.video_note, message.sticker, message.animation,
        message.audio, message.location, message.contact, message.poll, message.venue
    ]):
        return
    
    try:
        from utils.media_group_handler import media_group_handler
        
        async with async_session() as session:
            db = DatabaseQueries(session)

            chat_data = await db.get_chat_by_topic(message.message_thread_id)
            if not chat_data:
                logger.warning(f"Чат не найден для темы {message.message_thread_id}")
                return
            
            # Проверяем статус чата
            if chat_data.status in [config.STATUS_ENDED, config.STATUS_BANNED]:
                await message.reply(MarkdownV2Utils.format_info_message("Диалог завершен или пользователь заблокирован"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            
            # Получаем главного бота для обновления статуса
            main_bot = await bot_manager.get_bot(0)
            if not main_bot:
                await message.reply(MarkdownV2Utils.format_error_message("Главный бот недоступен"), parse_mode=ParseMode.MARKDOWN_V2)
                return
            
            # Используем обработчик медиагрупп для отправки сообщения пользователю
            await media_group_handler.handle_message(message, chat_data, main_bot, is_from_user=False)
            
            # Обновляем статус только если чат не на удержании
            if chat_data.status != config.STATUS_HOLD:
                await StatusManager.update_status(chat_data.id, config.STATUS_ANSWERED, main_bot)
                logger.info(f"Статус чата {chat_data.id} обновлен на ANSWERED")
            elif chat_data.status == config.STATUS_HOLD:
                logger.info(f"Сохраняем статус HOLD для чата {chat_data.id} при ответе оператора")
                
    except Exception as e:
        logger.error(f"Ошибка в ответе оператора для темы {message.message_thread_id}: {str(e)}", exc_info=True)
        await message.reply(MarkdownV2Utils.format_error_message(f"Ошибка при отправке сообщения: {str(e)}"), parse_mode=ParseMode.MARKDOWN_V2)