from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


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


def my_docs_kb():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Мои документы📄', callback_data='view')],
            [InlineKeyboardButton(text='Закрепить документ📌', callback_data='pin')],
            [InlineKeyboardButton(text='Открепить документ📌', callback_data='unpin')]
        ],
        resize_keyboard=True,
    )

    return keyboard


def pin_doc_kb():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Посмотреть все документы📁', callback_data='By_all_docs')],
            [InlineKeyboardButton(text='По названию📛', callback_data='By_name')],
        ],
        resize_keyboard=True,
    )

    return keyboard
