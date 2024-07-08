from modules import admin_panel as adm, chatgpt as gpt, buttons as bt, dbdata as db
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove

from main import dp, bot, storage

class UserControl(StatesGroup):
    new_user: StatesGroup = State()
    get_contact_info: StatesGroup = State()

class AdminPanel(StatesGroup):
    per_page: StatesGroup = State()
    remove_user: StatesGroup = State()

start_text = '''
👨🏻‍💻 Привет! Я - сборник всяких модных новых штук из мира ИИ. У меня тут есть:\n
☑️ ChatGPT версии 4 (новинка!) и 3.5 (не забудь поиграться с настройкой ролей ассистента!)
☑️ Генерация изображений StableDiffusion
☑️ Модификация изображений Stable Diffusion
☑️ Поиск картинок через pexels.com '''

help_text = '''
Доступные команды:
/picsearch - поиск картинок
/stablediffusion - генерация картинок
/gpt_model_settings - выбор модели GPT (3/4)
/gpt_role_settings - выбор роли GPT
/settings - баланс и другие параметры
/flush - сбросить контекст GPT
/buy - пополнить баланс GPT'''

group_help_text = '''
В групповом чате общение с ChatGPT возможно только после слэша "/"
Например, "/привет, как дела?"
Другие команды:
/gpt_model_settings - выбор модели GPT (3/4)
/gpt_role_settings - выбор роли GPT
/flush - сбросить контекст GPT
Остальное в в личном чате с ботом'''


# Обработка команды /start
async def start_command_handler(message: types.Message):
    enabled_chats, admin = db.get_all_users()
    if str(message.from_user.id) in enabled_chats:
        if message.chat.type == 'group':
            await bot.send_message(message.chat.id, text='ChatGPT к вашим услугам')
        else:
            await bot.send_message(message.chat.id, text=f'{start_text}\n{help_text}')
    else:
        state = dp.get_current().current_state(chat=message.from_user.id, user=message.from_user.id)
        await state.set_state(UserControl.new_user)
        async with state.proxy() as data:
            data['message'] = message
        keyboard=types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard = True) 
        keyboard.add(types.KeyboardButton(text = "Отправить номер", request_contact = True))
        await bot.send_message(message.from_user.id, 'Давай знакомиться? Нажми на кнопку снизу и отправь мне свой контакт', reply_markup = keyboard) 

# Команда /help 
async def help_command_handler(message: types.Message):
    if message.chat.type == 'group':
        await message.reply(group_help_text)
    else:
        await message.reply(f'{start_text}\n{help_text}')

# # Текстовый запрос без FSM стейта
# async def default_text_message(message: types.Message):
#     await message.reply(f'Достпуные команды тут /help')

# Получаем запрос на добавление нового пользователя и отправляем сообщение админу
async def get_new_user_contact(message: types.Message, state: FSMContext):
    state = dp.get_current().current_state(chat=message.from_user.id, user=message.from_user.id)
    enabled_chats, admin = db.get_all_users()
    data = await state.get_data()
    print(data['message'])
    await state.set_state(UserControl.get_contact_info)
    await state.update_data(user_info = message)
    print(message)
    NEW_USER_BUTTONS = await bt.new_user_buttons(message.from_user.id)
    await bot.send_message(message.from_user.id, text=f'Заявка принята. Ожидайте', reply_markup = ReplyKeyboardRemove())
    await bot.send_message(admin, text=f'Запрос доступа к боту\nTelegram ID: {message.contact.user_id}\nИмя: {message.contact.first_name}\nТип: {message.chat.type}\nТелефон: {message.contact.phone_number}', reply_markup=NEW_USER_BUTTONS)

# Одобряем запрос на добавление нового пользователя и добавляем его в базу
async def register_user(message: types.CallbackQuery):
    user_id = message.data.split('_')[-1]
    state = dp.get_current().current_state(chat=user_id, user=user_id)
    data = await state.get_data()
    db.register_user(data['user_info'])
    await message.message.edit_text(text=f'Добавил пользователя {data["user_info"].chat.id} в базу')
    await bot.send_message(user_id, text=f'Вы зарегистрированы!')
    await state.finish()

