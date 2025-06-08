from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging

from keyboards.inline import get_main_menu
from storage.json_storage import JSONStorage
from filters.text_length_filter import TextLengthFilter
from config.settings import ADMIN_IDS

router = Router()
storage = JSONStorage()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()

    await storage.add_user(
        message.from_user.id,
        message.from_user.username
    )

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я многофункциональный бот, который поможет тебе:\n"
        "🌤 Узнать погоду в любом городе\n"
        "🐱 Получить интересные факты о котах\n"
        "📝 Прочитать случайные записи\n"
        "⭐ Сохранить любимые города\n"
        "📊 Посмотреть статистику\n\n"
        "Выбери, что тебя интересует:",
        reply_markup=get_main_menu()
    )

    logger.info(f"Пользователь {message.from_user.id} запустил бота")


@router.message(Command("help"))
async def help_command(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS

    help_text = """
🤖 **Помощь по боту**

📋 **Доступные команды:**
/start - Запуск бота
/help - Эта справка
/weather - Узнать погоду
/cat - Случайный факт о котах
/favorites - Управление избранными городами
/about - О боте
/stats - Статистика
/contact - Контакты
"""

    if is_admin:
        help_text += """
👑 **Команды администратора:**
/admin - Админ панель
/allusers - Все пользователи
/userinfo <id> - Информация о пользователе
"""

    help_text += """
🎮 **Интерактивные функции:**
• Используйте кнопки для удобной навигации
• Добавляйте города в избранное
• Получайте актуальную информацию о погоде

❓ **Нужна помощь?** Просто нажмите на нужную кнопку!
"""

    await message.answer(help_text, reply_markup=get_main_menu(), parse_mode="Markdown")
    await storage.update_user_activity(message.from_user.id)
    logger.info(f"Пользователь {message.from_user.id} запросил помощь")


@router.message(Command("about"))
async def about_command(message: Message):
    """Информация о боте"""
    about_text = """
🤖 **О боте**

**Версия:** 1.0.0
**Разработчик:** @swerchansky
**Технологии:** aiogram 3.x, aiohttp, Python 3.13+

Этот бот создан как учебный проект и демонстрирует:
• Работу с внешними API (Weatherstack, Cat Facts, JSONPlaceholder)
• Кэширование данных
• FSM (машины состояний)
• Middleware и фильтры
• Хранение пользовательских данных
• Современные практики разработки

🌤 **API сервисы:**
• Weatherstack - подробная информация о погоде
• Cat Facts API - интересные факты о котах
• JSONPlaceholder - демо API для тестирования
"""

    await message.answer(about_text, reply_markup=get_main_menu(), parse_mode="Markdown")
    await storage.update_user_activity(message.from_user.id)


@router.message(Command("stats"))
async def stats_command(message: Message):
    """Статистика бота"""
    stats = await storage.get_statistics()
    user_favorites = await storage.get_favorites(message.from_user.id)

    stats_text = f"""
📊 **Статистика бота**

👥 Всего пользователей: {stats.get('total_users', 0)}
📈 Всего запросов: {stats.get('total_requests', 0)}
🎯 Ваших избранных городов: {len(user_favorites)}
🚀 Бот запущен: {stats.get('bot_started', 'Неизвестно')}

⭐ **Ваши избранные города:**
{chr(10).join([f"• {city}" for city in user_favorites]) if user_favorites else "Пока нет избранных городов"}
"""

    await message.answer(stats_text, reply_markup=get_main_menu(), parse_mode="Markdown")
    await storage.update_user_activity(message.from_user.id)


@router.message(Command("contact"))
async def contact_command(message: Message):
    """Контактная информация"""
    contact_text = """
📞 **Контакты**

По вопросам работы бота обращайтесь:
💬 **Telegram:** [@Viklundechka](https://t.me/viklundechka)

💡 **Есть предложения?** Напишите в Telegram

Буду рад обратной связи и предложениям! 😊
"""

    await message.answer(contact_text, reply_markup=get_main_menu(), parse_mode="Markdown")
    await storage.update_user_activity(message.from_user.id)


@router.message(
    TextLengthFilter(max_length=50),
    ~F.text.startswith('/'),
    lambda message, state: state is None or state.get_state() is None
)
async def echo_short_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            f"📝 Вы написали: *{message.text}*\n\n"
            "Используйте команды или кнопки для взаимодействия с ботом!",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        await storage.update_user_activity(message.from_user.id)


@router.message()
async def unknown_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❓ Неизвестная команда или слишком длинное сообщение.\n\n"
            "Используйте /help для просмотра доступных команд или выберите действие:",
            reply_markup=get_main_menu()
        )
        await storage.update_user_activity(message.from_user.id)