from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging
import asyncio
from datetime import datetime, timedelta

from config.settings import ADMIN_IDS
from filters.admin_filter import AdminFilter
from keyboards.inline import get_main_menu, get_admin_menu, get_admin_confirm_keyboard, get_admin_ban_keyboard, get_admin_cache_keyboard
from storage.json_storage import JSONStorage
from states import AdminStates
from services.api_client import WeatherstackAPI, CatFactsAPI

router = Router()
storage = JSONStorage()
logger = logging.getLogger(__name__)


@router.message(Command("admin"), AdminFilter(ADMIN_IDS))
async def admin_command(message: Message):
    stats = await storage.get_statistics()
    all_users = await storage.get_all_users()
    banned_users = await storage.get_banned_users()

    admin_text = f"""
🔧 **Админ панель**

📊 **Статистика:**
👥 Всего пользователей: {stats.get('total_users', 0)}
✅ Активных: {len(all_users) - len(banned_users)}
🚫 Заблокированных: {len(banned_users)}
📈 Всего запросов: {stats.get('total_requests', 0)}
🚀 Бот запущен: {stats.get('bot_started', 'Неизвестно')[:16]}

🕐 **Текущее время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""

    await message.answer(admin_text, reply_markup=get_admin_menu(), parse_mode="Markdown")
    logger.info(f"Админ {message.from_user.id} открыл админ панель")


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    stats = await storage.get_statistics()

    data = await storage.load_data()
    users_data = data.get("users", {})
    banned_users = data.get("banned_users", {})
    total_favorites = sum(len(favs) for favs in data.get("favorites", {}).values())

    now = datetime.now()
    yesterday = now - timedelta(days=1)
    active_today = 0

    for user_id, user_info in users_data.items():
        try:
            last_activity = datetime.fromisoformat(user_info.get('last_activity', '2020-01-01 00:00:00'))
            if last_activity > yesterday:
                active_today += 1
        except:
            pass

    city_counts = {}
    for user_favs in data.get("favorites", {}).values():
        for city in user_favs:
            city_counts[city] = city_counts.get(city, 0) + 1

    top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_cities_text = "\n".join([f"• {city}: {count}" for city, count in top_cities])

    users_by_registration = []
    for user_id, user_info in users_data.items():
        try:
            first_seen = datetime.fromisoformat(user_info.get('first_seen', '2020-01-01 00:00:00'))
            users_by_registration.append((user_id, user_info, first_seen))
        except:
            users_by_registration.append((user_id, user_info, datetime(2020, 1, 1)))

    users_by_registration.sort(key=lambda x: x[2], reverse=True)
    recent_users = users_by_registration[:10]

    recent_users_text = []
    for user_id, user_info, _ in recent_users:
        username = user_info.get('username', 'Не указан')
        status = "🚫" if user_id in banned_users else "✅"
        recent_users_text.append(f"{status} {user_id} (@{username})")

    detailed_stats = f"""
📊 **Детальная статистика**

👥 **Пользователи:**
• Всего: {stats.get('total_users', 0)}
• Активных за сутки: {active_today}
• Заблокированных: {len(banned_users)}

📈 **Активность:**
• Всего запросов: {stats.get('total_requests', 0)}
• Избранных городов: {total_favorites}

🏆 **Топ городов:**
{top_cities_text if top_cities_text else "Нет данных"}

📱 **Последние 10 пользователей:**
{chr(10).join(recent_users_text) if recent_users_text else "Нет данных"}

🚀 **Запуск:** {stats.get('bot_started', 'Неизвестно')[:16]}
"""

    await callback.message.edit_text(
        detailed_stats,
        reply_markup=get_admin_menu(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📢 **Массовая рассылка**\n\n"
        "Введите сообщение для отправки всем пользователям бота:\n\n"
        "⚠️ *Будьте осторожны! Сообщение будет отправлено всем пользователям.*",
        reply_markup=get_admin_menu(),
        parse_mode="Markdown"
    )

    await state.set_state(AdminStates.waiting_for_broadcast_message)
    logger.info(f"Админ {callback.from_user.id} начал рассылку")


@router.message(AdminStates.waiting_for_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет доступа")
        return

    broadcast_text = message.text

    confirm_text = f"""
📢 **Подтверждение рассылки**

