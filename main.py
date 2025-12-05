import asyncio
import logging
from loader import dp, bot
from database.db import init_db
import handlers.commands
import handlers.admin
import handlers.callbacks
import handlers.group
import handlers.private

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Инициализация базы данных...")
    await init_db()
    print("Бот запущен. Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
