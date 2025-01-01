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

import src.get_data_from_google_disk
from src.KonsultantPlus_get_data import get_data_by_name
from src.get_data_from_google_disk import all_data, all_data_with_folder, data_by_employees, get_data_from_spreadsheet, months
from src.keyboard import admin_kb, my_docs_kb, pin_doc_kb
from src.sqlite.main_db_sqlite import initialize_database, add_user, get_user_by_id, update_attached_docs, add_review, \
    get_all_review, get_all_users

load_dotenv()

# Токен бота
TOKEN = os.getenv('TOKEN')
# ID администратора и ID группы с отзывами
ADMIN_ID = int(os.getenv('ADMIN_ID'))
REVIEWS_ID = int(os.getenv('REVIEWS_ID'))

# Индекс месяца в списке months за который берутся данные
month = len(months) - 1

# Имя сотрудника
employee = ''

asyncio.sleep(5)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()


class Form(StatesGroup):
    pin = State()
    all_pin = State()
    reviews = State()
    consultant = State()
    employee_month = State()
    employee_name = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    Команда /start, приветствующая пользователя
    :param state: FSMContext
    :param message: Message
    :return: None
    """
    # Добавление пользователя в базу данных
    await add_user(message.from_user.id, message.from_user.full_name, str([]))

    await state.clear()
    message_for_admin = ''
    # Если пользователь является админом
    if message.from_user.id == ADMIN_ID:
        message_for_admin = '\n⚙️Команда для администратора - /admin'
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!\n"
        f"Я бот-помощник🤖, с помощью меня ты можешь:\n\n"
        f"1️⃣ Найти нужную тебе информацию из базы данных ОГС (Напиши название нужного тебе документа в 'Сообщение')\n\n"
        f"2️⃣ Посмотреть все документы из базы данных ОГС /all_docs\n\n"
        f"3️⃣ Закрепить информацию для быстрого доступа /my_docs\n\n"
        f"4️⃣ Посмотреть информацию о сотрудниках /employees_info\n\n\n"
        f"📝Отзыв/предложение/вопрос - /reviews{message_for_admin}")


@dp.message(Command('consultant_plus'))
async def consultant_plus_handler(message: Message, state: FSMContext) -> None:
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
    Команда /reviews, дает написать отзыв разработчику
    :param state:
    :param message: Message
    :return: None
    """
    # Добавление пользователя в базу данных
    await add_user(message.from_user.id, message.from_user.full_name, str([]))

    await message.answer('Напиши здесь отзыв/предложение/вопрос:')
    await state.set_state(Form.reviews)


@dp.message(Command('my_docs'))
async def my_documents_handler(message: Message) -> None:
    """
    Команда /my_docs, выводит клавиатуру для выбора:
    * посмотреть мои документы
    * закрепить новый документ
    * открепить закрепленный документ
    :param message: Message
    :return: None
    """
    # Добавление пользователя в базу данных
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    # Появление клавиатуры с выбором
    await message.answer(f'Выберите:', reply_markup=my_docs_kb())


@dp.message(Command('all_docs'))
async def all_docs_handler(message: Message, number1: int = 0, number2: int = 50) -> None:
    """
    Команда /all_docs, выводит все документы из папки Гарантийные обязательства,
    структурировав их по папкам
    :param number1: int = 0
    :param number2: int = 10
    :param message: Message
    :return: None
    """
    global folder
    global button_data_stack
    global folders_stack
    # Добавление пользователя в базу данных
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    # Сбрасывание всех переменных
    folder = all_data_with_folder
    button_data_stack = []
    folders_stack = []
    # Создание клавиатуры со всеми данными из папки Гарантийные обязательства, структурировав их по папкам
    docs = []
    for folder2 in all_data_with_folder[number1:number2]:
        if folder2['documents']:
            docs.append([InlineKeyboardButton(text=folder2['name'], callback_data=folder2['data'])])
        else:
            docs.append([InlineKeyboardButton(text=folder2['name'], url=folder2['link'])])
    markup = InlineKeyboardMarkup(inline_keyboard=docs)

    # Вывод всех документов из папки гарантийные обязательства
    await message.answer(f'Все документы:', reply_markup=markup)


@dp.message(Command('admin'))
async def admin_handler(message: Message) -> None:
    """
    Команда /admin, выводит клавиатуру для администрирования бота
    :param message: Message
    :return: None
    """
    # Проверка на админа
    if message.from_user.id == ADMIN_ID:
        # Вывод клавиатуры
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='⚙️Админка')]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer('Вы администратор данного бота!', reply_markup=markup)
    else:
        await message.answer('Вы не являетесь администратором!')


