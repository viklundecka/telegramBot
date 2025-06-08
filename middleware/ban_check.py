from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from storage.json_storage import JSONStorage
import logging

logger = logging.getLogger(__name__)


class BanCheckMiddleware(BaseMiddleware):
    def __init__(self):
        self.storage = JSONStorage()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id

            is_banned = await self.storage.is_user_banned(user_id)

            if is_banned:
                ban_info = await self.storage.get_ban_info(user_id)

                ban_message = f"""
🚫 **Вы заблокированы**

**Причина:** {ban_info.get('reason', 'Не указана')}
**Дата блокировки:** {ban_info.get('banned_at', 'Неизвестно')[:16]}

Обратитесь к администратору для разблокировки.
"""

                if isinstance(event, Message):
                    await event.answer(ban_message, parse_mode="Markdown")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 Вы заблокированы", show_alert=True)

                logger.info(f"Заблокированный пользователь {user_id} попытался использовать бота")
                return

        return await handler(event, data)
