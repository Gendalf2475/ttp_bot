from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_new_app_keyboard(app_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ В работу", callback_data=f"take:{app_id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_pre:{app_id}")
    return builder.as_markup()

def get_in_work_keyboard(app_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Отправить отчёт", callback_data=f"report:{app_id}")
    return builder.as_markup()

def get_review_keyboard(app_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"approve:{app_id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_final:{app_id}")
    return builder.as_markup()
