from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import time


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.user_last_message = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            current_time = time.time()

            if user_id in self.user_last_message:
                if current_time - self.user_last_message[user_id] < self.rate_limit:
                    if isinstance(event, Message):
                        await event.answer("⏳ Слишком много запросов! Подождите немного.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("⏳ Слишком много запросов!", show_alert=True)
                    return

            self.user_last_message[user_id] = current_time

        return await handler(event, data)