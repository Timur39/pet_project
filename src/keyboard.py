import asyncio
from cgitb import reset

import aiogram
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton


def admin_kb():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="📝 Отзывы")],
            [KeyboardButton(text="⬅️ Выйти из админки")]
        ],
        resize_keyboard=True,
        input_field_placeholder='Выбери действие:'
    )

    return keyboard
