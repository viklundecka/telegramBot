from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def build_cities_keyboard(cities: List[str]) -> InlineKeyboardMarkup:
    keyboard = []

    for city in cities:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🏙 {city}",
                callback_data=f"city_{city}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="⬅ Назад", callback_data="favorites")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)