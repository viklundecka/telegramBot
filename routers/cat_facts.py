from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
import logging

from services.api_client import CatFactsAPI
from keyboards.inline import get_main_menu, get_back_button
from storage.json_storage import JSONStorage

router = Router()
cat_api = CatFactsAPI()
storage = JSONStorage()
logger = logging.getLogger(__name__)


@router.message(Command("cat"))
async def cat_fact_command(message: Message):
    processing_msg = await message.answer("🐱 Ищу интересный факт о котах...")

    fact = await cat_api.get_cat_fact()

    if fact:
        await processing_msg.edit_text(
            f"🐱 **Факт о котах:**\n\n{fact}",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {message.from_user.id} запросил факт о котах")
    else:
        await processing_msg.edit_text(
            "❌ Не удалось получить факт о котах. Попробуйте позже.",
            reply_markup=get_main_menu()
        )

    await storage.update_user_activity(message.from_user.id)


@router.callback_query(F.data == "cat_fact")
async def cat_fact_callback(callback: CallbackQuery):
    await callback.answer("🐱 Загружаю факт...")

    fact = await cat_api.get_cat_fact()

    if fact:
        await callback.message.edit_text(
            f"🐱 **Факт о котах:**\n\n{fact}",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось получить факт о котах. Попробуйте позже.",
            reply_markup=get_main_menu()
        )

    await storage.update_user_activity(callback.from_user.id)