**Текст сообщения:**
{broadcast_text}

⚠️ **Внимание!** Сообщение будет отправлено всем пользователям бота.

Подтверждаете отправку?
"""

    await message.answer(
        confirm_text,
        reply_markup=get_admin_confirm_keyboard("broadcast"),
        parse_mode="Markdown"
    )

    await state.update_data(broadcast_text=broadcast_text)


@router.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    data = await state.get_data()
    broadcast_text = data.get("broadcast_text")

    if not broadcast_text:
        await callback.message.edit_text(
            "❌ Ошибка: текст сообщения не найден",
            reply_markup=get_admin_menu()
        )
        await state.clear()
        return

    all_users = await storage.get_all_users()

    await callback.message.edit_text(
        f"📤 **Начинаю рассылку...**\n\n"
        f"Пользователей для отправки: {len(all_users)}\n"
        f"Прогресс: 0/{len(all_users)}",
        parse_mode="Markdown"
    )

    success_count = 0
    failed_count = 0

    bot = callback.bot

    for i, user_id in enumerate(all_users):
        try:
            await bot.send_message(
                user_id,
                f"📢 **Сообщение от администрации:**\n\n{broadcast_text}",
                parse_mode="Markdown"
            )
            success_count += 1

            if (i + 1) % 10 == 0 or i == len(all_users) - 1:
                await callback.message.edit_text(
                    f"📤 **Рассылка в процессе...**\n\n"
                    f"Прогресс: {i + 1}/{len(all_users)}\n"
                    f"Успешно: {success_count}\n"
                    f"Ошибки: {failed_count}",
                    parse_mode="Markdown"
                )

            await asyncio.sleep(0.1)

        except Exception as e:
            failed_count += 1
            logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")

    final_text = f"""
✅ **Рассылка завершена!**

📊 **Результаты:**
✅ Успешно отправлено: {success_count}
❌ Ошибки: {failed_count}
📱 Всего пользователей: {len(all_users)}

