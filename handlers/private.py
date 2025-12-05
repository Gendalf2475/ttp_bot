from aiogram import types
from loader import dp, bot
from database import crud
from keyboards import inline
from config import GROUP_CHAT_ID, TOPIC_AWAIT_REVIEW_ID, RESPONSIBLE_USERNAMES

@dp.message(lambda m: m.chat.type == "private")
async def handle_private(message: types.Message):
    user = await crud.get_or_create_user(message.from_user)

    if user.role not in ("moderator", "admin"):
        await message.reply("У тебя нет прав отправлять отчёты.")
        return

    app_id = user.pending_report_app_id
    step = user.pending_report_step

    if not app_id or not step:
        await message.reply("Нет заявки, по которой ожидается отчёт.")
        return

    app = await crud.get_application(app_id)
    if not app:
        await message.reply("Заявка не найдена.")
        await crud.set_pending_report(message.from_user.id, None)
        return

    if step == 1:
        await crud.update_user_report_step(message.from_user.id, 1, message.text.strip())
        await message.reply(
            "Вопрос 2:\n"
            "Комментарий по прошедшему обзвону"
        )
        return

    if step == 2:
        await crud.update_user_report_step(message.from_user.id, 2, message.text.strip())
        await message.reply(
            "Вопрос 3:\n"
            "Ссылка на запись обзвона"
        )
        return

    if step == 3:
        await crud.update_user_report_step(message.from_user.id, 3, message.text.strip())

        # Получаем обновленного пользователя с ответами
        user = await crud.get_user(message.from_user.id)
        q1 = user.report_q1 or "-"
        q2 = user.report_q2 or "-"
        q3 = user.report_q3 or "-"

        await crud.update_application(
            app_id,
            status="awaiting_review",
            report_q1=q1,
            report_q2=q2,
            report_q3=q3,
        )

        mention_mod = f"[{message.from_user.id}](tg://user?id={message.from_user.id})"
        resp_mentions = " ".join(RESPONSIBLE_USERNAMES) if RESPONSIBLE_USERNAMES else ""
        text = (
            f"{resp_mentions}\n\n"
            f"Заявка #{app_id}\n\n"
            f"{app.text}\n\n"
            f"Отчёт модератора {mention_mod}:\n\n"
            f"1️⃣ Укажите количество верных ответов:\n{q1}\n\n"
            f"2️⃣ Комментарий по прошедшему обзвону:\n{q2}\n\n"
            f"3️⃣ Ссылка на запись обзвона:\n{q3}"
        )

        sent = await bot.send_message(
            GROUP_CHAT_ID,
            text,
            message_thread_id=TOPIC_AWAIT_REVIEW_ID,
            reply_markup=inline.get_review_keyboard(app_id),
            parse_mode="Markdown"
        )

        await crud.update_application(
            app_id,
            chat_id=sent.chat.id,
            topic_id=sent.message_thread_id,
            message_id=sent.message_id,
        )

        await crud.set_pending_report(message.from_user.id, None)

        await message.reply("Отчёт отправлен на рассмотрение.")
        return

    await crud.set_pending_report(message.from_user.id, None)
    await message.reply("Состояние отчёта сброшено. Попробуй ещё раз через кнопку под заявкой.")
