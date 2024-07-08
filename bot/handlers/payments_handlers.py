import os
from aiogram import types
from modules import dbdata as db

from main import dp, bot

PAYMENTS_TOKEN = os.environ.get('PAYMENTS_TOKEN') 
PRICE = types.LabeledPrice(label="Пополнить баланс на 50 р.", amount=50*100)  # в копейках (руб)

# buy
async def buy(message: types.Message):
    if PAYMENTS_TOKEN.split(':')[1] == 'TEST':
        await bot.send_message(message.from_user.id, "Тестовый платеж")
    await bot.send_invoice(message.from_user.id,
                           title=" Пополнение баланса",
                           description="Добавление 50 р. на счет",
                           provider_token=PAYMENTS_TOKEN,
                           currency="rub",
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter="balance-top-up",
                           payload="test-invoice-payload")

# pre checkout  (must be answered in 10 seconds)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# successful payment
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    for k, v in payment_info.items():
        print(f"{k} = {v}")
    amount = payment_info['total_amount'] / 100 / 90
    db.gpt_balance_top_up(message.from_user.id, amount)
    await bot.send_message(message.from_user.id,
                           f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно")

