from aiogram import types
from loader import dp, bot
from database import crud
from keyboards import inline
from config import GROUP_CHAT_ID, TOPIC_NEW_ID

async def auto_format_new_app(message: types.Message):
    """Автоматически формирует заявку, если пришло сообщение от Google Script."""
    if message.chat.id != GROUP_CHAT_ID:
        return
    if message.message_thread_id != TOPIC_NEW_ID:
        return

    full_text = message.text or ""
    if not full_text.strip():
        return  # игнорируем пустые сообщения

    app_id = await crud.create_application(
        text=full_text,
        chat_id=message.chat.id,
        topic_id=message.message_thread_id,
        message_id=message.message_id
    )

    new_text = f"⚡ НОВАЯ ЗАЯВКА #{app_id} ⚡\n\n{full_text}"

    sent = await bot.send_message(
        GROUP_CHAT_ID,
        new_text,
        message_thread_id=TOPIC_NEW_ID,
        reply_markup=inline.get_new_app_keyboard(app_id)
    )

    # Обновляем в БД привязку к новому сообщению
    await crud.update_application(
        app_id,
        chat_id=sent.chat.id,
        topic_id=sent.message_thread_id,
        message_id=sent.message_id,
    )

    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

@dp.message(lambda m: m.chat.id == GROUP_CHAT_ID and m.message_thread_id == TOPIC_NEW_ID)
async def handle_new_application_topic(message: types.Message):
    await auto_format_new_app(message)
