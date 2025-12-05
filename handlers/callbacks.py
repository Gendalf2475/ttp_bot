from datetime import datetime
from aiogram import types
from loader import dp, bot
from database import crud
from keyboards import inline
from config import GROUP_CHAT_ID, TOPIC_IN_WORK_ID, TOPIC_DECLINED_ID, TOPIC_APPROVED_ID

async def ensure_application_exists(call: types.CallbackQuery):
    """Создаёт заявку в БД, если она ещё не создана (для старых сообщений)."""
    message = call.message
    full_text = message.text or ""

    # Удаляем старую шапку "⚡ НОВАЯ ЗАЯВКА ⚡"
    lines = full_text.split("\n")
    body_lines = [l for l in lines if not ("НОВАЯ ЗАЯВКА" in l)]
    body_text = "\n".join(body_lines).strip()

    # Ищем заявку по message_id
    app = await crud.get_application_by_message_id(message.message_id)
    if app:
        return app.id, body_text

    # Создаём новую заявку
    app_id = await crud.create_application(
        text=body_text,
        chat_id=message.chat.id,
        topic_id=message.message_thread_id,
        message_id=message.message_id
    )
    return app_id, body_text

@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    data = call.data or ""
    user_id = call.from_user.id
    role = await crud.get_user_role(user_id)

    async def need_moderator():
        await call.answer("Недостаточно прав.")
        return

    # ============ ВЗЯТЬ В РАБОТУ ============
    if data.startswith("take:"):
        if role not in ("moderator", "admin"):
            await need_moderator()
            return

        app_id, body_text = await ensure_application_exists(call)
        
        new_text = (
            f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n"
            f"{body_text}\n\n"
            f"В работе: [{user_id}](tg://user?id={user_id})"
        )

        sent = await bot.send_message(
            GROUP_CHAT_ID,
            new_text,
            message_thread_id=TOPIC_IN_WORK_ID,
            reply_markup=inline.get_in_work_keyboard(app_id),
            parse_mode="Markdown"
        )

        try:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

        await crud.update_application(
            app_id,
            status="in_work",
            moderator_id=user_id,
            taken_at=datetime.utcnow().isoformat(),
            chat_id=sent.chat.id,
            topic_id=sent.message_thread_id,
            message_id=sent.message_id,
        )

        await call.answer("Заявка взята в работу.")

    # ============ ОТКЛОНИТЬ ДО РАССМОТРЕНИЯ ============
    elif data.startswith("reject_pre:"):
        if role not in ("moderator", "admin"):
            await need_moderator()
            return

        app_id, body_text = await ensure_application_exists(call)

        text = (
            f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n"
            f"{body_text}\n\n"
            f"❌ Отклонена до рассмотрения модератором "
            f"[{user_id}](tg://user?id={user_id})"
        )

        await bot.send_message(
            GROUP_CHAT_ID,
            text,
            message_thread_id=TOPIC_DECLINED_ID,
            parse_mode="Markdown"
        )

        try:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        await crud.update_application(app_id, status="declined_pre")
        await call.answer("Заявка отклонена.")

    # ============ ОТЧЕТ ============
    elif data.startswith("report:"):
        if role not in ("moderator", "admin"):
            await need_moderator()
            return

        app_id, _ = await ensure_application_exists(call)
        
        await crud.set_pending_report(user_id, app_id)
        await call.answer("Переходим к отчету.")

        try:
            await bot.send_message(
                user_id,
                f"Отчёт по заявке #{app_id}.\n\n"
                f"Вопрос 1:\nУкажите количество верных ответов"
            )
        except Exception:
            await bot.send_message(
                GROUP_CHAT_ID,
                f"[{user_id}](tg://user?id={user_id}), не могу написать тебе в личку. Запусти бота командой /start",
                message_thread_id=call.message.message_thread_id,
                parse_mode="Markdown"
            )

    # ============ ОДОБРИТЬ ============
    elif data.startswith("approve:"):
        if role != "admin":
            await need_moderator()
            return

        app_id, body_text = await ensure_application_exists(call)
        
        approved_text = (
            f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n"
            f"{body_text}\n\n"
            f"✅ Одобрена администратором "
            f"[{user_id}](tg://user?id={user_id})"
        )

        await bot.send_message(
            GROUP_CHAT_ID,
            approved_text,
            message_thread_id=TOPIC_APPROVED_ID,
            parse_mode="Markdown"
        )

        try:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        await crud.update_application(app_id, status="approved")
        await call.answer("Заявка одобрена.")

    # ============ ОТКЛОНИТЬ ПОСЛЕ РАССМОТРЕНИЯ ============
    elif data.startswith("reject_final:"):
        if role != "admin":
            await need_moderator()
            return

        app_id, body_text = await ensure_application_exists(call)
        
        declined_text = (
            f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n"
            f"{body_text}\n\n"
            f"❌ Отклонена после рассмотрения администратором "
            f"[{user_id}](tg://user?id={user_id})"
        )

        await bot.send_message(
            GROUP_CHAT_ID,
            declined_text,
            message_thread_id=TOPIC_DECLINED_ID,
            parse_mode="Markdown"
        )

        try:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        await crud.update_application(app_id, status="declined_final")
        await call.answer("Заявка отклонена окончательно.")

    else:
        await call.answer("Неизвестное действие.")
