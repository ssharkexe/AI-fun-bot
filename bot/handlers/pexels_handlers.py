from modules import pexels, dbdata as db
from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import RetryAfter
from asyncio import sleep

from main import dp, bot

class PictureSearch(StatesGroup):
    search_promt: StatesGroup = State()
    per_page: StatesGroup = State()

# Обработка команды /picsearch - поиск изображений по запросу
async def send_pictures(message: types.Message):
    enabled_chats, admin = db.get_all_users()
    if str(message.from_user.id) in enabled_chats:
        await PictureSearch.search_promt.set()
        await bot.send_message(message.from_user.id, text='Я найду картинки по твоему запросу:')
    else:
        await bot.send_message(message.from_user.id, text=f'Доступ запрещен')

# Поиск изображений и их отправка пользователю
async def send_pictures_promt(message: types.Message, state: FSMContext):
    print('Пошли искать: ', message.text)
    telegram_id = message.from_user.id
    query = message.text
    async with state.proxy() as data:
        data['query'] = query
    media, text, BUTTONS = await pexels.main_pex_func(query, 1, telegram_id)
    if media == 0:
        await bot.send_message(message.from_user.id, text=text, reply_markup=BUTTONS)
    else:
        await PictureSearch.per_page.set()
        await bot.send_media_group(message.from_user.id, media=media)
        await bot.send_message(message.from_user.id, text=text, reply_markup=BUTTONS)

# Переключение между страницами в поиске изображений
async def page_switcher(message: types.CallbackQuery):
    await message.message.delete()
    telegram_id = message.from_user.id
    new_page = int(message.data.split('_')[-1])
    state = dp.get_current().current_state()
    data = await state.get_data()
    query = data['query']
    media, text, PAGE_BUTTONS = await pexels.main_pex_func(query, new_page, telegram_id)
    try:
        await bot.send_media_group(message.from_user.id, media=media)
        await bot.send_message(message.from_user.id, text=text, reply_markup=PAGE_BUTTONS)
    except RetryAfter:
        await sleep(45)
        await bot.send_media_group(message.from_user.id, media=media)
        await bot.send_message(message.from_user.id, text=text, reply_markup=PAGE_BUTTONS)

# Новый поиск изображений из коллбэка
async def new_pic_search(message: types.CallbackQuery):
    await message.message.delete()
    await PictureSearch.search_promt.set()
    await bot.send_message(message.from_user.id, text='Вводи новый запрос:')