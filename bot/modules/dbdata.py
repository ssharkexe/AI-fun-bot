from peewee import *
import datetime, os
from peewee import DoesNotExist, OperationalError, IntegrityError, DoesNotExist
from aiogram.types import Message

ADMIN_ID = os.environ.get('ADMIN_TELEGRAM_ID')
print(f'Проверяем ID админа: {ADMIN_ID}')

# Создаем соединение с нашей базой данных
db = SqliteDatabase(None)
db.init('db/db.sqlite')

# Определяем базовую модель о которой будут наследоваться остальные
class BaseModel(Model):
    class Meta:
        database = db

# Определяем модель таблицы с пользовтаелями
class User(BaseModel):
    id = CharField(unique = True, null = False, primary_key = True)
    username = CharField(unique = False, null = True)
    first_name = CharField(unique = False, null = True)
    second_name = CharField(unique = False, null = True)
    phone_number = CharField(null = True)
    chat = BooleanField(default = False)
    admin = BooleanField(default = False)
    sd_api_key = CharField(unique = False, null = True)
    credits = FloatField(null = True)
    gpt_chat_credits = FloatField(default = 0)
    updated_date = DateTimeField(default = datetime.datetime.now)

class GptUsageHistory(BaseModel):
    id = AutoField(primary_key = True)
    telegram_id = ForeignKeyField(User)
    gpt_model = IntegerField(unique = False, null = False)
    action_date = DateTimeField(default = datetime.datetime.now)
    spent_tokens = FloatField(null = True)
    price = FloatField(null = True)

# далее осуществляем миграцию текущих пользователей
db.connect()
# User.drop_table()
# db.create_tables([User], safe = True)
# User.get_or_create(id=ADMIN_TELEGRAM_ID, admin=True)
try:
    # GptUsageHistory.drop_table()
    db.create_tables([User], safe = True)
    db.create_tables([GptUsageHistory], safe = True)
    User.get_or_create(id=ADMIN_ID, admin=True)
except OperationalError:
    print(f'Упс! OperationalError!')
except IntegrityError:
    print(f'Упс! IntegrityError!')
    User.update({User.admin: True}).where(User.id == ADMIN_ID).execute()

# Получаем список пользователей и чатов, записанных в базу + админа
def get_all_users() -> tuple:
    return [user['id'] for user in User.select(User.id).dicts()], User.select(User.id).where(User.admin==1).scalar()

# Получаем список сохраненных пользователей
def get_saved_users() -> list:
    usage_3 = fn.SUM(Case(None, (
        (GptUsageHistory.gpt_model == 3, GptUsageHistory.price),
    ), None))
    usage_4 = fn.SUM(Case(None, (
        (GptUsageHistory.gpt_model == 4, GptUsageHistory.price),
    ), None))
    query = (User
         .select(User, fn.SUM(GptUsageHistory.price).alias('total_price'), usage_3.alias('price_3'), usage_4.alias('price_4'))
         .join(GptUsageHistory, JOIN.LEFT_OUTER, on=(User.id == GptUsageHistory.telegram_id))
         .group_by(User))
    return [user for user in query.dicts()]

# Получаем данные по конкретному пользователю
def get_current_user(telegram_id: int) -> list:
    usage_3 = fn.SUM(Case(None, (
        (GptUsageHistory.gpt_model == 3, GptUsageHistory.price),
    ), None))
    usage_4 = fn.SUM(Case(None, (
        (GptUsageHistory.gpt_model == 4, GptUsageHistory.price),
    ), None))
    query = (User
         .select(User, fn.SUM(GptUsageHistory.price).alias('total_price'), usage_3.alias('price_3'), usage_4.alias('price_4'))
         .join(GptUsageHistory, JOIN.LEFT_OUTER, on=(User.id == GptUsageHistory.telegram_id))
         .where(User.id == telegram_id))
    return [user for user in query.dicts()]

# Получаем текущего пользователя, его stable diffusion api key и количество кредитов
def get_sd_params(telegram_id: int) -> tuple:
    try:
        Userparams = User.get_by_id(telegram_id)
        return True, Userparams.sd_api_key, Userparams.credits
    except DoesNotExist:
        return False, 0, 0

# Добавляем пользователя в базу
def register_user(data: Message) -> None:
    if data.chat.type == 'group':
        User.replace(id = data.chat.id, first_name = data.chat.title, chat=1).execute()
        User(id=data.chat.id).save()
    elif data.chat.type == 'private':
        User.replace(id = data.contact.user_id, first_name = data.contact.first_name, chat=0, phone_number = data.contact.phone_number).execute()
        User(id=data.contact.user_id).save()
    else:
        pass

def save_sd_api_key(telegram_id: int, api_key: str, credits: float) -> bool:
    try:
        User.update({User.sd_api_key: api_key}).where(User.id == telegram_id).execute()
        User.update({User.credits: credits}).where(User.id == telegram_id).execute()
        return False
    except IntegrityError:
        return True

def save_sd_credits(telegram_id: int, credits: float) -> None:
    User.update({User.credits: credits}).where(User.id == telegram_id).execute()

def save_gpt_chat_credits(telegram_id: int, model: int, input_tokens: float = 0, output_tokens: float = 0) -> None:
    # нужно посчитать стоимость запроса:
    # gpt4 input $0,03 per 1000, output $0,06 per 1000
    # gpt3 input $0.0015 per 1000, output $0.002 per 1000
    if model == 4:
        price = input_tokens/1000 * 0.03 + output_tokens/1000 * 0.06
    else:
        price = input_tokens/1000 * 0.0015 + output_tokens/1000 * 0.002
    spent_tokens = input_tokens + output_tokens
    update_gpt_balance(telegram_id, price)
    GptUsageHistory.create(telegram_id=telegram_id, gpt_model=model, spent_tokens=spent_tokens, price=price)

def update_gpt_balance(telegram_id: int, price: float) -> None:
    User.update(gpt_chat_credits=User.gpt_chat_credits - price).where(User.id == telegram_id).execute()

# Удаляем пользователя из базы
def delete_user(user_id: int) -> None:
    User.delete().where(User.id==user_id).execute()
    print(user_id)

# Проверяем, есть ли пользователь в базе
def check_user(telegram_id: int):
    try:
        current_user = User.get(User.id==telegram_id)
        return current_user
    except DoesNotExist:
        return False
    
# Обновляем баланс GPT
def gpt_balance_top_up(telegram_id: int, amount: float):
    User.update(gpt_chat_credits=User.gpt_chat_credits + amount).where(User.id == telegram_id).execute()