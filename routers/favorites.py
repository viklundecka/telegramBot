from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from keyboards.inline import get_favorites_menu, get_main_menu
from keyboards.builders import build_cities_keyboard
from states import FavoriteStates
from storage.json_storage import JSONStorage
from utils.formatters import format_user_list
from filters.text_length_filter import TextLengthFilter

router = Router()
storage = JSONStorage()
logger = logging.getLogger(__name__)


@router.message(Command("favorites"))
async def favorites_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⭐ Управление избранными городами:",
        reply_markup=get_favorites_menu()
    )
    await storage.update_user_activity(message.from_user.id)


@router.callback_query(F.data == "favorites")
async def favorites_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "⭐ Управление избранными городами:",
        reply_markup=get_favorites_menu()
    )
    await storage.update_user_activity(callback.from_user.id)


@router.callback_query(F.data == "show_favorites")
async def show_favorites_callback(callback: CallbackQuery):
    favorites = await storage.get_favorites(callback.from_user.id)

    if favorites:
        keyboard = build_cities_keyboard(favorites)
        await callback.message.edit_text(
            "⭐ Ваши избранные города:\n\nВыберите город для получения погоды:",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            "📭 У вас пока нет избранных городов.\n\nДобавьте города, чтобы быстро получать прогноз погоды!",
            reply_markup=get_favorites_menu()
        )

    await storage.update_user_activity(callback.from_user.id)


@router.callback_query(F.data == "add_favorite")
async def add_favorite_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ Введите название города для добавления в избранное:",
        reply_markup=get_favorites_menu()
    )
    await state.set_state(FavoriteStates.waiting_for_add_city)


@router.message(FavoriteStates.waiting_for_add_city, TextLengthFilter(min_length=2, max_length=50))
async def process_add_favorite(message: Message, state: FSMContext):
    city = message.text.strip().title()

    success = await storage.add_favorite(message.from_user.id, city)

    if success:
        await message.answer(
            f"✅ Город '{city}' добавлен в избранное!",
            reply_markup=get_favorites_menu()
        )
        logger.info(f"Пользователь {message.from_user.id} добавил город в избранное: {city}")
    else:
        await message.answer(
            f"ℹ️ Город '{city}' уже в вашем избранном.",
            reply_markup=get_favorites_menu()
        )

    await state.clear()
    await storage.update_user_activity(message.from_user.id)


@router.callback_query(F.data == "remove_favorite")
async def remove_favorite_callback(callback: CallbackQuery, state: FSMContext):
    favorites = await storage.get_favorites(callback.from_user.id)

    if not favorites:
        await callback.message.edit_text(
            "📭 У вас нет избранных городов для удаления.",
            reply_markup=get_favorites_menu()
        )
        return

    await callback.message.edit_text(
        "🗑 Введите название города для удаления из избранного:\n\n" +
        format_user_list(favorites),
        reply_markup=get_favorites_menu()
    )
    await state.set_state(FavoriteStates.waiting_for_remove_city)


@router.message(FavoriteStates.waiting_for_remove_city, TextLengthFilter(min_length=2, max_length=50))
async def process_remove_favorite(message: Message, state: FSMContext):
    city = message.text.strip().title()

    success = await storage.remove_favorite(message.from_user.id, city)

    if success:
        await message.answer(
            f"✅ Город '{city}' удален из избранного!",
            reply_markup=get_favorites_menu()
        )
        logger.info(f"Пользователь {message.from_user.id} удалил город из избранного: {city}")
    else:
        await message.answer(
            f"❌ Город '{city}' не найден в вашем избранном.",
            reply_markup=get_favorites_menu()
        )

    await state.clear()
    await storage.update_user_activity(message.from_user.id)


@router.callback_query(F.data == "stats")
async def stats_callback(callback: CallbackQuery):
    stats = await storage.get_statistics()
    user_favorites = await storage.get_favorites(callback.from_user.id)

    stats_text = f"""
📊 Статистика

👥 Всего пользователей бота: {stats.get('total_users', 0)}
📈 Всего запросов к боту: {stats.get('total_requests', 0)}
⭐ Ваших избранных городов: {len(user_favorites)}

{format_user_list(user_favorites) if user_favorites else "📭 У вас пока нет избранных городов"}
"""

    await callback.message.edit_text(
        stats_text,
        reply_markup=get_main_menu()
    )
    await storage.update_user_activity(callback.from_user.id)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_menu()
    )