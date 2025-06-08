from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from config.settings import WEATHERSTACK_API_KEY
from services.api_client import WeatherstackAPI
from utils.formatters import format_weather_message
from keyboards.inline import get_main_menu, get_back_button
from states import WeatherStates
from storage.json_storage import JSONStorage

router = Router()
weather_api = WeatherstackAPI(WEATHERSTACK_API_KEY) if WEATHERSTACK_API_KEY else None
storage = JSONStorage()
logger = logging.getLogger(__name__)


@router.message(Command("weather"))
async def weather_command(message: Message, state: FSMContext):
    if not weather_api:
        await message.answer(
            "❌ Сервис погоды временно недоступен.\n"
            "Причина: не настроен API ключ Weatherstack.",
            reply_markup=get_main_menu()
        )
        return

    await message.answer(
        "🌤 **Прогноз погоды**\n\n"
        "Введите название города для получения актуальной информации о погоде:\n\n"
        "Примеры: *Москва*, *London*, *New York*, *Париж*",
        reply_markup=get_back_button(),
        parse_mode="Markdown"
    )
    await state.set_state(WeatherStates.waiting_for_city)
    await storage.update_user_activity(message.from_user.id)
    logger.info(f"Пользователь {message.from_user.id} начал ввод города для погоды")


@router.callback_query(F.data == "weather")
async def weather_callback(callback: CallbackQuery, state: FSMContext):
    if not weather_api:
        await callback.message.edit_text(
            "❌ Сервис погоды временно недоступен.\n"
            "Причина: не настроен API ключ Weatherstack.",
            reply_markup=get_main_menu()
        )
        return

    await callback.message.edit_text(
        "🌤 **Прогноз погоды**\n\n"
        "Введите название города для получения актуальной информации о погоде:\n\n"
        "Примеры: *Москва*, *London*, *New York*, *Париж*",
        reply_markup=get_back_button(),
        parse_mode="Markdown"
    )
    await state.set_state(WeatherStates.waiting_for_city)
    await storage.update_user_activity(callback.from_user.id)
    logger.info(f"Пользователь {callback.from_user.id} начал ввод города для погоды")


@router.message(WeatherStates.waiting_for_city)
async def process_city_name(message: Message, state: FSMContext):
    city = message.text.strip()

    if len(city) < 2 or len(city) > 50:
        await message.answer(
            "❌ **Некорректное название города**\n\n"
            "Требования:\n"
            "• От 2 до 50 символов\n"
            "• Только буквы и пробелы\n"
            "• Без специальных символов\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
        return

    processing_msg = await message.answer(
        f"🔄 Получаю актуальную погоду для города **{city}**...\n"
        "⏳ Это займет несколько секунд",
        parse_mode="Markdown"
    )

    weather_data = await weather_api.get_weather(city)

    if weather_data:
        formatted_message = format_weather_message(weather_data)
        await processing_msg.edit_text(
            formatted_message,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {message.from_user.id} получил погоду для города: {city}")
    else:
        await processing_msg.edit_text(
            f"❌ **Город '{city}' не найден**\n\n"
            "Возможные причины:\n"
            "• Проверьте правильность написания\n"
            "• Попробуйте ввести название на английском\n"
            "• Укажите более крупный город поблизости\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
        logger.warning(f"Город не найден: {city} (пользователь {message.from_user.id})")
        return

    await state.clear()
    await storage.update_user_activity(message.from_user.id)


@router.callback_query(F.data.startswith("city_"))
async def weather_for_favorite_city(callback: CallbackQuery):
    city = callback.data.replace("city_", "")

    if not weather_api:
        await callback.answer("❌ Сервис погоды недоступен")
        return

    await callback.answer("🔄 Получаю погоду...")

    await callback.message.edit_text(
        f"🔄 Получаю актуальную погоду для **{city}**...",
        parse_mode="Markdown"
    )

    weather_data = await weather_api.get_weather(city)

    if weather_data:
        formatted_message = format_weather_message(weather_data)
        await callback.message.edit_text(
            formatted_message,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {callback.from_user.id} получил погоду для избранного города: {city}")
    else:
        await callback.message.edit_text(
            f"❌ Не удалось получить погоду для города **{city}**\n\n"
            "Возможно, проблемы с API или город был удален из базы данных.",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

    await storage.update_user_activity(callback.from_user.id)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 **Главное меню**\n\nВыберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню")