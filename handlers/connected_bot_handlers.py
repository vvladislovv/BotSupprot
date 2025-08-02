import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database.database import async_session
from database.queries import DatabaseQueries
from database.models import ConnectedBot
from utils.message_handler import MessageHandler
from utils.redis_manager import redis_manager
from config import config
from utils.text_utils import get_text

logger = logging.getLogger(__name__)

class ConnectedBotHandlers:

    
    @staticmethod
    def create_handlers(bot_db_id: int) -> Router:

        router = Router()
        
        @router.message(Command("start"))
        async def connected_bot_start(message: Message):
            """Обработка /start в подключенном боте"""
            try:
                async with async_session() as session:
                    db = DatabaseQueries(session)
                    
                    # Проверяем бан
                    if await db.is_user_banned(bot_db_id, message.from_user.id):
                        logger.info(f"Заблокированный пользователь {message.from_user.id} попытался написать боту {bot_db_id}")
                        return
                    
                    # Получаем данные бота из БД
                    bot_data = await session.get(ConnectedBot, bot_db_id)
                    if not bot_data:
                        logger.error(f"Бот с ID {bot_db_id} не найден в БД")
                        return
                    
                    # Получаем или создаем чат
                    chat_data = await db.get_chat(bot_db_id, message.from_user.id)
                    if not chat_data:
                        chat_data = await db.create_chat(
                            bot_id=bot_db_id,
                            user_id=message.from_user.id,
                            username=message.from_user.username,
                            first_name=message.from_user.first_name,
                            last_name=message.from_user.last_name
                        )
                    
                    # Определяем язык
                    lang = ConnectedBotHandlers._detect_language(message.from_user.language_code)
                    
                    # Получаем текст приветствия
                    welcome_text = get_text("welcome_message", lang)
                    
                    from aiogram.enums import ParseMode
                    
                    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN_V2)
                    logger.info(f"Отправлено приветствие пользователю {message.from_user.id} от бота {bot_db_id}")
                    
            except Exception as e:
                logger.error(f"Ошибка в обработчике /start для бота {bot_db_id}: {e}")
        
        @router.message(Command("info"))
        async def connected_bot_info(message: Message):
            """Обработка /info в подключенном боте"""
            try:
                async with async_session() as session:
                    db = DatabaseQueries(session)
                    
                    # Проверяем бан
                    if await db.is_user_banned(bot_db_id, message.from_user.id):
                        return
                    
                    # Получаем данные бота из БД
                    bot_data = await session.get(ConnectedBot, bot_db_id)
                    if not bot_data:
                        return
                    
                    # Определяем язык
                    lang = ConnectedBotHandlers._detect_language(message.from_user.language_code)
                    
                    # Получаем информационный текст
                    info_text = get_text("info_text", lang)
                    
                    from aiogram.enums import ParseMode
                    
                    await message.answer(info_text, parse_mode=ParseMode.MARKDOWN_V2)
                    logger.info(f"Отправлена информация пользователю {message.from_user.id} от бота {bot_db_id}")
                    
            except Exception as e:
                logger.error(f"Ошибка в обработчике /info для бота {bot_db_id}: {e}")
        
        @router.message()
        async def connected_bot_message(message: Message):
            """Обработка всех остальных сообщений"""
            try:
                # Импортируем здесь, чтобы избежать циркулярных зависимостей
                from utils.bot_manager import bot_manager
                from utils.media_group_handler import media_group_handler
                
                async with async_session() as session:
                    db = DatabaseQueries(session)
                    
                    # Проверяем бан
                    if await db.is_user_banned(bot_db_id, message.from_user.id):
                        return
                    
                    # Получаем данные бота из БД (убираем кеширование для стабильности)
                    bot_data = await session.get(ConnectedBot, bot_db_id)
                    if not bot_data or not bot_data.group_id:
                        logger.warning(f"Бот {bot_db_id} не настроен или не привязан к группе")
                        return
                    
                    # Получаем или создаем чат
                    chat_data = await db.get_chat(bot_db_id, message.from_user.id)
                    if not chat_data:
                        chat_data = await db.create_chat(
                            bot_id=bot_db_id,
                            user_id=message.from_user.id,
                            username=message.from_user.username,
                            first_name=message.from_user.first_name,
                            last_name=message.from_user.last_name
                        )
                        session.add(chat_data)
                        await session.commit()
                        await session.refresh(chat_data)
                    
                    # Устанавливаем связь с ботом для MessageHandler
                    chat_data.bot = bot_data
                    
                    # Получаем главного бота для пересылки
                    main_bot = await bot_manager.get_bot(0)  # Главный бот с ID 0
                    if main_bot:
                        # Обновляем статус на "ожидает ответа" только если чат не на удержании
                        from utils.status_manager import StatusManager
                        if chat_data.status != config.STATUS_HOLD:
                            # Используем обработчик медиагрупп для всех сообщений
                            await media_group_handler.handle_message(message, chat_data, main_bot, is_from_user=True)
                            await StatusManager.update_status(chat_data.id, config.STATUS_WAITING, main_bot)
                            logger.info(f"Сообщение от пользователя {message.from_user.id} обработано через медиа-обработчик")
                        else:
                            # Если чат на удержании, только отправляем сообщение пользователю, не пересылаем
                            lang = ConnectedBotHandlers._detect_language(message.from_user.language_code)
                            from aiogram.enums import ParseMode
                            await message.answer(get_text("hold_message", lang), parse_mode=ParseMode.MARKDOWN_V2)
                            logger.info(f"Сообщение от пользователя {message.from_user.id} проигнорировано из-за статуса удержания")
                    else:
                        logger.error("Главный бот недоступен для пересылки сообщения")
                        
            except Exception as e:
                logger.error(f"Ошибка в обработчике сообщений для бота {bot_db_id}: {e}")
        
        return router
    
    @staticmethod
    def _detect_language(language_code: str) -> str:
        """
        Определение языка пользователя
        
        Args:
            language_code: Код языка от Telegram
            
        Returns:
            'ru' или 'en'
        """
        if language_code and language_code.startswith('ru'):
            return 'ru'
        return 'en'
