#!/usr/bin/env python3
"""
Тестовый скрипт для проверки экранирования Markdown V2
"""

from utils.markdown_utils import MarkdownV2Utils, escape_md, bold, italic, code
from utils.text_formatter import TextFormatter

def test_escaping():
    """Тестирование экранирования специальных символов"""
    
    # Тестовые строки с проблемными символами
    test_strings = [
        "Пользователь (test)",
        "Ошибка: can't parse entities",
        "Character '-' is reserved",
        "Символы: _*[]()~`>#+-=|{}.!",
        "Email: user@example.com",
        "URL: https://example.com/path?param=value",
        "Код: function() { return 'test'; }",
        "Математика: 2 + 2 = 4",
        "Список: 1. Первый 2. Второй",
        "Скобки: (важно) [заметка] {объект}",
        "Telegram server says - Bad Request: can't parse entities",
    ]
    
    print("=== Тестирование экранирования ===")
    for test_str in test_strings:
        escaped = escape_md(test_str)
        print(f"Исходный: {test_str}")
        print(f"Экранированный: {escaped}")
        print()
    
    print("=== Тестирование форматирования ===")
    
    # Тестирование жирного текста
    bold_text = bold("Важное сообщение!")
    print(f"Жирный: {bold_text}")
    
    # Тестирование курсива
    italic_text = italic("Примечание (важно)")
    print(f"Курсив: {italic_text}")
    
    # Тестирование кода
    code_text = code("function() { return 'test'; }")
    print(f"Код: {code_text}")
    
    # Тестирование сложного форматирования
    complex_text = f"""
{bold('Ошибка подключения')}

{italic('Описание')}: Не удалось подключиться к серверу
{bold('Код ошибки')}: {code('CONNECTION_FAILED')}
{italic('Время')}: 2024-02-08 15:30:00

Попробуйте снова через несколько минут\\.
"""
    print(f"Сложное форматирование: {complex_text}")
    
    print("=== Тестирование TextFormatter ===")
    
    # Тестирование форматирования с entities
    text = "Это жирный текст и курсив"
    entities = [
        {'type': 'bold', 'offset': 4, 'length': 7},  # "жирный"
        {'type': 'italic', 'offset': 20, 'length': 6}  # "курсив"
    ]
    
    formatted = TextFormatter.format_text_with_entities(text, entities)
    print(f"Текст с entities: {formatted}")

def test_problematic_text():
    """Тестирование проблемного текста"""
    print("\n=== Тестирование проблемного текста ===")
    
    # Тестируем конкретно проблемный текст
    from utils.text_utils import get_text
    
    error_message = "Telegram server says - Bad Request: can't parse entities: Can't find end of Italic entity at byte offset 29"
    escaped_error = escape_md(error_message)
    
    # Получаем шаблон и подставляем экранированную ошибку
    template = get_text("bot_connection_error", "ru")
    final_text = template.format(error=escaped_error)
    
    print(f"Исходная ошибка: {error_message}")
    print(f"Экранированная ошибка: {escaped_error}")
    print(f"Шаблон: {template}")
    print(f"Финальный текст: {final_text}")

if __name__ == "__main__":
    test_escaping()
    test_problematic_text()