@dp.message(Command('employees_info'))
async def employees_info_handler(message: Message, state: FSMContext) -> None:
    """
    Команда /employees_info, выводит информацию о сотрудниках
    :param state:
    :param message: Message
    :return: None
    """
    markup = [[KeyboardButton(text=employee['name'])] for employee in data_by_employees]
    markup.append([KeyboardButton(text='Выйти')])
    keyboard = ReplyKeyboardMarkup(
        keyboard=markup,
        resize_keyboard=True
    )
    await state.set_state(Form.employee_name)
    await message.answer('Сотрудники:', reply_markup=keyboard)


@dp.message((F.text.in_([employee_1['name'] for employee_1 in data_by_employees])) | (F.text == 'Выйти'), Form.employee_name)
async def get_employees_info_name(message: Message, state: FSMContext):
    global employee
    if message.text == 'Выйти':
        markup = ReplyKeyboardRemove()
        await message.answer('Выход произошел успешно', reply_markup=markup)
        return
    markup = [[KeyboardButton(text=month)] for month in months]
    markup.append([KeyboardButton(text='Назад')])

    keyboard = ReplyKeyboardMarkup(
        keyboard=markup,
        resize_keyboard=True
    )
    employee = message.text
    await message.answer('Месяцы:', reply_markup=keyboard)
    await state.set_state(Form.employee_month)


@dp.message((F.text.in_(months)) | (F.text == 'Назад'), Form.employee_month)
async def get_employees_info_months(message: Message, state: FSMContext):
    if message.text == 'Назад':
        await employees_info_handler(message, state)
        return
    criteria = {
        0: 'Отсутствие просроченных обращений по гарантии.\nСтепень',
        1: 'Значение',
        2: 'Кол-во м2 на сотрудника',
        3: 'Кол-во заявок к отработке в месяц',
        4: 'Кол-во заявок завершено в месяц',
        5: 'Кол-во заявок в работе с просроком',
        6: 'Кол-во заявок завершенных с просроком',
        7: 'Дней в работе',
        8: 'Оценка за качество исполнения заявок (CSI клиентов).\nСтепень',
        9: 'Значение',
        10: 'Своевременное предоставление информации для подготовки ответа на претензию от собственника.\nСтепень',
        11: 'Значение',
        12: 'Внесение предложений по улучшению для Техсовета.',
        13: 'Предоставлять фотофиксацию недостатков',
        14: 'Подготовка пакета документов для замены ИПУ. Контроль наличия ИПУ на складе. Соблюдение утвержденного процесса.',
        15: 'Ведение отчетности на диске Z',
    }
    data_by_employees = await get_data_from_spreadsheet(months.index(message.text))
    for employee_data in data_by_employees:
        if employee_data['name'] == employee:
            info = ''
            db_info = ''
            for i in range(len(employee_data['info'])):
                if employee_data['info'][i] is None:
                    db_info = 'Нет данных'
                elif employee_data['info'][i] is False:
                    db_info = '❌'
                elif employee_data['info'][i] is True:
                    db_info = '✅'
                else:
                    db_info = employee_data['info'][i]

                info += f'{criteria[i]} - <b>{db_info}</b>\n'
            await message.answer(f"<b>{employee_data['name']}</b> \n"
                                 f"{info}")


