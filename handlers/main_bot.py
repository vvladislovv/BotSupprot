from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Chat
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot

from database.database import async_session
from database.queries import DatabaseQueries
from database.models import ConnectedBot
from sqlalchemy import select
from keyboards.inline import *
from utils.bot_manager import bot_manager
from utils.text_utils import get_text

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    KeyboardButtonRequestChat, ChatAdministratorRights
)

user_admin_rights = ChatAdministratorRights(
    is_anonymous=False,
    can_manage_chat=True,
    can_delete_messages=True,
    can_manage_video_chats=False,
    can_restrict_members=False,
    can_promote_members=False,
    can_change_info=False,
    can_invite_users=True,
    can_post_stories=False,
    can_edit_stories=False,
    can_delete_stories=False,
    can_manage_topics=True
)

bot_admin_rights = ChatAdministratorRights(
    is_anonymous=False,
    can_manage_chat=True,
    can_delete_messages=True,
    can_manage_video_chats=False,
    can_restrict_members=False,
    can_promote_members=False,
    can_change_info=False,
    can_invite_users=True,
    can_post_stories=False,
    can_edit_stories=False,
    can_delete_stories=False,
    can_manage_topics=True)

# Состояния FSM
class BotConnectionStates(StatesGroup):
    waiting_for_token = State()
    waiting_for_welcome_text = State()
    waiting_for_info_text = State()
    waiting_for_group_id = State()

router = Router()

@router.message(Command("start"))
async def start_command(message: Message, lang: str):
    """Обработка команды /start"""
    async with async_session() as session:
        db = DatabaseQueries(session)
        user_bots = await db.get_user_bots(message.from_user.id)
    
    text = get_text("welcome_message", lang)
    
    from aiogram.enums import ParseMode
    
    await message.answer(
        text,
        reply_markup=main_menu_keyboard(user_bots, lang),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, lang: str):
    """Возврат в главное меню"""
    async with async_session() as session:
        db = DatabaseQueries(session)
        user_bots = await db.get_user_bots(callback.from_user.id)
    
    text = get_text("main_menu", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(
        text,
        reply_markup=main_menu_keyboard(user_bots, lang),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data == "manage_subscription")
async def manage_subscription(callback: CallbackQuery, lang: str):
    """Управление подпиской (заглушка)"""
    text = get_text("manage_subscription", lang)
    
    # callback.answer не поддерживает parse_mode, поэтому экранируем текст вручную
    from utils.markdown_utils import escape_md
    # Убираем markdown форматирование для callback.answer
    plain_text = text.replace('*', '').replace('_', '').replace('`', '').replace('\\', '')
    
    await callback.answer(plain_text, show_alert=True)

@router.callback_query(F.data == "new_connection")
async def new_connection(callback: CallbackQuery, lang: str):
    """Новое подключение"""
    text = get_text("new_connection", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(
        text,
        reply_markup=new_connection_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data == "connect_bot")
async def connect_bot(callback: CallbackQuery, state: FSMContext, lang: str):
    """Подключение бота"""
    text = get_text("connect_bot", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(BotConnectionStates.waiting_for_token)

@router.message(StateFilter(BotConnectionStates.waiting_for_token))
async def process_bot_token(message: Message, state: FSMContext, lang: str):
    """Обработка токена бота"""
    token = message.text.strip()
    
    try:
        # Проверяем токен
        temp_bot = Bot(token=token)
        bot_info = await temp_bot.get_me()
        await temp_bot.session.close()
        
        # Проверяем, не подключен ли уже этот бот
        async with async_session() as session:
            db = DatabaseQueries(session)
            existing_bot = await db.get_connected_bot_by_token(token)
            
            if existing_bot:
                text = get_text("bot_already_connected", lang)
                from aiogram.enums import ParseMode
                await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)
                return
            
            # Создаем запись в БД
            bot_data = await db.create_connected_bot(
                user_id=message.from_user.id,
                bot_token=token,
                bot_username=bot_info.username,
                bot_id=bot_info.id
            )
            
            # Добавляем в менеджер ботов
            await bot_manager.add_bot(bot_data)
        
        from utils.markdown_utils import escape_md
        text = get_text("bot_connection_success", lang).format(username=escape_md(bot_info.username))
        
        from aiogram.enums import ParseMode
        
        await message.answer(
            text,
            reply_markup=bot_management_keyboard(bot_data.id, lang, bot_data.is_active),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
    except Exception as e:
        from utils.markdown_utils import escape_md
        text = get_text("bot_connection_error", lang).format(error=escape_md(str(e)))
        
        from aiogram.enums import ParseMode
        
        await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)
    
    await state.clear()

@router.callback_query(F.data.startswith("bot_manage:"))
async def bot_manage(callback: CallbackQuery, lang: str):
    """Управление ботом"""
    bot_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        db = DatabaseQueries(session)

        result = await session.execute(
            select(ConnectedBot).where(ConnectedBot.id == bot_id)
        )
        bot_data = result.scalar_one_or_none()
        
        if not bot_data:
            # callback.answer не поддерживает markdown, используем обычный текст
            await callback.answer("Бот не найден" if lang == 'ru' else "Bot not found")
            return
    
    from utils.markdown_utils import escape_md
    text = get_text("bot_management", lang).format(username=escape_md(bot_data.bot_username))
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(
        text,
        reply_markup=bot_management_keyboard(bot_id, lang, bot_data.is_active),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data.startswith("choose_group:"))
async def choose_group(callback: CallbackQuery, state: FSMContext, lang: str):
    """Выбор группы для бота через RequestChat"""
    bot_id = int(callback.data.split(":")[1])

    text = get_text("choose_group", lang)
    button_text = get_text("choose_group_button", lang)

    # Кнопка запроса группы (RequestChat) - добавляет главного бота
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text=button_text,
                request_chat=KeyboardButtonRequestChat(
                    request_id=1,
                    chat_is_channel=False,
                    chat_is_forum=True,
                    user_administrator_rights=user_admin_rights,
                    bot_administrator_rights=bot_admin_rights,
                    request_title=True
                )
            )
        ]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    from aiogram.enums import ParseMode
    
    await callback.message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(BotConnectionStates.waiting_for_group_id)
    await state.update_data(bot_id=bot_id)

