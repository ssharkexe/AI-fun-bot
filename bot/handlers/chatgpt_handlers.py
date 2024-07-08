from modules import chatgpt as gpt, buttons as bt, dbdata as db
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State, default_state

from main import dp, bot

class FSMGptChat(StatesGroup):
    activate_chat: StatesGroup = State()

# Обработка входящих сообщений от пользователей    
async def handle_message(message: types.Message):
    user_exists = db.check_user(message.from_user.id)
    if user_exists:
        if user_exists.gpt_chat_credits > 0:
            print(f'Баланс {message.from_user.id} = {user_exists.gpt_chat_credits}')
            # await FSMGptChat.activate_chat.set()
            state = dp.get_current().current_state(chat=message.chat.id, user=message.chat.id)
            await state.set_state(FSMGptChat.activate_chat)
            # await message.reply(f'ChatGPT слушает')
            try:
                data = await state.get_data()
                gpt_model = data['gpt_model']
            except KeyError:
                print('Не нашел настройки модели GPT')
                gpt_model = 3
            try:
                data = await state.get_data()
                contexts = data['contexts']
            except KeyError:
                print(f'С {message.from_user.id} еще не общались')
                contexts = {}
            contexts, gpt_reply = await gpt.handle_message(message.chat.id, message.text, contexts, gpt_model)
            await state.update_data(contexts = contexts)
            try:
                await message.reply(gpt_reply)
            except:
                await message.reply(f'Кажется, в ответе нейросети много кода')
        else:
            await message.reply(f'Пожалуйста, пополните баланс, чтобы пользоваться ChatGPT /buy')
    else:
        print(f'В чате {message.chat.id} пользователь {message.from_user.id} пытается воспользоваться chatGPT')
        await message.reply('Извини, доступ запрещен\nЕсли хотите пользоваться ботом, нажмите /start')

# Команда настройки стиля собеседника GPT 
async def assistant_role_menu(message: types.Message):
    user_exists = db.check_user(message.from_user.id)
    if user_exists:
        GPT_BUTTONS = await bt.chatgpt_roles()
        await bot.send_message(message.chat.id, text='Выбери стиль собеседника', reply_markup=GPT_BUTTONS)
    else:
        await bot.send_message(message.chat.id, text='Извини, доступ запрещен\nЕсли хотите пользоваться ботом, нажмите /start')

# Выбор стиля собеседника GPT 
async def assistant_role_change(message: types.CallbackQuery):
    # await message.message.delete()
    gpt_role_index = int(message.data.split('_')[-1])
    state = dp.get_current().current_state(chat=message.message.chat.id, user=message.message.chat.id)
    # state = dp.get_current().current_state()
    try:
        data = await state.get_data()
        contexts = data['contexts']
    except KeyError:
        print(f'С {message.message.chat.id} еще не общались')
        contexts = {}
    contexts, text = await gpt.assistant_role_setting(message.message.chat.id, gpt_role_index, contexts) #передаем айдишник чата, записываем настройку в контекст чата
    await state.update_data(contexts = contexts)
    await message.message.edit_text(text=text)

# Команда настройки модели GPT
async def gpt_model_menu(message: types.Message):
    user_exists = db.check_user(message.from_user.id)
    if user_exists:
        state = dp.get_current().current_state(chat=message.chat.id, user=message.chat.id)
        # state = dp.get_current().current_state()
        try:
            data = await state.get_data()
            gpt_model = data['gpt_model']
        except KeyError:
            print('Не нашел настройки модели GPT')
            gpt_model = 3
        GPT_MODEL_BT = await bt.gpt_model(gpt_model)
        await bot.send_message(message.chat.id, text='Выбирай модель из списка ниже:', reply_markup=GPT_MODEL_BT)
    else:
        await bot.send_message(message.chat.id, text='Извини, доступ запрещен\nЕсли хотите пользоваться ботом, нажмите /start')

# Выбор модели GPT
async def gpt_model_setting(message: types.CallbackQuery):
    gpt_model = int(message.data.split('_')[-1])
    print(f'Установили модель {gpt_model}')
    state = dp.get_current().current_state(chat=message.message.chat.id, user=message.message.chat.id)
    # state = dp.get_current().current_state()
    await state.update_data(gpt_model = gpt_model)
    GPT_MODEL_BT = await bt.gpt_model(gpt_model)
    await message.message.edit_text(text='Выбирай модель из списка ниже:', reply_markup=GPT_MODEL_BT)

# Обработка команды /flush - сброс контекста и любого стейта FSM
async def flush_cache(message: types.Message):
    state = dp.get_current().current_state(chat=message.chat.id, user=message.chat.id)
    # state = dp.get_current().current_state()
    contexts: dict = {}
    await state.update_data(contexts = contexts)
    await message.reply('Очистил контекст! Начнем заново?')

