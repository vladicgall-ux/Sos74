import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db import init_db
from motivation import motivation_scheduler
import owner
import worker


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан. Проверьте файл .env")

    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(owner.router)
    dp.include_router(worker.router)

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(motivation_scheduler(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