@router.callback_query(F.data.startswith("bot_settings:"))
async def bot_settings(callback: CallbackQuery, lang: str):
    """Настройки бота"""
    bot_id = int(callback.data.split(":")[1])
    
    text = get_text("bot_settings", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(
        text,
        reply_markup=settings_keyboard(bot_id, lang),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data.startswith("edit_welcome:"))
async def edit_welcome(callback: CallbackQuery, state: FSMContext, lang: str):
    """Редактирование приветствия"""
    bot_id = int(callback.data.split(":")[1])
    
    text = get_text("edit_welcome", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(BotConnectionStates.waiting_for_welcome_text)
    await state.update_data(bot_id=bot_id)

@router.message(StateFilter(BotConnectionStates.waiting_for_welcome_text))
async def process_welcome_text(message: Message, state: FSMContext, lang: str):
    """Обработка текста приветствия"""
    data = await state.get_data()
    bot_id = data['bot_id']
    
    async with async_session() as session:
        db = DatabaseQueries(session)
        
        if lang == 'ru':
            await db.update_bot_settings(bot_id, welcome_text_ru=message.text)
        else:
            await db.update_bot_settings(bot_id, welcome_text_en=message.text)
    
    text = get_text("welcome_text_updated", lang)
    
    # Get bot data to check if it's active
    async with async_session() as session:
        db = DatabaseQueries(session)
        result = await session.execute(
            select(ConnectedBot).where(ConnectedBot.id == bot_id)
        )
        bot_data = result.scalar_one_or_none()
        is_active = bot_data.is_active if bot_data else True
    
    from aiogram.enums import ParseMode
    
    await message.answer(
        text,
        reply_markup=bot_management_keyboard(bot_id, lang, is_active),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await state.clear()

@router.callback_query(F.data.startswith("edit_info:"))
async def edit_info(callback: CallbackQuery, state: FSMContext, lang: str):
    """Редактирование информации"""
    bot_id = int(callback.data.split(":")[1])
    
    text = get_text("edit_info", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(BotConnectionStates.waiting_for_info_text)
    await state.update_data(bot_id=bot_id)

@router.message(StateFilter(BotConnectionStates.waiting_for_info_text))
async def process_info_text(message: Message, state: FSMContext, lang: str):
    """Обработка информационного текста"""
    data = await state.get_data()
    bot_id = data['bot_id']
    
    async with async_session() as session:
        db = DatabaseQueries(session)
        
        if lang == 'ru':
            await db.update_bot_settings(bot_id, info_text_ru=message.text)
        else:
            await db.update_bot_settings(bot_id, info_text_en=message.text)
    
    text = get_text("info_text_updated", lang)
    
    # Get bot data to check if it's active
    async with async_session() as session:
        db = DatabaseQueries(session)
        result = await session.execute(
            select(ConnectedBot).where(ConnectedBot.id == bot_id)
        )
        bot_data = result.scalar_one_or_none()
        is_active = bot_data.is_active if bot_data else True
    
    from aiogram.enums import ParseMode
    
    await message.answer(
        text,
        reply_markup=bot_management_keyboard(bot_id, lang, is_active),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await state.clear()

@router.message(StateFilter(BotConnectionStates.waiting_for_group_id))
async def process_group_selection(message: Message, state: FSMContext, lang: str):
    """Обработка выбранной группы через RequestChat"""

    data = await state.get_data()
    bot_id = data['bot_id']

    try:
        group_id = message.chat_shared.chat_id
        group_title = message.chat_shared.title or "Unknown"


        async with async_session() as session:
            db = DatabaseQueries(session)
            result = await session.execute(
                select(ConnectedBot).where(ConnectedBot.id == bot_id)
            )
            bot_data = result.scalar_one_or_none()

            if not bot_data:
                from utils.markdown_utils import escape_md
                text = escape_md("❌ Бот не найден!") if lang == 'ru' else escape_md("❌ Bot not found!")
                from aiogram.enums import ParseMode
                await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN_V2)
                await state.clear()
                return


        main_bot = bot_manager.connected_bots.get(0)  # Главный бот с ID 0
        if not main_bot:
            text = get_text("main_bot_unavailable", lang)
            from aiogram.enums import ParseMode
            await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN_V2)
            await state.clear()
            return

        # Проверка прав главного бота в группе
        try:
            me = await main_bot.get_me()
            bot_member = await main_bot.get_chat_member(group_id, me.id)
            if bot_member.status not in ['administrator', 'creator']:
                text = get_text("main_bot_not_admin", lang)
                from aiogram.enums import ParseMode
                await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN_V2)
                await state.clear()
                return
        except Exception as e:
            from utils.markdown_utils import escape_md
            text = get_text("rights_check_error", lang).format(error=escape_md(str(e)))
            from aiogram.enums import ParseMode
            await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN_V2)
            await state.clear()
            return

        # Обновляем группу в БД
        async with async_session() as session:
            db = DatabaseQueries(session)
            await db.update_bot_group(bot_id, group_id)

        from utils.markdown_utils import escape_md
        text = get_text("group_linked_success", lang).format(title=escape_md(group_title), group_id=group_id)

        from aiogram.enums import ParseMode

        await message.answer(
            text,
            reply_markup=bot_management_keyboard(bot_id, lang, bot_data.is_active),
            parse_mode=ParseMode.MARKDOWN_V2
        )

    except Exception as e:
        from utils.markdown_utils import escape_md
        text = get_text("group_linking_error", lang).format(error=escape_md(str(e)))
        from aiogram.enums import ParseMode
        await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN_V2)

    await state.clear()

