from aiogram import types
from aiogram.filters import Command
from loader import dp, bot
from database import crud

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await crud.get_or_create_user(message.from_user)
    await message.reply(
        "Привет! Я бот заявок.\n"
        "Работаю в группе, куда приходят новые заявки.\n"
        "Если у тебя есть роль модератора или администратора, тебе выдадут доступ."
    )

@dp.message(Command("debug"))
async def cmd_debug(message: types.Message):
    await message.reply(
        f"chat_id: {message.chat.id}\n"
        f"thread_id (topic_id): {message.message_thread_id}"
    )
