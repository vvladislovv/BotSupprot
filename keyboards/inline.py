from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard(user_bots=None, lang='ru'):
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    
    if lang == 'ru':
        builder.add(InlineKeyboardButton(text="Управление подпиской", callback_data="manage_subscription"))
        builder.add(InlineKeyboardButton(text="Новое подключение", callback_data="new_connection"))
    else:
        builder.add(InlineKeyboardButton(text="Manage Subscription", callback_data="manage_subscription"))
        builder.add(InlineKeyboardButton(text="New Connection", callback_data="new_connection"))
    
    builder.adjust(1)

    if user_bots:
        for bot in user_bots:
            builder.add(InlineKeyboardButton(
                text=f"🤖 @{bot.bot_username}",
                callback_data=f"bot_manage:{bot.id}"
            ))
    
    return builder.as_markup()

def new_connection_keyboard(lang='ru'):
    """Меню нового подключения"""
    builder = InlineKeyboardBuilder()
    
    if lang == 'ru':
        builder.add(InlineKeyboardButton(text="Подключить бота", callback_data="connect_bot"))
        builder.add(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    else:
        builder.add(InlineKeyboardButton(text="Connect Bot", callback_data="connect_bot"))
        builder.add(InlineKeyboardButton(text="Back", callback_data="back_to_main"))
    
    builder.adjust(1)
    return builder.as_markup()

def bot_management_keyboard(bot_id: int, lang='ru', is_active=True):
    """Меню управления ботом"""
    builder = InlineKeyboardBuilder()
    
    if lang == 'ru':
        builder.add(InlineKeyboardButton(text="Выбрать группу", callback_data=f"choose_group:{bot_id}"))
        builder.add(InlineKeyboardButton(text="Настройки", callback_data=f"bot_settings:{bot_id}"))
        
        # Динамически добавляем кнопку запуска/остановки
        if is_active:
            builder.add(InlineKeyboardButton(text="Остановить", callback_data=f"stop_bot:{bot_id}"))
        else:
            builder.add(InlineKeyboardButton(text="Запустить", callback_data=f"start_bot:{bot_id}"))
            
        builder.add(InlineKeyboardButton(text="Удалить", callback_data=f"delete_bot:{bot_id}"))
        builder.add(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    else:
        builder.add(InlineKeyboardButton(text="Choose Group", callback_data=f"choose_group:{bot_id}"))
        builder.add(InlineKeyboardButton(text="Settings", callback_data=f"bot_settings:{bot_id}"))
        
        # Динамически добавляем кнопку запуска/остановки
        if is_active:
            builder.add(InlineKeyboardButton(text="Stop", callback_data=f"stop_bot:{bot_id}"))
        else:
            builder.add(InlineKeyboardButton(text="Start", callback_data=f"start_bot:{bot_id}"))
            
        builder.add(InlineKeyboardButton(text="Delete", callback_data=f"delete_bot:{bot_id}"))
        builder.add(InlineKeyboardButton(text="Back", callback_data="back_to_main"))
    
    builder.adjust(1)
    return builder.as_markup()

def settings_keyboard(bot_id: int, lang='ru'):
    """Меню настроек бота"""
    builder = InlineKeyboardBuilder()
    
    if lang == 'ru':
        builder.add(InlineKeyboardButton(text="Изменить приветствие", callback_data=f"edit_welcome:{bot_id}"))
        builder.add(InlineKeyboardButton(text="Изменить инфо", callback_data=f"edit_info:{bot_id}"))
        builder.add(InlineKeyboardButton(text="Назад", callback_data=f"bot_manage:{bot_id}"))
    else:
        builder.add(InlineKeyboardButton(text="Edit Welcome", callback_data=f"edit_welcome:{bot_id}"))
        builder.add(InlineKeyboardButton(text="Edit Info", callback_data=f"edit_info:{bot_id}"))
        builder.add(InlineKeyboardButton(text="Back", callback_data=f"bot_manage:{bot_id}"))
    
    builder.adjust(1)
    return builder.as_markup()

def confirmation_keyboard(action: str, bot_id: int, lang='ru'):
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    
    if lang == 'ru':
        builder.add(InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}:{bot_id}"))
        builder.add(InlineKeyboardButton(text="❌ Нет", callback_data=f"bot_manage:{bot_id}"))
    else:
        builder.add(InlineKeyboardButton(text="✅ Yes", callback_data=f"confirm_{action}:{bot_id}"))
        builder.add(InlineKeyboardButton(text="❌ No", callback_data=f"bot_manage:{bot_id}"))
    
    builder.adjust(2)
    return builder.as_markup()
