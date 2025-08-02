import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TextFormatter:
    """Класс для форматирования текста с entities в Markdown V2"""
    
    @staticmethod
    def entities_to_markdown_v2(text: str, entities: List[Dict[str, Any]]) -> str:
        """
        Преобразование текста с entities в Markdown V2 формат
        Использует простой алгоритм обработки entities по порядку
        
        Args:
            text: Исходный текст
            entities: Список entities
            
        Returns:
            Отформатированный текст в Markdown V2
        """
        if not text:
            return ""
        
        if not entities:
            return TextFormatter._escape_markdown_v2(text)
        
        try:
            # Сортируем entities по offset в обратном порядке, чтобы не сбивать позиции
            sorted_entities = sorted(entities, key=lambda x: (x.get('offset', 0), x.get('length', 0)), reverse=True)
            
            result_text = text
            
            for entity in sorted_entities:
                entity_type = entity.get('type')
                offset = entity.get('offset', 0)
                length = entity.get('length', 0)
                
                if offset < 0 or length <= 0 or offset + length > len(result_text):
                    logger.warning(f"Некорректные параметры entity: offset={offset}, length={length}, text_len={len(result_text)}")
                    continue
                
                # Извлекаем части текста
                before = result_text[:offset]
                entity_text = result_text[offset:offset + length]
                after = result_text[offset + length:]
                
                # Форматируем entity_text в зависимости от типа
                formatted_text = TextFormatter._format_entity_text(entity_text, entity_type, entity)
                
                # Собираем результат
                result_text = before + formatted_text + after
            
            return result_text
            
        except Exception as e:
            logger.error(f"Ошибка при форматировании текста: {e}")
            return TextFormatter._escape_markdown_v2(text)
    
    @staticmethod
    def _format_entity_text(entity_text: str, entity_type: str, entity: Dict[str, Any]) -> str:
        """
        Форматирование текста entity в соответствии с его типом
        
        Args:
            entity_text: Текст entity
            entity_type: Тип entity
            entity: Полные данные entity
            
        Returns:
            Отформатированный текст
        """
        if entity_type == 'bold':
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            return f"*{escaped_text}*"
        
        elif entity_type == 'italic':
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            return f"_{escaped_text}_"
        
        elif entity_type == 'underline':
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            return f"__{escaped_text}__"
        
        elif entity_type == 'strikethrough':
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            return f"~{escaped_text}~"
        
        elif entity_type == 'spoiler':
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            return f"||{escaped_text}||"
        
        elif entity_type == 'blockquote':
            # Блочная цитата - каждую строку начинаем с >
            lines = entity_text.split('\n')
            quoted_lines = []
            for line in lines:
                escaped_line = TextFormatter._escape_markdown_v2(line)
                quoted_lines.append(f">{escaped_line}")
            return '\n'.join(quoted_lines)
        
        elif entity_type == 'expandable_blockquote':
            # Раскрывающаяся блочная цитата - то же что и обычная, но с дополнительным символом
            lines = entity_text.split('\n')
            quoted_lines = []
            for line in lines:
                escaped_line = TextFormatter._escape_markdown_v2(line)
                quoted_lines.append(f">{escaped_line}")
            return '\n'.join(quoted_lines)
        
        elif entity_type == 'code':
            # Код не экранируем
            return f"`{entity_text}`"
        
        elif entity_type == 'pre':
            language = entity.get('language', '')
            if language:
                return f"```{language}\n{entity_text}\n```"
            else:
                return f"```\n{entity_text}\n```"
        
        elif entity_type == 'text_link':
            url = entity.get('url', '')
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            if url:
                escaped_url = TextFormatter._escape_url(url)
                return f"[{escaped_text}]({escaped_url})"
            else:
                return escaped_text
        
        elif entity_type == 'url':
            # Для URL entity используем сам текст как ссылку
            escaped_url = TextFormatter._escape_url(entity_text)
            return f"[{entity_text}]({escaped_url})"
        
        elif entity_type == 'email':
            return f"[{entity_text}](mailto:{entity_text})"
        
        elif entity_type == 'phone_number':
            return f"[{entity_text}](tel:{entity_text})"
        
        elif entity_type in ['mention', 'hashtag', 'cashtag', 'bot_command']:
            # Эти типы не требуют дополнительного форматирования
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            return escaped_text
        
        elif entity_type == 'custom_emoji':
            # Кастомные эмодзи не поддерживаются в Markdown V2
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            return escaped_text
        
        else:
            # Неизвестный тип - экранируем и возвращаем
            logger.debug(f"Неизвестный тип entity: {entity_type}")
            escaped_text = TextFormatter._escape_markdown_v2(entity_text)
            return escaped_text
    
    @staticmethod
    def _escape_url(url: str) -> str:
        """Экранирование URL для Markdown V2"""
        if not url:
            return ""
        
        # Экранируем только скобки в URL
        return url.replace('(', '\\(').replace(')', '\\)')
    
    @staticmethod
    def _escape_markdown_v2(text: str) -> str:
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
    def format_text_with_entities(text: str, entities: List[Dict[str, Any]]) -> str:
        """
        Основная функция для форматирования текста с entities
        
        Args:
            text: Исходный текст
            entities: Список entities
            
        Returns:
            Отформатированный текст
        """
        return TextFormatter.entities_to_markdown_v2(text, entities)
    
    @staticmethod
    def format_caption_with_entities(caption: Optional[str], entities: List[Dict[str, Any]]) -> Optional[str]:
        """
        Форматирование подписи с entities
        
        Args:
            caption: Подпись
            entities: Список entities
            
        Returns:
            Отформатированная подпись или None
        """
        if not caption:
            return None
        
        return TextFormatter.format_text_with_entities(caption, entities)

# Глобальная функция для удобства
def format_message_text(text: str, entities: List[Dict[str, Any]]) -> str:
    """Удобная функция для форматирования текста сообщения"""
    return TextFormatter.format_text_with_entities(text, entities)