from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:

        if isinstance(event, Message):
            user_lang = event.from_user.language_code
        else:
            user_lang = event.from_user.language_code
        

        lang = 'ru' if user_lang and user_lang.startswith('ru') else 'en'
        data['lang'] = lang
        
        return await handler(event, data)