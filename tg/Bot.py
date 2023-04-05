import os

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, \
    KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from database import DataBase


API_TOKEN = os.environ["API_TOKEN_TG_SELLERBOT"]

db = DataBase()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class reg(StatesGroup):
    # для журналистов
    journalist_name = State()
    redaction = State()

    # для зрителей
    viewer_name = State()
    is_ready_to_go = State()


async def create_filter(message: types.Message):
    return 'admin_create' in message


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply(f"Здравствуйте! Это бот который регистрирует пользователей на мероприятия",
                        reply_markup=pool_button)


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.reply(
        'Если Вы хотите зарегистрироваться на мероприятие нажмите на кнопку '
        '"\\регистрация",\n'
        'Если Вы не помните регистрировались ли Вы нажмите на кнопку "\\проверка"')


@dp.message_handler(commands=['admin_help'])
async def admin_command(message: types.Message):
    if db.check_admin(message.from_user.id):
        await message.reply('Вы можете создать мероприятие, для этого'
                            'введите комманду admin_create, '
                            'название мероприятия и диапазон билетов')
    else:
        await message.reply('Вы не администратор')


@dp.message_handler(commands=['admin_create'])
async def create_command(message: types.Message):
    if db.check_admin(message.from_user.id):
        data = message.text.split()[1:]  # data = всё кроме команды
        db.add_event(data)
        await message.reply('Успешно')
    else:
        await message.reply('Вы не администратор')


@dp.message_handler(commands=['регистрация'])
async def reg_command(message: types.Message):
    await message.reply('Как именно Вы хотите зарегистрироваться?', reply_markup=inline_button_pool)


@dp.message_handler(commands=['проверка'])
async def check_command(message: types.Message):
    await message.reply('Введите "/мероприятия" для зрителей или "/естьвбазе" для журналистов')


@dp.message_handler(commands=['мероприятия'])
async def check_view(message: types.Message):
    if res := db.check_which_events_is_user_on(message.from_user.id):
        for events in res:
            # events[0] = название мероприятия
            await message.answer(f'Вы зарегистрированны на {events[0]}, номер билета {events[1]}')

    else:
        await message.answer('Вы не зарегистрированы ни на одно мероприятие')


@dp.message_handler(commands=['естьвбазе'])
async def check_journalist(message: types.Message):
    if db.check_journalist(message.from_user.id):
        await message.answer('Вы зарегистрированы')
    else:
        await message.answer('Вы не зарегистрированы')


@dp.message_handler(commands=['удаление'])
async def del_command(message: types.Message):
    await message.reply('Если Вы хотите удалиться из базы напишите '
                        '"/отказ"')


@dp.message_handler(commands=['отказ'])
async def remove_viewer_command(message: types.Message):
    db.remove_viewer(message.from_user.id)
    await message.answer('Вы удалены из базы')


registration_button = KeyboardButton('/регистрация')
checking_button = KeyboardButton('/проверка')
remove_button = KeyboardButton('/удаление')

pool_button = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)\
    .add(registration_button)\
    .add(checking_button)\
    .add(remove_button)

# Markup кнопок
inline_button_pool = InlineKeyboardMarkup()

# кнопки
inline_button1 = InlineKeyboardButton('Журналист', callback_data='but1')
inline_button2 = InlineKeyboardButton('Зритель', callback_data='but2')

inline_button_pool.add(inline_button1, inline_button2)


# ветвление кнопок
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('but'))
async def call_pool_button(callback_query: types.CallbackQuery):
    code = callback_query.data[-1]
    if code.isdigit():
        code = int(code)
    if code == 1:
        await bot.send_message(callback_query.from_user.id, 'Введите номер вашей аккредитации')
        await reg.journalist_name.set()
    if code == 2:
        await bot.send_message(callback_query.from_user.id, 'Введите номер билета')
        await reg.viewer_name.set()


# Для журналистов, так как он должен ввести номер и название газеты
@dp.message_handler(state=reg.journalist_name)
async def process_message(message: types.Message, state: FSMContext):
    await state.update_data(id=message.from_user.id)
    await state.update_data(name=message.text)
    await bot.send_message(message.from_user.id, 'Введите название Вашей редакции')
    await reg.redaction.set()


# регистрация журналиста
@dp.message_handler(state=reg.redaction)
async def process_message(message: types.Message, state: FSMContext):
    await reg.is_ready_to_go.set()
    await state.update_data(redact=message.text)
    user_data = await state.get_data()
    data = tuple(user_data.values())
    db.add_journalist(data)
    await message.reply('Вы успешно зарегистрированы')
    await state.reset_state()


# регистрация зрителя
@dp.message_handler(state=reg.viewer_name)
async def process_viewer(message: types.Message, state=FSMContext):
    await state.update_data(id=message.from_user.id)
    await state.update_data(name=message.text)
    await reg.is_ready_to_go.set()
    user_data = await state.get_data()
    data = tuple(user_data.values())
    db.add_viewer(data)
    await message.reply('Вы успешно зарегистрированы')
    await state.reset_state()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
