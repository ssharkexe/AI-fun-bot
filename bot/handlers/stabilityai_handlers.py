import io, aiofiles
from modules import stabilityai as sd, buttons as bt, dbdata as db
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound
from PIL import Image

from main import dp, bot

class StableDiffAPI(StatesGroup):
    api_set: StatesGroup = State()

class StableDiffPrompt(StatesGroup):
    prompt: StatesGroup = State()

start_text = '🌠 Генерация изображений через нейросеть Stable Diffusion. Доступна как генерация по запросу, так и модификация вашего изображения'

# Обработка команды /stablediffusion
async def stable_diffusion(message: types.Message):
    # await message.reply("Экспериментальная функция: нейросеть Stable Diffusion")
    # print(message)
    user_exists, api_key, credits = db.get_sd_params(message.from_user.id)
    if user_exists is True:
        if api_key is None:
            await bot.send_message(message.from_user.id, text=f'⛔️ Отсутствует API ключ Stable Diffusion\n➡️ Напиши мне свой API ключ в ответном сообщении')
            await bot.send_message(message.from_user.id, text='https://telegra.ph/Kak-poluchit-API-klyuch-k-Stable-Diffusion-05-16')
            await StableDiffAPI.api_set.set()
        else:
            api_is_ok, credits = await sd.get_balance(api_key)
            if credits == None:
                credits = 0
            if credits >= 0.8:
                SD_SETTINGS_BT = await bt.sd_settings(0)
                msg = await bot.send_message(message.from_user.id, text=f'{start_text}\n\nБаланс: {credits} кредитов\n\n🔹 Выбери стиль изображения в настройках', reply_markup=SD_SETTINGS_BT)
                await StableDiffPrompt.prompt.set()
                state = dp.get_current().current_state()
                async with state.proxy() as data:
                    data['api_key'] = api_key
                    data['credits'] = credits
                    data['style_preset'] = 'photographic'
                    data['settings_msg'] = msg
                    data['img2img'] = False
            else:
                await update_sd_api_key(message.from_user.id)
    else:
        await bot.send_message(message.from_user.id, text=f'Вы не зарегистрированы! Нажмите /start')

# Настройка стиля изображения Stable Diffusion
async def sd_style_settings(message: types.CallbackQuery):
    await message.message.delete()
    state = dp.get_current().current_state()
    SD_SETTINGS_BT = await bt.sd_settings(1)
    await bot.send_message(message.from_user.id, text=f'Стиль генерируемого изображения:', reply_markup=SD_SETTINGS_BT)

# Сохранение в машину состояний настройки стиля изображения Stable Diffusion
async def sd_style_settings_apply(message: types.CallbackQuery):
    await message.message.delete()
    style_preset = message.data.split('_')[-1]
    state = dp.get_current().current_state()
    data = await state.get_data()
    credits = data['credits']
    SD_SETTINGS_BT = await bt.sd_settings(0)
    msg = await bot.send_message(message.from_user.id, text=f'Баланс: {credits} кредитов\n\n🔹 {style_preset}', reply_markup=SD_SETTINGS_BT)
    # await bot.send_message(message.from_user.id, text=f'Экспериментальная функция: image 2 image\nОтправляйте боту картинку, затем пишите текстовый запрос для модификации изображения')
    async with state.proxy() as data:
        data['style_preset'] = style_preset
        data['settings_msg'] = msg
        
