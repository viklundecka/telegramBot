from aiogram.filters import BaseFilter
from aiogram.types import Message


class TextLengthFilter(BaseFilter):

    def __init__(self, min_length: int = 1, max_length: int = 100):
        self.min_length = min_length
        self.max_length = max_length

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return self.min_length <= len(message.text) <= self.max_length