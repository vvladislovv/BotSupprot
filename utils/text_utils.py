"""Utility module for managing language-specific texts in the CRM bot project."""

from utils.markdown_utils import MarkdownV2Utils, escape_md, bold, italic, code

def get_text(key: str, lang: str = "en") -> str:
    """
    Retrieve a language-specific text string based on the provided key and language code.
    All texts are automatically formatted for Markdown V2.
    
    Args:
        key: The identifier for the text string.
        lang: The language code ('ru' for Russian, any other value for English).
    
    Returns:
        The text string in the specified language, formatted for Markdown V2.
    """
    texts = {
        "welcome_message": {
            "ru": f"👋 {bold('Добро пожаловать!')} Чем могу помочь?",
            "en": f"👋 {bold('Welcome!')} How can I help you?"
        },
        "info_text": {
            "ru": f"""ℹ️ {bold('Информация о боте')}

Этот бот предоставляет поддержку клиентов\\. Свяжитесь с нами, если у вас есть вопросы\\.""",
            "en": f"""ℹ️ {bold('Bot Information')}

This bot provides customer support\\. Contact us if you have any questions\\."""
        },
        "hold_message": {
            "ru": f"🟡 Ваш запрос находится на {bold('удержании')}\\. Мы свяжемся с вами в ближайшее время\\.",
            "en": f"🟡 Your request is on {bold('hold')}\\. We will contact you shortly\\."
        },
        "main_menu": {
            "ru": f"🏠 {bold('Главное меню')}\n\nВыберите действие\\:",
            "en": f"🏠 {bold('Main Menu')}\n\nChoose an action\\:"
        },
        "manage_subscription": {
            "ru": f"🔧 {bold('Управление подпиской')}\n\nЭта функция находится в разработке\\.",
            "en": f"🔧 {bold('Manage Subscription')}\n\nThis feature is under development\\."
        },
        "new_connection": {
            "ru": f"""🔗 {bold('Новое подключение бота')}

Для подключения нового бота\\:
1\\. Создайте бота через @BotFather
2\\. Получите токен бота
3\\. Нажмите {italic('Подключить бота')} и отправьте токен""",
            "en": f"""🔗 {bold('New Bot Connection')}

To connect a new bot\\:
1\\. Create a bot via @BotFather
2\\. Get the bot token
3\\. Click {italic('Connect Bot')} and send the token"""
        },
        "connect_bot": {
            "ru": f"🤖 {bold('Отправьте токен бота')}\n\nПолучить токен можно у @BotFather",
            "en": f"🤖 {bold('Send bot token')}\n\nYou can get the token from @BotFather"
        },
        "bot_already_connected": {
            "ru": f"❌ {bold('Этот бот уже подключен!')}",
            "en": f"❌ {bold('This bot is already connected!')}"
        },
        "bot_connection_success": {
            "ru": f"✅ Бот @{{username}} {bold('успешно подключен!')}\n\nТеперь настройте его\\:",
            "en": f"✅ Bot @{{username}} {bold('successfully connected!')}\n\nNow configure it\\:"
        },
        "bot_connection_error": {
            "ru": f"❌ {bold('Ошибка подключения бота')}\\: {{error}}\n\nПроверьте токен и попробуйте снова\\.",
            "en": f"❌ {bold('Bot connection error')}\\: {{error}}\n\nCheck the token and try again\\."
        },
        "bot_management": {
            "ru": f"🤖 {bold('Управление ботом')} @{{username}}\n\nВыберите действие\\:",
            "en": f"🤖 {bold('Managing bot')} @{{username}}\n\nChoose an action\\:"
        },
        "bot_not_found": {
            "ru": f"❌ {bold('Бот не найден')}",
            "en": f"❌ {bold('Bot not found')}"
        },
        "choose_group": {
            "ru": f"""📋 {bold('Выбор группы')}

Для работы системы нужно\\:
1\\. Создать супергруппу с темами
2\\. Добавить {bold('ГЛАВНОГО бота')} \\(этого\\) в группу как админа
3\\. Дать права на управление темами

⚠️ {bold('ВАЖНО')}\\: В группу добавляется только главный бот\\!
Подключенные боты работают отдельно и передают сообщения главному боту\\.

Нажмите кнопку ниже, чтобы выбрать группу ⬇️""",
            "en": f"""📋 {bold('Choose Group')}

For the system to work\\:
1\\. Create a supergroup with topics
2\\. Add the {bold('MAIN bot')} \\(this one\\) to the group as admin
3\\. Give topic management rights

⚠️ {bold('IMPORTANT')}\\: Only the main bot is added to the group\\!
Connected bots work separately and send messages to the main bot\\.

Press the button below to choose a group ⬇️"""
        },
        "choose_group_button": {
            "ru": "🔗 Выбрать группу",
            "en": "🔗 Choose Group"
        },
        "bot_settings": {
            "ru": f"⚙️ {bold('Настройки бота')}\n\nВыберите что хотите изменить\\:",
            "en": f"⚙️ {bold('Bot Settings')}\n\nChoose what you want to change\\:"
        },
        "edit_welcome": {
            "ru": f"📝 {bold('Отправьте новый текст приветствия')}\\:",
            "en": f"📝 {bold('Send new welcome text')}\\:"
        },
        "welcome_text_updated": {
            "ru": f"✅ {bold('Текст приветствия обновлен!')}",
            "en": f"✅ {bold('Welcome text updated!')}"
        },
        "edit_info": {
            "ru": f"📝 {bold('Отправьте новый информационный текст')}\\:",
            "en": f"📝 {bold('Send new info text')}\\:"
        },
        "info_text_updated": {
            "ru": f"✅ {bold('Информационный текст обновлен!')}",
            "en": f"✅ {bold('Info text updated!')}"
        },
        "main_bot_unavailable": {
            "ru": f"❌ {bold('Главный бот недоступен!')}",
            "en": f"❌ {bold('Main bot is not available!')}"
        },
        "main_bot_not_admin": {
            "ru": f"❌ {bold('Главный бот должен быть администратором группы!')}",
            "en": f"❌ {bold('Main bot must be an administrator of the group!')}"
        },
        "rights_check_error": {
            "ru": f"❌ {bold('Ошибка проверки прав')}\\: {{error}}",
            "en": f"❌ {bold('Rights check error')}\\: {{error}}"
        },
        "group_linked_success": {
            "ru": f"✅ {bold('Группа успешно привязана!')}\n\nГруппа\\: {{title}}\nID\\: {code('{group_id}')}",
            "en": f"✅ {bold('Group successfully linked!')}\n\nGroup\\: {{title}}\nID\\: {code('{group_id}')}"
        },
        "group_linking_error": {
            "ru": f"❌ {bold('Ошибка при привязке группы')}\\: {{error}}\n\nПроверьте, что бот добавлен в группу как администратор\\.",
            "en": f"❌ {bold('Error linking group')}\\: {{error}}\n\nMake sure the bot is added to the group as administrator\\."
        },
        "stop_bot_confirmation": {
            "ru": f"⏸️ Вы уверены, что хотите {bold('остановить бота')}?\n\nОн перестанет отвечать пользователям\\.",
            "en": f"⏸️ Are you sure you want to {bold('stop the bot')}?\n\nIt will stop responding to users\\."
        },
        "bot_stopped": {
            "ru": f"⏸️ {bold('Бот остановлен')}",
            "en": f"⏸️ {bold('Bot stopped')}"
        },
        "bot_started": {
            "ru": f"▶️ {bold('Бот запущен')}",
            "en": f"▶️ {bold('Bot started')}"
        },
        "bot_start_error": {
            "ru": f"❌ {bold('Ошибка запуска бота')}\\: {{error}}",
            "en": f"❌ {bold('Bot start error')}\\: {{error}}"
        },
        "delete_bot_confirmation": {
            "ru": f"🗑️ Вы уверены, что хотите {bold('удалить бота')}?\n\n⚠️ {bold('Это действие нельзя отменить!')}",
            "en": f"🗑️ Are you sure you want to {bold('delete the bot')}?\n\n⚠️ {bold('This action cannot be undone!')}"
        },
        "bot_deleted": {
            "ru": f"🗑️ {bold('Бот удален')}",
            "en": f"🗑️ {bold('Bot deleted')}"
        }
    }
    
    text = texts.get(key, {"ru": "", "en": ""})
    return text["ru"] if lang == "ru" else text["en"]
