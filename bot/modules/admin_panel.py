from modules import buttons as bt
import math
from modules import dbdata as db

# Обработка команды /settings
async def manage_users(users: list, page: int) -> tuple:
    users_count = len(users)
    max_users_length = 5
    pages = math.ceil(users_count / max_users_length)
    start_point = page * max_users_length - max_users_length
    end_point = page * max_users_length
    print(f'старт - {start_point}, окончание - {end_point}')
    MNG_BUTTONS = await bt.manage_users_buttons(users_count, page, pages)
    start_text = f'Перечень сохраненных пользователей (страница {page} из {pages}):'
    for i in users[start_point:end_point]:
        start_text = start_text + f'\n🔹 Telegram ID: {i["id"]} \nИмя: {str(i["first_name"])} \nБаланс StableDiff: {str(round(float(i["credits"] or 0), 4))} \nПотрачено GPT3: $ {str(round(float(i["price_3"] or 0), 4))} \nПотрачено GPT4: $ {str(round(float(i["price_4"] or 0), 4))} \nПотрачено Всего: $ {str(round(float(i["total_price"] or 0), 4))} \nДоступный баланс: $ {str(round(float(i["gpt_chat_credits"] or 0), 4))}'
    per_page_users = []
    for i in users[start_point:end_point]:
        per_page_users.append(i['id'])
    return start_text, MNG_BUTTONS, per_page_users

async def get_current_user_details(telegram_id: int) -> str:
    user = db.get_current_user(telegram_id)
    start_text = f'Ваши данные:'
    for i in user:
        start_text = start_text + f'\n🔹 Telegram ID: {i["id"]} \nИмя: {str(i["first_name"])} \nБаланс StableDiff: {str(round(float(i["credits"] or 0), 4))} \nПотрачено GPT3: $ {str(round(float(i["price_3"] or 0), 4))} \nПотрачено GPT4: $ {str(round(float(i["price_4"] or 0), 4))} \nПотрачено Всего: $ {str(round(float(i["total_price"] or 0), 4))} \nДоступный баланс: $ {str(round(float(i["gpt_chat_credits"] or 0), 4))}'
    return start_text