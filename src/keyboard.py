from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


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