@router.callback_query(F.data.startswith("stop_bot:"))
async def stop_bot(callback: CallbackQuery, lang: str):
    """Подтверждение остановки бота"""
    bot_id = int(callback.data.split(":")[1])
    
    text = get_text("stop_bot_confirmation", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(
        text,
        reply_markup=confirmation_keyboard("stop", bot_id, lang),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data.startswith("confirm_stop:"))
async def confirm_stop_bot(callback: CallbackQuery, lang: str):
    """Остановка бота"""
    bot_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        db = DatabaseQueries(session)
        await db.update_bot_settings(bot_id, is_active=False)
    
    await bot_manager.stop_bot(bot_id)
    
    text = get_text("bot_stopped", lang)
    
    # callback.answer не поддерживает markdown, убираем форматирование
    plain_text = text.replace('*', '').replace('_', '').replace('`', '').replace('\\', '')
    await callback.answer(plain_text)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(
        text,
        reply_markup=bot_management_keyboard(bot_id, lang, False),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data.startswith("start_bot:"))
async def start_bot(callback: CallbackQuery, lang: str):
    """Запуск бота"""
    bot_id = int(callback.data.split(":")[1])
    
    try:
        async with async_session() as session:
            db = DatabaseQueries(session)
            result = await session.execute(
                select(ConnectedBot).where(ConnectedBot.id == bot_id)
            )
            bot_data = result.scalar_one_or_none()
            
            if not bot_data:
                # callback.answer не поддерживает markdown, используем обычный текст
                plain_text = "Бот не найден" if lang == 'ru' else "Bot not found"
                await callback.answer(plain_text)
                return
        

        async with async_session() as session:
            db = DatabaseQueries(session)
            await db.update_bot_settings(bot_id, is_active=True)

        await bot_manager.start_bot(bot_id)
        
        text = get_text("bot_started", lang)
        
        # callback.answer не поддерживает markdown, убираем форматирование
        plain_text = text.replace('*', '').replace('_', '').replace('`', '').replace('\\', '')
        await callback.answer(plain_text)
        
        from aiogram.enums import ParseMode
        
        await callback.message.edit_text(
            text,
            reply_markup=bot_management_keyboard(bot_id, lang, True),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
    except Exception as e:
        from utils.markdown_utils import escape_md
        text = get_text("bot_start_error", lang).format(error=escape_md(str(e)))
        
        # callback.answer не поддерживает markdown, убираем форматирование
        plain_text = text.replace('*', '').replace('_', '').replace('`', '').replace('\\', '')
        await callback.answer(plain_text, show_alert=True)

@router.callback_query(F.data.startswith("delete_bot:"))
async def delete_bot(callback: CallbackQuery, lang: str):
    """Подтверждение удаления бота"""
    bot_id = int(callback.data.split(":")[1])
    
    text = get_text("delete_bot_confirmation", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(
        text,
        reply_markup=confirmation_keyboard("delete", bot_id, lang),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_bot(callback: CallbackQuery, lang: str):
    """Удаление бота"""
    bot_id = int(callback.data.split(":")[1])
    
    # Удаляем из менеджера
    await bot_manager.remove_bot(bot_id)
    
    # Удаляем из БД
    async with async_session() as session:
        db = DatabaseQueries(session)
        await db.delete_bot(bot_id)
    
    text = get_text("bot_deleted", lang)
    
    # callback.answer не поддерживает markdown, убираем форматирование
    plain_text = text.replace('*', '').replace('_', '').replace('`', '').replace('\\', '')
    await callback.answer(plain_text)
    
    # Возвращаемся в главное меню
    async with async_session() as session:
        db = DatabaseQueries(session)
        user_bots = await db.get_user_bots(callback.from_user.id)
    
    main_text = get_text("main_menu", lang)
    
    from aiogram.enums import ParseMode
    
    await callback.message.edit_text(
        main_text,
        reply_markup=main_menu_keyboard(user_bots, lang),
        parse_mode=ParseMode.MARKDOWN_V2
    )