@dp.callback_query()
async def callback_query_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработка callback данных (на какую кнопку нажал пользователь)
    :param state: FSMContext
    :param callback_query: CallbackQuery
    :return: None
    """
    # Добавление пользователя в базу данных
    await add_user(callback_query.from_user.id, callback_query.message.from_user.full_name, str([]))
    # Получаем данные пользователя из базы данных
    user_data = await get_user_by_id(callback_query.from_user.id)

    # Обработка callback данных
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
    elif data == 'By_name':
        await callback_query.message.answer('Введите название документа:')
        await state.set_state(Form.pin)
    elif data == 'By_all_docs':
        await pin_all_document_func(callback_query.message)
    elif data == 'pin':
        await callback_query.message.answer('Закрепить документ:', reply_markup=pin_doc_kb())
    elif data == 'unpin':
        if not user_data['attached_docs']:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        docs = []
        for i in range(len(user_data['attached_docs'])):
            doc_button = [InlineKeyboardButton(
                text=user_data['attached_docs'][i][0],
                callback_data=f'{len(user_data['attached_docs'][i][0])} {user_data['attached_docs'][i][0][:30]}'
            )]
            docs.append(doc_button)
        markup = InlineKeyboardMarkup(inline_keyboard=docs)
        await callback_query.message.answer(f'Ваши закрепленные документы:', reply_markup=markup)
    # Обработка нажатия, какой документ нужно открепить
    elif data.split(' ')[0].isdigit():
        data = data.split(' ')
        for i in range(len(user_data['attached_docs'])):
            if int(data[0]) == len(user_data['attached_docs'][i][0]) and data[1] in user_data['attached_docs'][i][0]:
                await callback_query.answer(f'Документ {user_data['attached_docs'][i][0]} откреплен')
                # Удаляю документ
                user_data['attached_docs'].remove(user_data['attached_docs'][i])
                # Обновляю базу данных
                await update_attached_docs(callback_query.from_user.id, str(user_data['attached_docs']))
                return
        await callback_query.answer(f'Документ не закреплен')
    # Обработка нажатия, какой документ нужно закрепить
    elif data.split(' ')[0] == 'pin_document':
        i = int(data.split(' ')[1])
        url = all_data[i]['link']

        if not all_data[i]['name'] in [doc[0] for doc in user_data['attached_docs']]:
            await callback_query.answer(f'Документ {all_data[i]['name']} закреплен')
            # Добавляю документ
            user_data['attached_docs'].append([all_data[i]['name'], url])
            # Обновляю бд
            await update_attached_docs(callback_query.from_user.id, str(user_data['attached_docs']))

            await state.clear()
        else:
            await callback_query.answer(f'Документ {all_data[i]['name']} уже закреплен')
            await state.clear()
    elif data == 'view':
        if not user_data['attached_docs']:
            await callback_query.message.answer(f'У вас нет закрепленных документов!')
            return
        buttons = []
        for doc in user_data['attached_docs']:
            buttons.append([InlineKeyboardButton(text=doc[0], url=doc[1])])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.answer(f'Ваши закрепленные документы:', reply_markup=markup)
    else:
        await callback_query_handler_all(callback_query, state)


# Текущая папка
folder = all_data_with_folder

# Данные нужной папки
button_data_stack = []

# Папки
folders_stack = []


@dp.callback_query()
async def callback_query_handler_all(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработка нажатия на папку, при выдаче всех документов командой /all_docs
    :param callback_query: CallbackQuery
    :param state: FSMContext
    :return: None
    """
    global folder
    global folders_stack
    global button_data_stack

    data = callback_query.data
    if data:
        # Если нажата кнопка Назад
        if data == 'back':
            # Изменение папки для поиска
            folders_stack.pop()
            # Изменение папки, которую нужно открыть
            button_data_stack.pop()
            if button_data_stack and folders_stack:
                data = button_data_stack[-1]
                folder = folders_stack[-1]
            else:
                await callback_query.message.delete()
                await all_docs_handler(callback_query.message)
                return

        if not folder:
            folder = all_data_with_folder

        buttons = []
        # Обработка данных в папке
        for i in folder:
            # Поиск в ней подходящей папки
            if data == i['data']:
                if i['documents']:
                    folders_stack.append(folder) if not folder in folders_stack else None
                    button_data_stack.append(i['data']) if not i['data'] in button_data_stack else None
                    folder = i['documents']
                    for j in i['documents']:
                        if not j.get('documents'):
                            buttons.append([InlineKeyboardButton(text=j['name'], url=j['link'])])
                        else:
                            buttons.append([InlineKeyboardButton(text=j['name'], callback_data=j['data'])])
                else:
                    buttons.append([InlineKeyboardButton(text='Пусто', callback_data='пусто')])
        buttons.append([InlineKeyboardButton(text='Назад', callback_data='back')])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        # Удаление прошлого сообщение
        await callback_query.message.delete()
        # Выдача нового сообщения
        await callback_query.message.answer('Выберите документ:', reply_markup=markup)


@dp.message((F.from_user.id == ADMIN_ID) & (F.text == '⚙️Админка'))
async def admin_view_kb(message: Message) -> None:
    """
    Отображение кнопок админки
    :param message: Message
    :return: None
    """
    await message.answer('Админка активирована!', reply_markup=admin_kb())


