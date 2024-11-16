import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, html
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardRemove
from aiogram.types import Message
from dotenv import load_dotenv

from src.KonsultantPlus_get_data import get_data_by_name
from src.keyboard import admin_kb
from src.sqlite.main_db_sqlite import initialize_database, add_user, get_user_by_id, update_attached_docs, add_review, \
    get_all_review, get_all_users
from src.get_data_from_google_disk import all_data, all_data_with_folder

load_dotenv()

# Токен бота
TOKEN = os.getenv('TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()


class Form(StatesGroup):
    pin = State()
    all_pin = State()
    reviews = State()
    consultant = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    Команда /start, приветствующая пользователя
    :param state: FSMContext
    :param message: Message
    :return: None
    """
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    await state.clear()
    message_for_admin = ''
    if message.from_user.id == ADMIN_ID:
        message_for_admin = '\n⚙️Команда для администратора - /admin'
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!\n"
        f"Я бот-помощник🤖, с помощью меня ты можешь:\n\n"
        f"1️⃣ Найти нужную тебе информацию из базы данных ОГС (Напиши название нужного тебе документа в 'Сообщение')\n\n"
        f"2️⃣ Посмотреть все документы из базы данных ОГС /all_docs\n\n"
        f"3️⃣ Закрепить информацию для быстрого доступа /my_docs\n\n\n"
        f"📝Отзыв/предложение/вопрос - /reviews{message_for_admin}")


@dp.message(Command('consultant_plus'))
async def consultant_plus_handler(message: Message, state: FSMContext):
    """
    Команда /consultant_plus, вызывает функцию получения информации из ConsultantPlus
    :param: message: Message
    :param: state: FSMContext
    :return: None
    """
    await message.answer('Напишите что хотите найти (кодекс, закон или другие материалы): ')
    await state.set_state(Form.consultant)


@dp.message(Command('reviews'))
async def reviews_handler(message: Message, state: FSMContext) -> None:
    """
    Команда /reviews, дает написать отзыв
    :param state:
    :param message: Message
    :return: None
    """
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    await message.answer('Напиши здесь отзыв/предложение/вопрос:')
    await state.set_state(Form.reviews)


@dp.message(Command('my_docs'))
async def my_documents_handler(message: Message) -> None:
    """
    Команда /my_docs, выводит клавиатуру для выбора: посмотреть мои документы или закрепить новый документ
    :param message: Message
    :return: None
    """
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    button1 = [InlineKeyboardButton(text='Мои документы📄', callback_data='view')]
    button2 = [InlineKeyboardButton(text='Закрепить документ📌', callback_data='pin')]
    button3 = [InlineKeyboardButton(text='Открепить документ📌', callback_data='unpin')]
    buttons_list = [button1, button2, button3]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    await message.answer(f'Выберите:', reply_markup=markup)


# TODO: структурировать по папкам
@dp.message(Command('all_docs'))
async def all_docs_handler(message: Message, number1: int = 0, number2: int = 50) -> None:
    """
    Команда /all_docs, выводит все документы из документа Сводная информация ОГС
    :param number1: int = 0
    :param number2: int = 10
    :param message: Message
    :return: None
    """
    await add_user(message.from_user.id, message.from_user.full_name, str([]))

    docs = []
    # print(all_data_with_folder)
    # for folder in all_data_with_folder[number1:number2]:
    #     docs.append([InlineKeyboardButton(text=folder['name'], callback_data=folder['data'])])
    for doc in all_data[number1:number2]:
        docs.append([InlineKeyboardButton(text=doc['name'], url=doc['link'])])
    if len(all_data) > number2:
        docs.append([InlineKeyboardButton(text='Показать еще...', callback_data=f'pin_all*{number1}*{number2}')])
    markup = InlineKeyboardMarkup(inline_keyboard=docs)
    await message.answer(f'Все документы:', reply_markup=markup)


@dp.message(Command('admin'))
async def admin_handler(message: Message):
    if message.from_user.id == ADMIN_ID:
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='⚙️Админка')]], resize_keyboard=True,
                                     one_time_keyboard=True)
        await message.answer('Вы администратор данного бота!', reply_markup=markup)
    else:
        await message.answer('Вы не являетесь администратором!')


@dp.callback_query()
async def callback_query_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Проверка что выбрал пользователь
    :param state: FSMContext
    :param callback_query: CallbackQuery
    :return: None
    """

    await add_user(callback_query.from_user.id, callback_query.message.from_user.full_name, str([]))

    user_data = await get_user_by_id(callback_query.from_user.id)
    data = callback_query.data
    if data.split('*')[0] == 'all':
        data = data.split('*')
        await all_docs_handler(callback_query.message, int(data[1]) + 50, int(data[2]) + 50)
    elif data.split('*')[0] == 'pin_all':
        data = data.split('*')
        await pin_all_document_func(callback_query.message, int(data[1]) + 50, int(data[2]) + 50)
    elif 'add_10' in data:
        data = data.split('*')
        data2 = ''
        if len(data) >= 4:
            data2 = data[3]
        await consultant_plus_handler(callback_query.message, state, data2, int(data[1]) + 10,
                                      int(data[2]) + 10)
    elif data == 'pin':
        button1 = [InlineKeyboardButton(text='Посмотреть все документы📁', callback_data='By_all_docs')]
        button2 = [InlineKeyboardButton(text='По названию📛', callback_data='By_name')]
        buttons = [button1, button2]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.answer('Закрепить документ:', reply_markup=markup)
    elif data == 'By_name':
        await callback_query.message.answer('Введите название документа:')
        await state.set_state(Form.pin)
    elif data == 'By_all_docs':
        await pin_all_document_func(callback_query.message)
    elif data == 'unpin':
        if not user_data['attached_docs']:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        else:
            docs = []
            for i in range(len(user_data['attached_docs'])):
                doc_button = [InlineKeyboardButton(text=user_data['attached_docs'][i][0],
                                                   callback_data=f'{len(user_data['attached_docs'][i][0])} {user_data['attached_docs'][i][0][:30]}')]
                docs.append(doc_button)
            markup = InlineKeyboardMarkup(inline_keyboard=docs)
            await callback_query.message.answer(f'Ваши закрепленные документы:', reply_markup=markup)
    elif data.split(' ')[0].isdigit():
        data = data.split(' ')
        for i in range(len(user_data['attached_docs'])):
            if int(data[0]) == len(user_data['attached_docs'][i][0]) and data[1] in user_data['attached_docs'][i][0]:
                await callback_query.answer(f'Документ {user_data['attached_docs'][i][0]} откреплен')
                user_data['attached_docs'].remove(user_data['attached_docs'][i])
                await update_attached_docs(callback_query.from_user.id, str(user_data['attached_docs']))
                return

        await callback_query.answer(f'Документ не закреплен')
    elif data == 'view':
        if not user_data['attached_docs']:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        buttons = []
        for doc in user_data['attached_docs']:
            buttons.append([InlineKeyboardButton(text=doc[0], url=doc[1])])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.answer(f'Ваши закрепленные документы:', reply_markup=markup)
    elif data.split(' ')[0] == 'pin_document':
        i = int(data.split(' ')[1])
        url = all_data[i]['link']

        if not all_data[i]['name'] in [doc[0] for doc in user_data['attached_docs']]:
            await callback_query.answer(f'Документ {all_data[i]['name']} закреплен')
            user_data['attached_docs'].append([all_data[i]['name'], url])

            await update_attached_docs(callback_query.from_user.id, str(user_data['attached_docs']))
            await state.clear()
        else:
            await callback_query.answer(f'Документ {all_data[i]['name']} уже закреплен')
            await state.clear()


@dp.message((F.from_user.id == ADMIN_ID) & (F.text == '⚙️Админка'))
async def admin_access(message: Message):
    markup = admin_kb()
    await message.answer('Админка активирована!', reply_markup=markup)


@dp.message(F.text, Form.consultant)
async def consultant_plus_handler(message: Message, state: FSMContext, document: str = '', number1: int = 0,
                                  number2: int = 10):
    """
    Команда /consultant_plus, вызывает функцию получения информации из ConsultantPlus
    :param document: str = message.text
    :param number2: int = 0
    :param number1: int = 10
    :param message: Message
    :param state: FSMContext
    :return: None
    """
    if number1 == 0:
        document = message.text
    consultant_data = []
    if not get_data_by_name(document):
        consultant_data = get_data_by_name(document)
    else:
        consultant_data = get_data_by_name(document)
    if not consultant_data:
        await message.answer('Ничего не найдено.')
    else:
        for data in consultant_data[number1:number2]:
            if consultant_data.index(data) == number2 - 1 and len(consultant_data) > number2:
                buttons = [[InlineKeyboardButton(text='Показать еще...',
                                                 callback_data=f'add_10*{number1}*{number2}*{document}')]]
                markup = InlineKeyboardMarkup(inline_keyboard=buttons)
                await message.answer(
                    f'<a href="{data['link']}"><b>{data['name'][1]}</b></a>\n{data['name'][2] if len(data['name']) > 2 else ''}',
                    reply_markup=markup)
            else:
                await message.answer(
                    f'<a href="{data['link']}"><b>{data['name'][1]}</b></a>\n{data['name'][2] if len(data['name']) > 2 else ''}')

        await state.clear()


@dp.message(F.text, Form.reviews)
async def reviews_function(message: Message, state: FSMContext) -> None:
    """
    Отправляем отзыв разработчику
    :param message: Message
    :param state: FSMContext
    :return: None
    """
    await add_user(message.from_user.id, message.from_user.full_name, str([]))

    await add_review(message.from_user.full_name, message.text)

    await message.answer(f'Отзыв отправлен разработчику!')
    await bot.send_message(-4579349386, f'{message.from_user.full_name} добавил(а) отзыв: {message.text}')
    await state.clear()


@dp.message(F.text, Form.pin)
async def pin_document_func(message: Message, state: FSMContext):
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    user_data = await get_user_by_id(message.from_user.id)
    suitable_docs = []

    for i in range(len(all_data)):
        url = all_data[i]['link']

        if message.text.lower() == all_data[i]['name'].lower():
            if all_data[i]['name'] in [doc[0] for doc in user_data['attached_docs']]:
                await message.answer(f'Документ {all_data[i]['name']} уже закреплен!')
                await state.clear()
                return

            await message.answer(f'Документ {all_data[i]['name']} закреплен!')

            await state.clear()

            user_data['attached_docs'].append([all_data[i]['name'], url])
            await update_attached_docs(message.from_user.id, str(user_data['attached_docs']))
            return
        elif message.text.lower() in all_data[i]['name'].lower():
            suitable_docs.append(
                [InlineKeyboardButton(text=all_data[i]['name'], callback_data=f'pin_document {i}')]),
    if not suitable_docs:
        await message.answer(
            f'Документ {message.text} не найден!\n')
        return
    else:
        markup = InlineKeyboardMarkup(inline_keyboard=suitable_docs)
        await message.answer(
            f'Документ {message.text} не найден!\nВозможно вы имели в виду:', reply_markup=markup)
        return


# TODO: структурировать по папкам
async def pin_all_document_func(message: Message, number1: int = 0, number2: int = 50):
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    user_data = await get_user_by_id(message.from_user.id)

    docs = []
    for data in all_data[number1:number2]:
        docs.append([InlineKeyboardButton(text=data['name'], callback_data=f'pin_document {all_data.index(data)}')])
    if len(all_data) > number2:
        docs.append([InlineKeyboardButton(text='Показать еще...', callback_data=f'pin_all*{number1}*{number2}')])
    markup = InlineKeyboardMarkup(inline_keyboard=docs)
    await message.answer(f'Все документы:', reply_markup=markup)


@dp.message(F.text, F.from_user.id == ADMIN_ID)
async def admin_access(message: Message, state: FSMContext):
    if message.text == '👥 Пользователи':
        all_users = await get_all_users()
        for user in all_users:
            await message.answer(
                f'<span class="tg-spoiler">{user['user_id']}</span> {user['full_name']}\nЗакрепленных документов: {len(user['attached_docs'])}')
    elif message.text == '📝 Отзывы':
        all_reviews = await get_all_review()
        for review in all_reviews:
            await message.answer(f'{review['full_name']} - {review['review']}')
        if len(all_reviews) == 0:
            await message.answer(f'Отзывов нет!')
    elif message.text == '⬅️ Выйти из админки':
        remove_markup = ReplyKeyboardRemove()
        await message.answer(f'Админка деактивирована!', reply_markup=remove_markup)
    else:
        await get_documents_handler(message)


@dp.message(F.text)
async def get_documents_handler(message: Message) -> None:
    """
    Обрабатывает сообщение пользователя,
    ищет совпадения в название документа и выдает все подходящие документы
    :param message: Message
    :return: None
    """
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    try:
        inline_kb_list = []
        await message.answer(f"Данные обрабатываются...⌛")
        # Поиск подходящих документов
        for i in range(len(all_data)):
            if message.text.lower() in all_data[i]['name'].lower():
                url = all_data[i]['link']
                for button in inline_kb_list:
                    if button[0].url == url:
                        continue
                inline_kb_list.append([InlineKeyboardButton(text=all_data[i]['name'], url=url)]),
        markup = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
        await message.answer(f"По вашему запросу найдено {len(inline_kb_list)} результата(ов).", reply_markup=markup)
    # Обработка ошибок
    except Exception as e:
        print(f'Произошла ошибка: {str(e)}')
        await message.answer(f"Неверные данные или объем данных слишком велик! Введите другие данные:")


async def on_startup() -> None:
    # Создаю базу данных и таблицу с пользователями
    await initialize_database()
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
