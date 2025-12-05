from datetime import date
from aiogram import types
from aiogram.filters import Command
from loader import dp, bot
from database import crud
from config import SUPER_ADMINS

def is_super_admin(user_id):
    return user_id in SUPER_ADMINS

@dp.message(Command("addmod", "delmod", "addadmin", "deladmin"))
async def cmd_roles(message: types.Message):
    if not is_super_admin(message.from_user.id):
        await message.reply("У тебя нет прав для управления ролями.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Нужно указать user_id.\nПример: /addmod 123456789")
        return

    target = parts[1]

    try:
        target_id = int(target)
    except ValueError:
        await message.reply(
            "В этой версии нужно указывать именно числовой user_id.\n"
            "Его можно узнать через бота @userinfobot."
        )
        return

    cmd = message.text.split()[0].lstrip("/")
    if cmd == "addmod":
        role = "moderator"
    elif cmd == "addadmin":
        role = "admin"
    elif cmd in ("delmod", "deladmin"):
        role = "none"
    else:
        await message.reply("Неизвестная команда.")
        return

    await crud.set_user_role(target_id, role)
    await message.reply(f"Роль пользователя {target_id} установлена: {role}")


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    role = await crud.get_user_role(message.from_user.id)
    if role != "admin":
        await message.reply("Команда доступна только администраторам.")
        return

    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_start_iso = month_start.isoformat()

    new_count, approved_count, declined_count, rows = await crud.get_stats_data(month_start_iso)

    text = [
        f"📊 Статистика за текущий месяц ({month_start.strftime('%d.%m.%Y')} - сегодня):",
        "",
        f"Новых заявок: {new_count}",
        f"Одобрено: {approved_count}",
        f"Отклонено: {declined_count}",
        "",
        "👤 Заявки по модераторам:",
    ]

    if not rows:
        text.append("нет данных.")
    else:
        for moderator_id, cnt in rows:
            mention = f"[{moderator_id}](tg://user?id={moderator_id})"
            text.append(f"{mention} — {cnt} заявок")

    await message.reply("\n".join(text), parse_mode="Markdown")