@dp.message(F.text, Form.consultant)
async def consultant_plus_handler(message: Message, state: FSMContext, document: str = '', number1: int = 0,
                                  number2: int = 10) -> None:
    """
    Команда /consultant_plus, получает и отдает пользователю информации из ConsultantPlus'а
    :param number2: int = 10
    :param number1: int = 0
    :param document: str = ''
    :param state: FSMContext
    :param message: Message
    :return: None
    """
    # Если запущен в первый раз
    if number1 == 0:
        document = message.text
    consultant_data = []
    # Проверка, что данные пришли правильно
    if not get_data_by_name(document):
        consultant_data = get_data_by_name(document)
    else:
        consultant_data = get_data_by_name(document)
    # Если ничего не найдено
    if not consultant_data:
        await message.answer('Ничего не найдено.')
    else:
        # Обработка данных
        for data in consultant_data[number1:number2]:
            if consultant_data.index(data) == number2 - 1 and len(consultant_data) > number2:
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text='Показать еще...',
                        callback_data=f'add_10*{number1}*{number2}*{document}'
                    )]
                ])
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
    # Добавление пользователя в базу данных
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    # Добавление отзыва в базу данных
    await add_review(message.from_user.full_name, message.text)

    await message.answer(f'Отзыв отправлен разработчику!')
    # Отправка отзыва
    await bot.send_message(REVIEWS_ID, f'{message.from_user.full_name} добавил(а) отзыв: {message.text}')
    await state.clear()


@dp.message(F.text, Form.pin)
async def pin_document_func(message: Message, state: FSMContext) -> None:
    """
    Функция для добавления документов в базу данных
    :param message: Message
    :param state: State
    :return: None
    """
    # Добавление пользователя в базу данных
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    # Получение данных пользователя
    user_data = await get_user_by_id(message.from_user.id)
    # Подходящие документы
    suitable_docs = []
    # Обработка данных, поиск подходящий документов
    for i in range(len(all_data)):
        url = all_data[i]['link']
        # Если документ указан точно
        if message.text.lower() == all_data[i]['name'].lower():
            # Если документ уже закреплен
            if all_data[i]['name'] in [doc[0] for doc in user_data['attached_docs']]:
                await message.answer(f'Документ {all_data[i]['name']} уже закреплен!')
                await state.clear()
                return

            await message.answer(f'Документ {all_data[i]['name']} закреплен!')

            await state.clear()
            # Добавление документа
            user_data['attached_docs'].append([all_data[i]['name'], url])
            # Обновление базы данных
            await update_attached_docs(message.from_user.id, str(user_data['attached_docs']))
            return
        # Если есть подходящие документы
        elif message.text.lower() in all_data[i]['name'].lower():
            suitable_docs.append(
                [InlineKeyboardButton(text=all_data[i]['name'], callback_data=f'pin_document {i}')]),
    # Если нет подходящих документов
    if not suitable_docs:
        await message.answer(
            f'Документ {message.text} не найден!\n')
        return
    markup = InlineKeyboardMarkup(inline_keyboard=suitable_docs)
    await message.answer(
        f'Документ {message.text} не найден!\nВозможно вы имели в виду:', reply_markup=markup)


async def pin_all_document_func(message: Message, number1: int = 0, number2: int = 50) -> None:
    """
    Функция для выбора из всех документов для добавления их в базу данных
    :param message: Message
    :param number1: int = 0
    :param number2: int = 50
    :return: None
    """
    # Добавление пользователя в базу данных
    await add_user(message.from_user.id, message.from_user.full_name, str([]))
    # Получение данных пользователя
    user_data = await get_user_by_id(message.from_user.id)

    docs = []
    # Вывод всех документов для закрепления
    for data in all_data[number1:number2]:
        docs.append([InlineKeyboardButton(text=data['name'], callback_data=f'pin_document {all_data.index(data)}')])
    # Если документов много, то добавить кнопку Показать еще...
    if len(all_data) > number2:
        docs.append([InlineKeyboardButton(text='Показать еще...', callback_data=f'pin_all*{number1}*{number2}')])
    markup = InlineKeyboardMarkup(inline_keyboard=docs)
    await message.answer(f'Все документы:', reply_markup=markup)


@dp.message(F.text, F.from_user.id == ADMIN_ID)
async def admin_access(message: Message, state: FSMContext) -> None:
    """
    Обработка нажатия кнопок в админке
    :param message: Message
    :param state: FSMContext
    :return: None
    """
    if message.text == '👥 Пользователи':
        # Получение всех пользователей
        all_users = await get_all_users()
        # Вывод их админу
        for user in all_users:
            await message.answer(
                f'<span class="tg-spoiler">{user['user_id']}</span> {user['full_name']}\nЗакрепленных документов: {len(user['attached_docs'])}')
    elif message.text == '📝 Отзывы':
        # Получение всех отзывов
        all_reviews = await get_all_review()
        # Вывод их админу
        for review in all_reviews:
            await message.answer(f'{review['full_name']} - {review['review']}')
        # Если нет отзывов
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
    # Добавление пользователя в базу данных
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
    # Добавление логирования
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main())