# Отклоняем запрос пользователя
async def deny_user(message: types.CallbackQuery):
    user_id = message.data.split('_')[-1]
    state = dp.get_current().current_state(chat=user_id, user=user_id)
    await bot.send_message(message.from_user.id, text='Пользователю отказано в доступе')
    await bot.send_message(user_id, text=f'Вам отказано в доступе')
    await state.finish()

# Обработка команды /settings
async def admin_panel(message: types.Message):
    enabled_chats, admin = db.get_all_users()
    if str(message.from_user.id) == admin:
        users = db.get_saved_users()
        start_text, MNG_BUTTONS, per_page_users = await adm.manage_users(users, 1)
        msg = await bot.send_message(message.from_user.id, text=start_text, reply_markup=MNG_BUTTONS)
        await AdminPanel.per_page.set()
        state = dp.get_current().current_state()
        async with state.proxy() as data:
            data['msg'] = msg
            data['users'] = users
            data['per_page_users'] = per_page_users
    elif str(message.from_user.id) in enabled_chats:
        await bot.send_message(message.from_user.id, text=await adm.get_current_user_details(message.from_user.id)) 
    else:
        await bot.send_message(message.from_user.id, text=f'Доступ запрещен')
        await bot.send_message(admin, text=f'⛔️ Попытка попасть в настройки бота\nTelegram ID: {message.from_user.id}\nИмя: {message.chat.first_name} / {message.chat.title}\nТип: {message.chat.type}')

# Переключение между страницами в панели администратора
async def page_switcher_adm(message: types.CallbackQuery):
    state = dp.get_current().current_state()
    data = await state.get_data()
    # msg = data['msg']
    users = data['users']
    per_page_users = data['per_page_users']
    # await msg.delete()
    new_page = int(message.data.split('_')[-1])
    start_text, MNG_BUTTONS, per_page_users = await adm.manage_users(users, new_page)
    # msg = await bot.send_message(message.message.chat.id, text=start_text, reply_markup=MNG_BUTTONS)
    await message.message.edit_text(text=start_text, reply_markup=MNG_BUTTONS)
    state = dp.get_current().current_state()
    async with state.proxy() as data:
        # data['msg'] = msg
        data['page'] = new_page
        data['per_page_users'] = per_page_users

# Формирование инлайн клавиатуры для удаления пользователя
async def remove_user_menu(message: types.CallbackQuery):
    state = dp.get_current().current_state()
    data = await state.get_data()
    users = data['users']
    per_page_users = data['per_page_users']
    # await msg.delete()
    RMV_BUTTONS = await bt.remove_users_buttons(per_page_users)
    # msg2 = await bot.send_message(message.from_user.id, text='Выберите пользователя, которого нужно удалить', reply_markup=RMV_BUTTONS)
    await message.message.edit_text(text='Выберите пользователя, которого нужно удалить', reply_markup=RMV_BUTTONS)
    await AdminPanel.remove_user.set()
    # async with state.proxy() as data:
    #     data['msg2'] = msg2

# Нажатие на определенного пользователя в инлайн клавиатуре для удаления
async def remove_user_from_db(message: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # msg2 = data['msg2']
    user_id = int(message.data.split('_')[-1])
    # await msg2.delete()
    db.delete_user(user_id)
    # await bot.send_message(message.from_user.id, f'Удалил пользователя с id: {user_id}')
    await message.message.edit_text(text=f'Удалил пользователя с id: {user_id}')
    await state.finish()

# Выход из FSM
async def exit_fsm(message: types.CallbackQuery):
    await message.message.delete()
    state = dp.get_current().current_state()
    # data = await state.get_data()
    await state.set_state(state=None)

# Выдача айдишника контакта, для добавления в базу
async def get_contact_id(message: types.Message):
    print(message)
    await bot.send_message(message.from_user.id, text=f'Имя: {message.contact.first_name} {message.contact.last_name}\nTelegram ID: {message.contact.user_id}\nТелефон: {message.contact.phone_number}')