# Сохранение API ключа Stable Diffusion в базу
async def save_sd_api_key(message: types.Message, state: FSMContext):
    api_key = message.text
    telegram_id = message.from_user.id
    api_is_ok, credits = await sd.get_balance(api_key)
    if api_is_ok is True:
        if credits is not None:
            api_key_exists = db.save_sd_api_key(telegram_id, api_key, credits)
            if api_key_exists is True:
                await bot.send_message(message.from_user.id, text=f'Такой ключ уже сохранен, введите другой')
            else:
                SD_SETTINGS_BT = await bt.sd_settings(0)
                msg = await bot.send_message(message.from_user.id, text=f'Ключ сохранен, можешь пользоваться! Пиши запрос на английском или присылай фотку (лучше квадратную)', reply_markup=SD_SETTINGS_BT)
                await state.finish()
                await StableDiffPrompt.prompt.set()
                state = dp.get_current().current_state()
                async with state.proxy() as data:
                    data['api_key'] = api_key
                    data['credits'] = credits
                    data['img2img'] = False
                    data['style_preset'] = 'photographic'
                    data['settings_msg'] = msg
    else:
        await bot.send_message(message.from_user.id, text=f'Ключ неверный, попробуй еще раз', reply_markup = await bt.exit_button())

# Остаток кредитов исчерпан, необходимо обновить API ключ
async def update_sd_api_key(telegram_id):
    await bot.send_message(telegram_id, text=f'🟠 Баланс кредитов исчерпан\n➡️ Напиши мне новый API ключ в ответном сообщении')
    await bot.send_message(telegram_id, text='https://telegra.ph/Kak-poluchit-API-klyuch-k-Stable-Diffusion-05-16')
    state = dp.get_current().current_state()
    await state.finish()
    await StableDiffAPI.api_set.set()

# Запрос к Stable Diffusion
async def text2img_prompt(message: types.Message, state: FSMContext):
    prompt = message.text
    telegram_id = message.from_user.id
    data = await state.get_data()
    api_key = data['api_key']
    style_preset = data['style_preset']
    old_credits = data['credits']
    settings_msg = data['settings_msg']
    img2img = data['img2img']
    try:
        await settings_msg.delete()
    except MessageToDeleteNotFound:
        pass
    if old_credits >= 0.8:
        if img2img == True:
            response_ok, text = await sd.img2img(prompt, api_key, telegram_id, style_preset)
        else:
            response_ok, text = await sd.text2image(prompt, api_key, telegram_id, style_preset)
        if response_ok is True:
            # msg = data['msg']
            # await msg.delete()
            media = types.MediaGroup()
            media.attach_photo(types.InputFile(f'img/2img_{telegram_id}.png'))
            api_is_ok, credits = await sd.get_balance(api_key)
            async with state.proxy() as data:
                data['credits'] = credits
            spent_credits = round(old_credits - credits, 2)
            db.save_sd_credits(telegram_id, credits)
            await bot.send_media_group(message.from_user.id, media=media)
            msg = await bot.send_message(message.from_user.id, text=f'✅ На запрос потрачено {spent_credits} кредитов. Пробуем еще?', reply_markup = await bt.sd_settings(0))
            async with state.proxy() as data:
                data['settings_msg'] = msg
        else:
            await bot.send_message(message.from_user.id, text=f'❌ Ошибка: {text}')
    else:
        await update_sd_api_key(telegram_id)

# Обработка фотки, сохранение в PNG
async def sd_img2img(message: types.Message):
    telegram_id = message.from_user.id
    image = io.BytesIO()
    await message.photo[-1].download(destination_file=image)
    img = Image.open(image)
    w, h = img.size
    # print(f'Исходное изображение: ширина - {w}, высота - {h}')
    if w > h:
        cr = int(round((w - h) / 2, 0))
        img = img.crop((cr, 0, w-cr, h))
    elif w < h:
        cr = int(round((h - w) / 2, 0))
        img = img.crop((0, cr, w, h-cr))
    # w, h = img.size
    # print(f'После ресайза ширина - {w}, высота - {h}')
    img = img.resize((512, 512), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="png")
    async with aiofiles.open(f'img/init_{telegram_id}_image.png', 'wb') as file:
        await file.write(output.getvalue())
    msg = await bot.send_message(message.from_user.id, text=f'➡️ Картинку получил, теперь можешь написать текстовый запрос (на английском) для ее модификации', reply_markup = await bt.sd_settings(0))
    state = dp.get_current().current_state()
    async with state.proxy() as data:
        data['img2img'] = True
        data['msg'] = msg