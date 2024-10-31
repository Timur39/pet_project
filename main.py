import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types import Message

from src.get_data import all_data

load_dotenv()
# Токен бота
TOKEN = os.getenv('TOKEN')
my_documents = []

dp = Dispatcher()


class Form(StatesGroup):
    pin = State()
    start = State()


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
        f'/help - список доступных команд')


@dp.message(Command('my_documents'))
async def my_documents_handler(message: Message) -> None:
    """
    Команда /my_documents, выводит клавиатуру для выбора: посмотреть мои документы или закрепить новый документ
    :param message: Message
    :return: None
    """
    button1 = [InlineKeyboardButton(text='Мои документы📄', callback_data='view')]
    button2 = [InlineKeyboardButton(text='Закрепить документ📌', callback_data='pin')]
    button3 = [InlineKeyboardButton(text='Открепить документ📌', callback_data='unpin')]
    buttons_list = [button1, button2, button3]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    await message.answer(f'Выберите:', reply_markup=markup)


@dp.callback_query()
async def callback_query_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Проверка что выбрал пользователь
    :param state: FSMContext
    :param callback_query: CallbackQuery
    :return: None
    """
    global my_documents
    data = callback_query.data
    if data == 'pin':
        await callback_query.message.answer('Введите название вашего документа:')
        await state.set_state(Form.pin)
    elif data == 'unpin':
        if not my_documents:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        else:
            docs = []
            for i in range(len(my_documents)):
                doc = my_documents[i][0].copy()
                doc.callback_data = f'{i}'
                doc.url = None
                docs.append([doc])
            markup = InlineKeyboardMarkup(inline_keyboard=docs)
            await callback_query.message.answer(f'Ваши закрепленные документы:', reply_markup=markup)
    elif data.isdigit():
        try:
            i = int(data)

            if len(my_documents) == 1:
                deleted_doc = my_documents.pop(0)
                await callback_query.answer(f'Документ {deleted_doc[0].text} откреплен')
            else:
                deleted_doc = my_documents.pop(i)
                await callback_query.answer(f'Документ {deleted_doc[0].text} откреплен')
        except:
            print('Error')
    elif data == 'view':
        if not my_documents:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        markup = InlineKeyboardMarkup(
            inline_keyboard=[doc for doc in my_documents])
        await callback_query.message.answer(f'Ваши закрепленные документы:', reply_markup=markup)
    elif data.split(' ')[0] == 'pin_document':
        i = int(data.split(' ')[1])
        url = all_data[i]['link'] if all_data[i]['link'] and all_data[i]['link'].startswith('https://') else \
            all_data[i]['note'] if all_data[i]['note'] and all_data[i]['note'].startswith('https://') else \
                all_data[i]['offers']

        if not [InlineKeyboardButton(text=all_data[i]['document'], url=url)] in my_documents:
            my_documents.append([InlineKeyboardButton(text=all_data[i]['document'], url=url)]),
            await callback_query.answer(f'Документ {all_data[i]['document']} закреплен')
        else:
            await callback_query.answer(f'Документ {all_data[i]['document']} уже закреплен')


@dp.message(F.text, Form.pin)
async def pin_document_func(message: Message, state: FSMContext):
    suitable_docs = []
    for i in range(len(all_data)):
        url = all_data[i]['link'] if all_data[i]['link'] and all_data[i]['link'].startswith('https://') else \
            all_data[i]['note'] if all_data[i]['note'] and all_data[i]['note'].startswith('https://') else \
                all_data[i]['offers']
        if message.text.lower() == all_data[i]['document'].lower():
            if [InlineKeyboardButton(text=all_data[i]['document'], url=url)] in my_documents:
                await message.answer(f'Документ {all_data[i]['document']} уже закреплен!')
                return
            elif not url or not url.startswith('https://'):
                continue
            my_documents.append([InlineKeyboardButton(text=all_data[i]['document'], url=url)]),
            await message.answer(f'Документ {all_data[i]['document']} закреплен!')
            return
        elif message.text.lower() in all_data[i]['document'].lower():
            if not url or not url.startswith('https://'):
                continue
            suitable_docs.append(
                [InlineKeyboardButton(text=all_data[i]['document'], callback_data=f'pin_document {i}')]),
    if not suitable_docs:
        await message.answer(
            f'Документ {message.text} не найден!\n')
        return
    else:
        markup = InlineKeyboardMarkup(inline_keyboard=suitable_docs)
        await message.answer(
            f'Документ {message.text} не найден!\nВозможно вы имели в виду:', reply_markup=markup)
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
    if message.from_user.id != int(os.getenv('USERS_ID')):
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
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
