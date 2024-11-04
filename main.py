import asyncio
import logging
import os
import sys
import time
from aiogram import Bot, Dispatcher, html
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types import Message
from dotenv import load_dotenv

from src.get_data import all_data
from src.postgres.main_db import create_table_users, insert_user, get_user_data, update_user_data

time.sleep(7)
load_dotenv()

# Токен бота
TOKEN = os.getenv('TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
my_documents = []

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()


class Form(StatesGroup):
    pin = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    Команда /start, приветствующая пользователя
    :param state: FSMContext
    :param message: Message
    :return: None
    """
    if await get_user_data(message.from_user.id):
        pass
    else:
        await insert_user({'user_id': message.from_user.id,
                           'full_name': message.from_user.full_name,
                           "attached_doc": [],
                           })
    await state.clear()
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
        f'/my_docs - ваши закрепленные документы\n'
        f'/all_docs - все документы\n'
        f'/help - список доступных команд')


@dp.message(Command('my_docs'))
async def my_documents_handler(message: Message) -> None:
    """
    Команда /my_docs, выводит клавиатуру для выбора: посмотреть мои документы или закрепить новый документ
    :param message: Message
    :return: None
    """
    button1 = [InlineKeyboardButton(text='Мои документы📄', callback_data='view')]
    button2 = [InlineKeyboardButton(text='Закрепить документ📌', callback_data='pin')]
    button3 = [InlineKeyboardButton(text='Открепить документ📌', callback_data='unpin')]
    buttons_list = [button1, button2, button3]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    await message.answer(f'Выберите:', reply_markup=markup)


@dp.message(Command('all_docs'))
async def all_docs_handler(message: Message, number: int = 0, cb_data: str = 'all') -> None:
    """
    Команда /all_docs, выводит все документы
    :param cb_data: str = 'all_data'
    :param number: int = 0
    :param message: Message
    :return: None
    """
    counter = 0
    docs = []
    url = ''
    for doc in all_data:
        if doc['link']:
            if doc['link'].startswith('https://') or doc['link'].startswith('http://'):
                url = doc['link']
        elif doc['note']:
            if doc['note'].startswith('https://') or doc['note'].startswith('http://'):
                url = doc['note']
        elif doc['offers']:
            if doc['offers'].startswith('https://') or doc['offers'].startswith('http://'):
                url = doc['offers']
        else:
            continue
        if number == 0 and len(docs) < 50:
            docs.append([InlineKeyboardButton(text=doc['document'], url=url)])
        elif number == 1 and len(docs) < 50:
            if counter <= 50:
                counter += 1
                continue
            docs.append([InlineKeyboardButton(text=doc['document'], url=url)])
        elif number == 2 and len(docs) < 50:
            if counter <= 100:
                counter += 1
                continue
            docs.append([InlineKeyboardButton(text=doc['document'], url=url)])
        else:
            if counter <= 150:
                counter += 1
                continue
            docs.append([InlineKeyboardButton(text=doc['document'], url=url)])
    if number != 3 and number != 2 if len(all_data) <= 200 else True:
        docs.append([InlineKeyboardButton(text='Показать еще...', callback_data=cb_data)])
    markup = InlineKeyboardMarkup(inline_keyboard=docs)
    await message.answer(f'Все документы:', reply_markup=markup)


@dp.callback_query()
async def callback_query_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Проверка что выбрал пользователь
    :param state: FSMContext
    :param callback_query: CallbackQuery
    :return: None
    """
    global my_documents
    user_data = await get_user_data(callback_query.from_user.id)
    data = callback_query.data
    if data == 'all':
        await all_docs_handler(callback_query.message, 1, 'all_2')
    elif data == 'all_2':
        await all_docs_handler(callback_query.message, 2, 'all_3')
    elif data == 'all_3':
        await all_docs_handler(callback_query.message, 3, 'all')
    elif data == 'pin':
        await callback_query.message.answer('Введите название вашего документа:')
        await state.set_state(Form.pin)
    elif data == 'unpin':
        if not user_data:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        elif not user_data['attached_doc']:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        else:
            docs = []
            for i in range(len(user_data['attached_doc']) // 2):
                doc = [InlineKeyboardButton(text='', callback_data=f'{i}')]
                docs.append(doc)
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
            pass
    elif data == 'view':
        if not user_data:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        elif not user_data['attached_doc']:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        buttons = []
        print([doc.split('*') for doc in user_data['attached_doc']])
        for doc in user_data['attached_doc']:
            buttons.append([InlineKeyboardButton(text=doc.split('*')[0], url=doc.split('*')[1])])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.answer(f'Ваши закрепленные документы:', reply_markup=markup)
    elif data.split(' ')[0] == 'pin_document':
        i = int(data.split(' ')[1])
        url = all_data[i]['link'] if all_data[i]['link'] and all_data[i]['link'].startswith('https://') else \
            all_data[i]['note'] if all_data[i]['note'] and all_data[i]['note'].startswith('https://') else \
            all_data[i]['offers']

        users_lst = []
        for doc in user_data['attached_doc']:
            users_lst.append(doc.split('*'))
        if not all_data[i]['document'] in [item for sublist in users_lst for item in sublist]:
            print(all_data[i]['document'])
            print([item for sublist in users_lst for item in sublist])
            my_documents.append([InlineKeyboardButton(text=all_data[i]['document'], url=url)]),
            await callback_query.answer(f'Документ {all_data[i]['document']} закреплен')
            user_data['attached_doc'] += [f'{all_data[i]['document']}*{url}']
            await update_user_data(user_data)
            await state.clear()
        else:
            await callback_query.answer(f'Документ {all_data[i]['document']} уже закреплен')
            await state.clear()



@dp.message(F.text, Form.pin)
async def pin_document_func(message: Message, state: FSMContext):
    suitable_docs = []
    user_data = await get_user_data(message.from_user.id)
    for i in range(len(all_data)):
        url = all_data[i]['link'] if all_data[i]['link'] and all_data[i]['link'].startswith('https://') else \
            all_data[i]['note'] if all_data[i]['note'] and all_data[i]['note'].startswith('https://') else \
            all_data[i]['offers']
        if message.text.lower() == all_data[i]['document'].lower():
            if all_data[i]['document'] in user_data['attached_doc']:
                await message.answer(f'Документ {all_data[i]['document']} уже закреплен!')
                await state.clear()
                return
            elif not url or not url.startswith('https://'):
                continue
            # my_documents.append([InlineKeyboardButton(text=all_data[i]['document'], url=url)]),
            await message.answer(f'Документ {all_data[i]['document']} закреплен!')
            await state.clear()
            user_data['attached_doc'] += [f'{all_data[i]['document']}*{url}']
            await update_user_data(user_data)
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
    # if message.from_user.id != int(os.getenv('USERS_ID')) and message.from_user.full_name != int(os.getenv('USERS_FULL_NAME')):
    #     await message.answer('У вас не доступа!🛑')
    #     return
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


async def on_startup() -> None:
    # Создаю базу данных и таблицу с пользователями
    await create_table_users()

    # Отправляю себе сообщение, что бот запущен
    await bot.send_message(chat_id=ADMIN_ID, text='Бот запущен!')


async def on_shutdown() -> None:
    # Отправляю себе сообщение, что бот остановлен
    await bot.send_message(chat_id=ADMIN_ID, text='Бот остановлен!')


async def main() -> None:
    """
    Функция для запуска бота
    :return: None
    """
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


# Проверка, где запускается файл и запуск бота
if __name__ == "__main__":
    print('Starting...')
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main())
