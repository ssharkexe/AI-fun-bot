from modules import dbdata as db
import os
import openai, httpx
from openai import OpenAI, OpenAIError, APIConnectionError, BadRequestError, RateLimitError, PermissionDeniedError, AuthenticationError

proxy_host = os.environ.get("PROXY_HOST")
proxy_port = os.environ.get("PROXY_PORT")
proxy_user = os.environ.get("PROXY_USER")
proxy_pass = os.environ.get("PROXY_PASS")
proxy = ''
if '' not in [proxy_host, proxy_port, proxy_user, proxy_pass]:
    proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

if proxy:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), http_client=httpx.Client(proxies=proxy))
else:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), http_client=httpx.Client())

# Создание словаря для хранения контекста и словаря стилей собеседника
# contexts = {}

roles = {
    'Инопланетянин':{"role": "system", "content": "Отвечай как инопланетянин"},
    'Итальянец':{"role": "system", "content": "Периодически вставляй испанские слова будто ты иностранец"},
    'Гопник':{"role": "system", "content": "Отвечай как гопник"},
    'Трудный ребенок':{"role": "system", "content": "Отвечай как трудный ребенок"},
    'Программист':{"role": "system", "content": "Отвечай как программист"},
    'Обиженный полицейский':{"role": "system", "content": "Отвечай как обиженный полицейский"}
}

gpt_models = {
    3:'gpt-4o-mini',
    4:'gpt-4-turbo'
}

# Обработка входящих сообщений от пользователей    
async def handle_message(telegram_id: int, text: str, contexts: dict, model: int = 3):
    # Получение контекста для пользователя
    text = text.split('/')[-1]
    user_input = {"role": "user", "content": text}
    if telegram_id in contexts.keys():
        contexts[telegram_id].append(user_input)
    else:
        contexts[telegram_id] = [user_input]
    print(f'До запроса к нейросети:')
    print(contexts)
    print(f'используемая модель - {gpt_models[model]}')
    # Получение ответа от OpenAI API
    try:
        response = client.chat.completions.create(
            model=f'{gpt_models[model]}', 
            # max_tokens=4000,
            messages=contexts[telegram_id])
        # Сохранение контекста после получения ответа
        gpt_answer: str = response.choices[0].message.content
        gpt_answer_shrinked: str = response.choices[0].message.content
        if len(gpt_answer) > 400:
            gpt_answer_shrinked = response.choices[0].message.content[0:400]
        contexts[telegram_id].append({"role": "assistant", "content": gpt_answer_shrinked})
        print(f'После запроса к нейросети:')
        print(contexts[telegram_id])
        print(f'Запрос: {response.usage.prompt_tokens} т., ответ: {response.usage.completion_tokens} т.')
        db.save_gpt_chat_credits(telegram_id, model, response.usage.prompt_tokens, response.usage.completion_tokens)
        # Отправка ответа пользователю
        return contexts, gpt_answer
    except APIConnectionError:
        return contexts, 'Хьюстон, у нас проблемы со связью 👨🏻‍💻. Напиши еще раз'
    except PermissionDeniedError:
        return contexts, 'Ваш регион не поддерживается, необходимо добавить proxy'
    except RateLimitError:
        return contexts, 'ИИ перегружен, попробуй позже'
    except BadRequestError:
        contexts[telegram_id] = []
        return contexts, 'Контекст превышает 4000 токенов! Кэш контекста сброшен'
    except AuthenticationError:
        contexts[telegram_id] = []
        return contexts, 'Обновите токен OpenAI'
    
    
# Настройка стиля собеседника   
async def assistant_role_setting(telegram_id: int, gpt_role_index: int, contexts: dict):
    role_dict = list(roles.values())[gpt_role_index]
    role_name = list(roles.keys())[gpt_role_index]
    # contexts[telegram_id].append(role_dict)
    if telegram_id in contexts.keys():
        contexts[telegram_id].append(role_dict)
    else:
        contexts[telegram_id] = [role_dict]
    return contexts, f'Окей, настроил! {role_name}'
    
# Получаем из машины состояний настройку роли помощника и модели GPT
async def get_gpt_params():
    pass


