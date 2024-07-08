from modules.stabilityai import styles
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from modules.chatgpt import roles, gpt_models

exit = InlineKeyboardButton('Выход', callback_data='exit')

async def page_switcher(page: int, total: int = 15) -> dict:
    new_search = InlineKeyboardButton(text = 'Новый поиск', callback_data='new_search')
    p_num = page - 1
    n_num = page + 1
    previous_page = InlineKeyboardButton(text = '< Пред.', callback_data=f'switch_page_pic_{p_num}')
    next_page = InlineKeyboardButton(text = 'След. >', callback_data=f'switch_page_pic_{n_num}')
    if page > 1:
        PAGE_BUTTONS = InlineKeyboardMarkup(row_width=3)
        PAGE_BUTTONS.add(previous_page, exit, next_page)
        return PAGE_BUTTONS
    else:
        if total > 10:
            PAGE_BUTTONS = InlineKeyboardMarkup(row_width=2) 
            PAGE_BUTTONS.add(exit, next_page)
            return PAGE_BUTTONS
        else:
            PAGE_BUTTONS = InlineKeyboardMarkup(row_width=2)
            PAGE_BUTTONS.add(exit, new_search)
            return PAGE_BUTTONS
        
async def exit_button() -> dict:
    EXIT_BUTTON = InlineKeyboardMarkup(row_width=1)
    EXIT_BUTTON.add(exit)
    print(EXIT_BUTTON)
    return EXIT_BUTTON
        
async def new_user_buttons(id: int):
    deny_btn = InlineKeyboardButton(text = '❌ Отклонить', callback_data=f'deny_{id}')
    approve_btn = InlineKeyboardButton(text = '✅ Добавить', callback_data=f'approve_{id}')
    NEW_USER_BUTTONS = InlineKeyboardMarkup(row_width=2)
    NEW_USER_BUTTONS.add(deny_btn, approve_btn)
    print(NEW_USER_BUTTONS)
    return NEW_USER_BUTTONS

async def sd_settings(param: int) -> dict: #Если в параметре приходит 1 - то показываем весь список кнопок, если 0 - то только 1 кнопку настроек
    sd_settings = InlineKeyboardButton(text = 'Настройки', callback_data='sd_style_settings')
    if param == 0:
        SD_SETTINGS_BT = InlineKeyboardMarkup(row_width=2)
        SD_SETTINGS_BT.add(sd_settings, exit)
        return SD_SETTINGS_BT
    else:
        SD_SETTINGS_BT = InlineKeyboardMarkup(row_width=3)
        buttons_list = [InlineKeyboardButton(text = key, callback_data='sdstyle_' + str(value)) for key, value in styles.items()] # словарь стилей импортим из stabilityai.py
        SD_SETTINGS_BT.add(*buttons_list)
        return SD_SETTINGS_BT
    
async def manage_users_buttons(total_users: int, page: int, end: int) -> dict:
    p_num = page - 1
    n_num = page + 1
    previous_page = InlineKeyboardButton(text = f'< Пред. ({p_num})', callback_data=f'switch_page_adm_{p_num}')
    next_page = InlineKeyboardButton(text = f'({n_num}) След. >', callback_data=f'switch_page_adm_{n_num}')
    remove = InlineKeyboardButton(text = 'Управление', callback_data='remove_user')
    if page == 1:
        if total_users <= 5:
            MNG_BUTTONS = InlineKeyboardMarkup(row_width=2)
            MNG_BUTTONS.add(remove, exit)
            return MNG_BUTTONS
        else:
            MNG_BUTTONS = InlineKeyboardMarkup(row_width=2)
            MNG_BUTTONS.add(remove, next_page, exit)
            return MNG_BUTTONS
    elif page > 1 and page != end:
        MNG_BUTTONS = InlineKeyboardMarkup(row_width=3)
        MNG_BUTTONS.add(previous_page, remove, next_page, exit)
        return MNG_BUTTONS
    elif page == end:
        MNG_BUTTONS = InlineKeyboardMarkup(row_width=2)
        MNG_BUTTONS.add(previous_page, remove, exit)
        return MNG_BUTTONS
    else:
        print('Не удалось сформировать список кнопок')
        return {}

async def remove_users_buttons(per_page_users: list) -> dict:
    buttons_list = [InlineKeyboardButton(text = i, callback_data=f'remove_user_{i}') for i in per_page_users]
    RMV_BUTTONS = InlineKeyboardMarkup(row_width=3)
    RMV_BUTTONS.add(*buttons_list, exit)
    return RMV_BUTTONS

async def chatgpt_roles() -> dict:
    buttons_list = [InlineKeyboardButton(text = i, callback_data=f'gpt_system_role_{list(roles).index(i)}') for i in roles.keys()]
    GPT_BUTTONS = InlineKeyboardMarkup(row_width=2)
    GPT_BUTTONS.add(*buttons_list, exit)
    return GPT_BUTTONS

async def gpt_model(model: int = 3) -> dict:
    ok_text = '✅'
    models = gpt_models.copy()
    if model == 3:
        models[3] = f'{ok_text} {gpt_models[3]}'
    else:
        models[4] = f'{ok_text} {gpt_models[4]}'
    GPT_MODEL_BT = InlineKeyboardMarkup(row_width=2)
    buttons_list = [InlineKeyboardButton(text = value, callback_data='gpt_model_' + str(key)) for key, value in models.items()] # словарь моделей из chatgpt.py
    GPT_MODEL_BT.add(*buttons_list, exit)
    return GPT_MODEL_BT