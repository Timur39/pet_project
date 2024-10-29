import asyncio
import os

import dotenv
from aiogram import Bot, Dispatcher, html
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types import Message

from get_data import all_data

dotenv.load_dotenv()
# Токен бота
TOKEN = os.getenv('BOT_TOKEN')
my_documents = []

dp = Dispatcher()


class Form(StatesGroup):
    first = State()
    second = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Команда /start, приветствующая пользователя
    :param message: Message
    :return: None
    """
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!\nЯ бот-помощник🤖, напиши название нужного тебе документа📄\nВведи команду /help она даст список доступных команд")


@dp.message(Command('help'))
async def help_handler(message: Message) -> None:
    """
    Команда /help, выводит все доступные команды
    :param message: Message
    :return: None
    """
    await message.answer(
        f'Доступные команды:\n/start - приветственное сообщение\n'
        f'/my_documents - ваши закрепленные документы\n'
        f'/help - список доступных команд\n'
        f'/pin_document - для закрепления документа')


@dp.message(Command('my_documents'))
async def my_documents_handler(message: Message) -> None:
    """
    Команда /my_documents, выводит клавиатуру для выбора: посмотреть мои документы или закрепить новый документ
    :param message: Message
    :return: None
    """
    button1 = [InlineKeyboardButton(text='Мои документы📄', callback_data='view')]
    button2 = [InlineKeyboardButton(text='Закрепить документ📌', callback_data='pin')]
    buttons_list = [button1, button2]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    await message.answer(f'Выберите:', reply_markup=markup)


@dp.callback_query()
async def callback_query_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Проверка что выбрал пользователь
    :param callback_query: CallbackQuery
    :return: None
    """
    if callback_query.data == 'pin':
        await callback_query.message.answer('Введите название вашего документа:')
        await state.set_state(Form.first)

    elif callback_query.data == 'view':
        if not my_documents:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        markup = InlineKeyboardMarkup(
            inline_keyboard=[doc for doc in my_documents])
        await callback_query.message.answer(f'Ваши закрепленные документы:', reply_markup=markup)


@dp.message(F.text, Form.first)
async def first_func(message: Message, state: FSMContext):
    s = False
    for i in range(len(all_data)):
        if message.text.lower() == all_data[i]['document'].lower():
            url = all_data[i]['link'] if all_data[i]['link'] and all_data[i]['link'].startswith('https://') else \
                all_data[i]['note'] if all_data[i]['note'] and all_data[i]['note'].startswith('https://') else \
                    all_data[i]['offers']
            if not url or not url.startswith('https://'):
                continue
            my_documents.append([InlineKeyboardButton(text=all_data[i]['document'], url=url)]),
            s = True
    if s:
        await message.answer(f'Документ {message.text} закреплен!')
        return
    else:
        await message.answer(
            f'Документ {message.text} не найден!\nЛибо по вашему запросу найдено несколько документов!')
        return


@dp.message(F.text)
async def get_documents_handler(message: Message) -> None:
    """
    Обрабатывает сообщение пользователя,
    ищет совпадения в название документа и выдает все подходящие документы
    :param message: Message
    :return: None
    """
    # Проверка доступа
    if message.from_user.id != int(os.getenv('USERS_NAME')):
        await message.answer('У вас не доступа!🛑')
        return
    try:
        inline_kb_list = []
        await message.answer(f"Данные обрабатываются...⌛")
        # Поиск подходящих документов
        for i in range(len(all_data)):
            if message.text.lower() in all_data[i]['document'].lower():
                url = all_data[i]['link'] if all_data[i]['link'] and all_data[i]['link'].startswith('https://') else \
                    all_data[i]['note'] if all_data[i]['note'] and all_data[i]['note'].startswith('https://') else \
                        all_data[i]['offers']
                if not url or not url.startswith('https://'):
                    continue
                inline_kb_list.append([InlineKeyboardButton(text=all_data[i]['document'], url=url)]),
        markup = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
        await message.answer(f"По вашему запросу найдено {len(inline_kb_list)} результата(ов).", reply_markup=markup)
    # Обработка ошибок
    except Exception as e:
        print(f'Произошла ошибка: {str(e)}')
        await message.answer(f"Неверные данные или объем данных слишком велик! Введите другие данные:")


async def main() -> None:
    """
    Функция для запуска бота
    :return: None
    """
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


# Проверка, где запускается файл и запуск бота
if __name__ == "__main__":
    print('Starting...')
    asyncio.run(main())
