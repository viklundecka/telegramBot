import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import BOT_TOKEN
from middleware.ban_check import BanCheckMiddleware
from routers import weather, favorites
from routers import commands
from routers.cat_facts import router as cat_router
from middleware.throttling import ThrottlingMiddleware
from utils.logger import setup_logger
from routers.admin import router as admin_router


async def main():
    setup_logger()

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    dp.include_router(weather.router)
    dp.include_router(favorites.router)
    dp.include_router(cat_router)
    dp.include_router(admin_router)
    dp.include_router(commands.router)

    logging.info("Бот запущен и готов к работе!")

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())