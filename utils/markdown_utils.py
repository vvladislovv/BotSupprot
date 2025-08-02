import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MarkdownV2Utils:
    """Утилиты для работы с Markdown V2 форматированием"""
    
    @staticmethod
    def escape_markdown_v2(text: str) -> str:
        """
        Экранирование специальных символов для Markdown V2
        
        Args:
            text: Исходный текст
            
        Returns:
            Экранированный текст
        """
        if not text:
            return ""
        
        # Символы, которые нужно экранировать в Markdown V2
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        result = text
        for char in special_chars:
            result = result.replace(char, f'\\{char}')
        
        return result
    
    @staticmethod
    def bold(text: str) -> str:
        """Жирный текст"""
        if not text:
            return ""
        escaped = MarkdownV2Utils.escape_markdown_v2(text)
        return f"*{escaped}*"
    
    @staticmethod
    def italic(text: str) -> str:
        """Курсив"""
        if not text:
            return ""
        escaped = MarkdownV2Utils.escape_markdown_v2(text)
        return f"_{escaped}_"
    
    @staticmethod
    def code(text: str) -> str:
        """Моноширинный код"""
        if not text:
            return ""
        # Код не экранируем
        return f"`{text}`"
    
    @staticmethod
    def pre(text: str, language: str = "") -> str:
        """Блок кода"""
        if not text:
            return ""
        if language:
            return f"```{language}\n{text}\n```"
        else:
            return f"```\n{text}\n```"
    
    @staticmethod
    def link(text: str, url: str) -> str:
        """Ссылка"""
        if not text or not url:
            return text or ""
        escaped_text = MarkdownV2Utils.escape_markdown_v2(text)
        return f"[{escaped_text}]({url})"
    
    @staticmethod
    def strikethrough(text: str) -> str:
        """Зачеркнутый текст"""
        if not text:
            return ""
        escaped = MarkdownV2Utils.escape_markdown_v2(text)
        return f"~{escaped}~"
    
    @staticmethod
    def underline(text: str) -> str:
        """Подчеркнутый текст"""
        if not text:
            return ""
        escaped = MarkdownV2Utils.escape_markdown_v2(text)
        return f"__{escaped}__"
    
    @staticmethod
    def spoiler(text: str) -> str:
        """Спойлер"""
        if not text:
            return ""
        escaped = MarkdownV2Utils.escape_markdown_v2(text)
        return f"||{escaped}||"
    
    @staticmethod
    def format_user_info(first_name: str, username: Optional[str] = None, bot_username: Optional[str] = None) -> str:
        """
        Форматирование информации о пользователе
        
        Args:
            first_name: Имя пользователя
            username: Username пользователя
            bot_username: Username бота
            
        Returns:
            Отформатированная строка
        """
        # Эмодзи не экранируем
        result = f"👤 {MarkdownV2Utils.escape_markdown_v2(first_name or 'Пользователь')}"
        
        if username:
            result += f" \\(@{MarkdownV2Utils.escape_markdown_v2(username)}\\)"
        
        if bot_username:
            result += f"\n🤖 Бот: @{MarkdownV2Utils.escape_markdown_v2(bot_username)}"
        
        return result
    
    @staticmethod
    def format_bot_info(bot_username: str, bot_id: int, is_active: bool = True) -> str:
        """
        Форматирование информации о боте
        
        Args:
            bot_username: Username бота
            bot_id: ID бота
            is_active: Активен ли бот
            
        Returns:
            Отформатированная строка
        """
        status_emoji = "🟢" if is_active else "🔴"
        status_text = "активен" if is_active else "остановлен"
        
        result = f"🤖 Бот: @{MarkdownV2Utils.escape_markdown_v2(bot_username)}\n"
        result += f"🆔 ID: {MarkdownV2Utils.code(str(bot_id))}\n"
        result += f"{status_emoji} Статус: {MarkdownV2Utils.escape_markdown_v2(status_text)}"
        
        return result
    
    @staticmethod
    def format_group_info(group_title: str, group_id: int) -> str:
        """
        Форматирование информации о группе
        
        Args:
            group_title: Название группы
            group_id: ID группы
            
        Returns:
            Отформатированная строка
        """
        result = f"📋 Группа: {MarkdownV2Utils.escape_markdown_v2(group_title)}\n"
        result += f"🆔 ID: {MarkdownV2Utils.code(str(group_id))}"
        
        return result
    
    @staticmethod
    def format_error_message(error: str) -> str:
        """
        Форматирование сообщения об ошибке
        
        Args:
            error: Текст ошибки
            
        Returns:
            Отформатированная строка
        """
        return f"❌ {MarkdownV2Utils.bold('Ошибка')}: {MarkdownV2Utils.escape_markdown_v2(str(error))}"
    
    @staticmethod
    def format_success_message(message: str) -> str:
        """
        Форматирование сообщения об успехе
        
        Args:
            message: Текст сообщения
            
        Returns:
            Отформатированная строка
        """
        return f"✅ {MarkdownV2Utils.escape_markdown_v2(message)}"
    
    @staticmethod
    def format_warning_message(message: str) -> str:
        """
        Форматирование предупреждающего сообщения
        
        Args:
            message: Текст сообщения
            
        Returns:
            Отформатированная строка
        """
        return f"⚠️ {MarkdownV2Utils.escape_markdown_v2(message)}"
    
    @staticmethod
    def format_info_message(message: str) -> str:
        """
        Форматирование информационного сообщения
        
        Args:
            message: Текст сообщения
            
        Returns:
            Отформатированная строка
        """
        return f"ℹ️ {MarkdownV2Utils.escape_markdown_v2(message)}"
    
    @staticmethod
    def format_command_help() -> str:
        """Форматирование справки по командам операторов"""
        help_text = f"""🔧 {MarkdownV2Utils.bold('Команды оператора')}:

🟡 {MarkdownV2Utils.code('/hold')} \\- поставить на удержание
🟢 {MarkdownV2Utils.code('/unhold')} \\- снять с удержания
🔒 {MarkdownV2Utils.code('/ban')} \\- заблокировать пользователя
🔓 {MarkdownV2Utils.code('/unban')} \\- разблокировать пользователя
❌ {MarkdownV2Utils.code('/end')} \\- завершить диалог
❓ {MarkdownV2Utils.code('/help')} \\- показать справку

💬 Для ответа пользователю просто напишите сообщение в теме\\."""
        
        return help_text
    
    @staticmethod
    def format_status_message(status: str, chat_id: int) -> str:
        """
        Форматирование сообщения о статусе
        
        Args:
            status: Статус
            chat_id: ID чата
            
        Returns:
            Отформатированная строка
        """
        status_emojis = {
            'waiting': '⏳',
            'answered': '✅',
            'hold': '🟡',
            'banned': '🔒',
            'ended': '❌'
        }
        
        status_names = {
            'waiting': 'ожидает ответа',
            'answered': 'отвечен',
            'hold': 'на удержании',
            'banned': 'заблокирован',
            'ended': 'завершен'
        }
        
        emoji = status_emojis.get(status, '❓')
        name = status_names.get(status, status)
        
        return f"{emoji} Статус диалога {MarkdownV2Utils.code(str(chat_id))}: {MarkdownV2Utils.escape_markdown_v2(name)}"

# Глобальные функции для удобства
def escape_md(text: str) -> str:
    """Быстрое экранирование для Markdown V2"""
    return MarkdownV2Utils.escape_markdown_v2(text)

def bold(text: str) -> str:
    """Быстрое создание жирного текста"""
    return MarkdownV2Utils.bold(text)

def italic(text: str) -> str:
    """Быстрое создание курсива"""
    return MarkdownV2Utils.italic(text)

def code(text: str) -> str:
    """Быстрое создание кода"""
    return MarkdownV2Utils.code(text)

def link(text: str, url: str) -> str:
    """Быстрое создание ссылки"""
    return MarkdownV2Utils.link(text, url)