🕐 Время завершения: {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""

    await callback.message.edit_text(
        final_text,
        reply_markup=get_admin_menu(),
        parse_mode="Markdown"
    )

    await state.clear()
    logger.info(f"Админ {callback.from_user.id} завершил рассылку: {success_count} успешно, {failed_count} ошибок")


@router.callback_query(F.data == "admin_cache")
async def admin_cache_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    from config.settings import WEATHERSTACK_API_KEY
    weather_api = WeatherstackAPI(WEATHERSTACK_API_KEY) if WEATHERSTACK_API_KEY else None
    cat_api = CatFactsAPI()

    cache_info = f"""
🔧 **Управление кэшем**

🌤 **Weather API кэш:**
Записей: {len(weather_api.cache) if weather_api else 0}

🐱 **Cat Facts кэш:**
Записей: {len(cat_api.cache)}

💾 **Общий размер кэша:** ~{_calculate_cache_size(weather_api, cat_api)} KB
"""

    await callback.message.edit_text(
        cache_info,
        reply_markup=get_admin_cache_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "clear_cache")
async def clear_cache_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    from config.settings import WEATHERSTACK_API_KEY
    weather_api = WeatherstackAPI(WEATHERSTACK_API_KEY) if WEATHERSTACK_API_KEY else None
    cat_api = CatFactsAPI()

    if weather_api:
        weather_api.cache.clear()
    cat_api.cache.clear()

    await callback.answer("✅ Кэш очищен!", show_alert=True)

    await callback.message.edit_text(
        "✅ **Кэш успешно очищен!**\n\n"
        "Все кэшированные данные удалены.\n"
        "Следующие запросы будут обращаться к API.",
        reply_markup=get_admin_menu(),
        parse_mode="Markdown"
    )

    logger.info(f"Админ {callback.from_user.id} очистил кэш")


@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ **Рассылка отменена**",
        reply_markup=get_admin_menu(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    data = await storage.load_data()
    users_data = data.get("users", {})
    banned_users = data.get("banned_users", {})

    now = datetime.now()
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    active_today = 0
    active_week = 0

    users_by_activity = []
    for user_id, user_info in users_data.items():
        try:
            last_activity = datetime.fromisoformat(user_info.get('last_activity', '2020-01-01 00:00:00'))
            users_by_activity.append((user_id, user_info, last_activity))

            if last_activity > yesterday:
                active_today += 1
            if last_activity > week_ago:
                active_week += 1
        except:
            users_by_activity.append((user_id, user_info, datetime(2020, 1, 1)))

    users_by_activity.sort(key=lambda x: x[2], reverse=True)

    top_users = users_by_activity[:10]
    users_list = []

    for user_id, user_info, last_activity in top_users:
        username = user_info.get('username', 'Не указан')
        status = "🚫 Заблокирован" if user_id in banned_users else "✅ Активен"
        activity_str = last_activity.strftime('%d.%m %H:%M') if last_activity.year > 2020 else "Давно"
        request_count = user_info.get('request_count', 0)

        users_list.append(f"• {user_id} (@{username})\n  {status} | {request_count} запросов | {activity_str}")

    users_text = f"""
👥 **Управление пользователями**

📊 **Статистика:**
• Всего пользователей: {len(users_data)}
• Активных за сутки: {active_today}
• Активных за неделю: {active_week}
• Заблокированных: {len(banned_users)}

📱 **Топ-10 активных пользователей:**
{chr(10).join(users_list) if users_list else "Нет данных"}

ℹ️ *Пользователи сортированы по последней активности*
"""

    await callback.message.edit_text(
        users_text,
        reply_markup=get_admin_ban_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "ban_user")
async def ban_user_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🚫 **Блокировка пользователя**\n\n"
        "Введите ID пользователя для блокировки:\n\n"
        "⚠️ *Пользователь не сможет использовать бота*\n"
        "💡 *Подсказка: используйте /allusers для просмотра всех пользователей*",
        reply_markup=get_admin_ban_keyboard(),
        parse_mode="Markdown"
    )

    await state.set_state(AdminStates.waiting_for_ban_user_id)
    logger.info(f"Админ {callback.from_user.id} начал процесс блокировки пользователя")


@router.message(AdminStates.waiting_for_ban_user_id)
async def process_ban_user_id(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет доступа")
        await state.clear()
        return

    logger.info(f"Админ {message.from_user.id} ввел ID для блокировки: {message.text}")

    try:
        user_id = int(message.text.strip())

        if user_id in ADMIN_IDS:
            await message.answer(
                "❌ **Ошибка**\n\nНельзя заблокировать администратора!",
                reply_markup=get_admin_ban_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
            return

        user_info = await storage.get_user_info(user_id)
        if not user_info:
            await message.answer(
                f"❌ **Пользователь не найден**\n\n"
                f"Пользователь с ID {user_id} не найден в базе данных.\n"
                f"Используйте /allusers для просмотра всех пользователей.",
                reply_markup=get_admin_ban_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
            return

        is_banned = await storage.is_user_banned(user_id)
        if is_banned:
            await message.answer(
                f"⚠️ **Пользователь уже заблокирован**\n\n"
                f"Пользователь {user_id} уже находится в черном списке.",
                reply_markup=get_admin_ban_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
            return

        username = user_info.get("username", "Не указан")
        confirm_text = f"""
🚫 **Подтверждение блокировки**

**Пользователь:** {user_id} (@{username})
**Последняя активность:** {user_info.get('last_activity', 'Неизвестно')[:16]}
**Запросов сделано:** {user_info.get('request_count', 0)}

Введите причину блокировки:
"""

        await message.answer(confirm_text, parse_mode="Markdown")
        await state.update_data(ban_user_id=user_id)
        await state.set_state(AdminStates.waiting_for_ban_reason)
        logger.info(f"Запрошена причина блокировки для пользователя {user_id}")

    except ValueError:
        await message.answer(
            "❌ **Некорректный ID**\n\n"
            "Введите корректный числовой ID пользователя.\n"
            "Например: 123456789",
            reply_markup=get_admin_ban_keyboard(),
            parse_mode="Markdown"
        )


@router.message(AdminStates.waiting_for_ban_reason)
async def process_ban_reason(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет доступа")
        await state.clear()
        return

    data = await state.get_data()
    user_id = data.get("ban_user_id")
    reason = message.text.strip()

    logger.info(f"Админ {message.from_user.id} ввел причину блокировки: {reason}")

    if not reason or len(reason) > 200:
        await message.answer(
            "❌ **Некорректная причина**\n\n"
            "Причина должна быть от 1 до 200 символов.\n"
            "Введите причину блокировки снова:",
            parse_mode="Markdown"
        )
        return

    success = await storage.ban_user(user_id, reason, message.from_user.id)

    if success:
        try:
            await message.bot.send_message(
                user_id,
                f"🚫 **Вы заблокированы**\n\n"
                f"**Причина:** {reason}\n"
                f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Обратитесь к администратору для разблокировки.",
                parse_mode="Markdown"
            )
            notification_status = "✅ Уведомление отправлено"
        except Exception as e:
            notification_status = "⚠️ Не удалось отправить уведомление"
            logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")

        await message.answer(
            f"✅ **Пользователь заблокирован**\n\n"
            f"**ID:** {user_id}\n"
            f"**Причина:** {reason}\n"
            f"**Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"**Статус:** {notification_status}",
            reply_markup=get_admin_ban_keyboard(),
            parse_mode="Markdown"
        )

        logger.info(f"Админ {message.from_user.id} успешно заблокировал пользователя {user_id}")
    else:
        await message.answer(
            "❌ **Ошибка блокировки**\n\n"
            "Не удалось заблокировать пользователя. Попробуйте снова.",
            reply_markup=get_admin_ban_keyboard(),
            parse_mode="Markdown"
        )

    await state.clear()


@router.callback_query(F.data == "unban_user")
async def unban_user_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    banned_users = await storage.get_banned_users()

    if not banned_users:
        await callback.message.edit_text(
            "✅ **Нет заблокированных пользователей**\n\n"
            "Все пользователи активны.",
            reply_markup=get_admin_ban_keyboard(),
            parse_mode="Markdown"
        )
        return

    banned_list = []
    for user_id, ban_info in list(banned_users.items())[:10]:
        reason = ban_info.get('reason', 'Не указана')[:30]
        banned_date = ban_info.get('banned_at', 'Неизвестно')[:10]
        banned_list.append(f"• {user_id} - {reason} ({banned_date})")

    unban_text = f"""
🚫 **Заблокированные пользователи**

📊 Всего заблокировано: {len(banned_users)}

{chr(10).join(banned_list)}
{"..." if len(banned_users) > 10 else ""}

Введите ID пользователя для разблокировки:
"""

    await callback.message.edit_text(
        unban_text,
        reply_markup=get_admin_ban_keyboard(),
        parse_mode="Markdown"
    )

    await state.set_state(AdminStates.waiting_for_unban_user_id)
    logger.info(f"Админ {callback.from_user.id} начал процесс разблокировки")


@router.message(AdminStates.waiting_for_unban_user_id)
async def process_unban_user_id(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет доступа")
        await state.clear()
        return

    try:
        user_id = int(message.text.strip())

        is_banned = await storage.is_user_banned(user_id)
        if not is_banned:
            await message.answer(
                f"⚠️ **Пользователь не заблокирован**\n\n"
                f"Пользователь {user_id} не находится в черном списке.",
                reply_markup=get_admin_ban_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
            return

        ban_info = await storage.get_ban_info(user_id)

        success = await storage.unban_user(user_id, message.from_user.id)

        if success:
            try:
                await message.bot.send_message(
                    user_id,
                    f"✅ **Вы разблокированы**\n\n"
                    f"**Время разблокировки:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Теперь вы можете пользоваться ботом.",
                    parse_mode="Markdown"
                )
                notification_status = "✅ Уведомление отправлено"
            except Exception as e:
                notification_status = "⚠️ Не удалось отправить уведомление"
                logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")

            await message.answer(
                f"✅ **Пользователь разблокирован**\n\n"
                f"**ID:** {user_id}\n"
                f"**Была причина:** {ban_info.get('reason', 'Не указана')}\n"
                f"**Заблокирован:** {ban_info.get('banned_at', 'Неизвестно')[:16]}\n"
                f"**Разблокирован:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                f"**Статус:** {notification_status}",
                reply_markup=get_admin_ban_keyboard(),
                parse_mode="Markdown"
            )

            logger.info(f"Админ {message.from_user.id} разблокировал пользователя {user_id}")
        else:
            await message.answer(
                "❌ **Ошибка разблокировки**\n\n"
                "Не удалось разблокировать пользователя.",
                reply_markup=get_admin_ban_keyboard(),
                parse_mode="Markdown"
            )

    except ValueError:
        await message.answer(
            "❌ **Некорректный ID**\n\n"
            "Введите корректный числовой ID пользователя.",
            parse_mode="Markdown"
        )
        return

    await state.clear()


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    stats = await storage.get_statistics()
    all_users = await storage.get_all_users()
    banned_users = await storage.get_banned_users()

    admin_text = f"""
🔧 **Админ панель**

📊 **Статистика:**
👥 Всего пользователей: {stats.get('total_users', 0)}
✅ Активных: {len(all_users) - len(banned_users)}
🚫 Заблокированных: {len(banned_users)}
📈 Всего запросов: {stats.get('total_requests', 0)}
🚀 Бот запущен: {stats.get('bot_started', 'Неизвестно')[:16]}

🕐 **Текущее время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""

    await callback.message.edit_text(admin_text, reply_markup=get_admin_menu(), parse_mode="Markdown")


def _calculate_cache_size(weather_api, cat_api):
    size = 0
    if weather_api:
        size += len(str(weather_api.cache))
    size += len(str(cat_api.cache))
    return round(size / 1024, 2)


@router.message(Command("allusers"), AdminFilter(ADMIN_IDS))
async def all_users_command(message: Message):
    data = await storage.load_data()
    users_data = data.get("users", {})
    banned_users = data.get("banned_users", {})

    if not users_data:
        await message.answer("📭 Пользователей не найдено.")
        return

    users_list = []
    for user_id, user_info in users_data.items():
        username = user_info.get('username', 'Не указан')
        status = "🚫" if user_id in banned_users else "✅"
        request_count = user_info.get('request_count', 0)
        first_seen = user_info.get('first_seen', 'Неизвестно')[:10]

        users_list.append(f"{status} {user_id} (@{username}) | {request_count} зап. | с {first_seen}")

    chunk_size = 20
    for i in range(0, len(users_list), chunk_size):
        chunk = users_list[i:i + chunk_size]
        page_num = i // chunk_size + 1
        total_pages = (len(users_list) + chunk_size - 1) // chunk_size

        users_text = f"""
📋 **Все пользователи** (стр. {page_num}/{total_pages})

{chr(10).join(chunk)}

✅ - Активен | 🚫 - Заблокирован
"""

        await message.answer(users_text, parse_mode="Markdown")

        if i + chunk_size < len(users_list):
            await asyncio.sleep(1)


@router.message(Command("userinfo"), AdminFilter(ADMIN_IDS))
async def user_info_command(message: Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ **Использование команды:**\n`/userinfo <user_id>`\n\nПример: `/userinfo 123456789`",
                parse_mode="Markdown"
            )
            return

        user_id = int(parts[1])

        user_info = await storage.get_user_info(user_id)
        if not user_info:
            await message.answer(f"❌ Пользователь {user_id} не найден в базе данных.")
            return

        is_banned = await storage.is_user_banned(user_id)
        ban_info = await storage.get_ban_info(user_id) if is_banned else None

        favorites = await storage.get_favorites(user_id)

        status = "🚫 Заблокирован" if is_banned else "✅ Активен"

        info_text = f"""
👤 **Информация о пользователе {user_id}**

**Статус:** {status}
**Username:** @{user_info.get('username', 'Не указан')}
**Первое посещение:** {user_info.get('first_seen', 'Неизвестно')[:16]}
**Последняя активность:** {user_info.get('last_activity', 'Неизвестно')[:16]}
**Количество запросов:** {user_info.get('request_count', 0)}

**Избранных городов:** {len(favorites)}
{chr(10).join([f"• {city}" for city in favorites]) if favorites else "Нет избранных"}
"""

        if is_banned and ban_info:
            info_text += f"""

🚫 **Информация о блокировке:**
**Причина:** {ban_info.get('reason', 'Не указана')}
**Дата блокировки:** {ban_info.get('banned_at', 'Неизвестно')[:16]}
**Заблокировал:** {ban_info.get('banned_by', 'Неизвестно')}
"""

        await message.answer(info_text, parse_mode="Markdown")

    except ValueError:
        await message.answer("❌ Некорректный ID пользователя. Используйте числовой ID.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")