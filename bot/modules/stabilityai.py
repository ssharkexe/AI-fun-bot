import json, aiohttp, base64, aiofiles
from aiofiles import os as aios

engine_id = "stable-diffusion-512-v2-1"

styles = {
    '3d-model': '3d-model',
    'analog-film': 'analog-film',
    'anime': 'anime',
    'cinematic': 'cinematic',
    'comic-book': 'comic-book',
    'digital-art': 'digital-art',
    'enhance': 'enhance',
    'fantasy-art': 'fantasy-art',
    'isometric': 'isometric',
    'line-art': 'line-art',
    'low-poly': 'low-poly',
    'modeling-compound': 'modeling-compound',
    'neon-punk': 'neon-punk',
    'origami': 'origami',
    'photographic': 'photographic',
    'pixel-art': 'pixel-art',
    'tile-texture': 'tile-texture'
}

api_host = 'https://api.stability.ai'

def credits_monitor(func):
    def wrapper(*args, **kwargs):
        initial_balance = get_balance()
        func(*args, **kwargs)
        new_balance = get_balance()
        spent = round(initial_balance - new_balance, 3)
        print(f'Баланс кредитов: {new_balance}. Потрачено {spent}')
    return wrapper

async def get_balance(api_key: str) -> tuple:
    balance_url = f"{api_host}/v1/user/balance"
    headers={"Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession() as session:
        session.headers.update(headers)
        balance_responce = await session.get(balance_url)
        if balance_responce.status != 200:
            return False, None
        data = await balance_responce.read()
        balance = round(json.loads(data)['credits'], 2)
    return True, balance

# @credits_monitor
async def text2image(prompt: str, api_key: str, telegram_id: int, style_preset: str = 'photographic') -> tuple:
    # await aios.makedirs('img', exist_ok=True)
    if api_key is None:
        raise Exception("Missing Stability API key.")
    params ={
            "text_prompts": [
                {
                    "text": f'{prompt}'
                }
            ],
            "cfg_scale": 7,
            "clip_guidance_preset": "NONE",
            "height": 512,
            "width": 512,
            "style_preset": f'{style_preset}',
            "samples": 1,
            "steps": 50,
        }
    headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f'Bearer {api_key}'
        }
    url = f"{api_host}/v1/generation/{engine_id}/text-to-image"
    async with aiohttp.ClientSession() as p:
        p.headers.update(headers)
        response = await p.post(url, json=params)
        if response.status != 200:
            data = await response.read()
            return False, json.loads(data)['message']
        else:
            data = await response.read()
            for i, image in enumerate(json.loads(data)["artifacts"]):
                f = await aiofiles.open(f"img/2img_{telegram_id}.png", "wb")
                await f.write(base64.b64decode(image["base64"]))
                await f.close()
                print('Готово!')
            return True, ''
            
async def img2img(prompt: str, api_key: str, telegram_id: int, style_preset: str = 'photographic') -> tuple:
    await aios.makedirs('img', exist_ok=True)
    if api_key is None:
        raise Exception("Missing Stability API key.")
    headers={
            # "Content-Type": "multipart/form-data",
            "Authorization": f'Bearer {api_key}'
        }
    url = f"{api_host}/v1/generation/{engine_id}/image-to-image"
    params = {
            "image_strength": 0.35,
            "init_image_mode": "IMAGE_STRENGTH",
            # 'init_image': f'{image}',
            "text_prompts[0][text]": f'{prompt}',
            "text_prompts[0][weight]": 1,
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "samples": 1,
            "steps": 50,
            "style_preset": f'{style_preset}'
        }
    
    form_data = aiohttp.FormData()
    form_data.add_field("image_strength", '0.5')
    form_data.add_field("init_image_mode", "IMAGE_STRENGTH")
    form_data.add_field("text_prompts[0][text]", f'{prompt}')
    form_data.add_field("text_prompts[0][weight]", '1')
    form_data.add_field("cfg_scale", '7')
    form_data.add_field("clip_guidance_preset", "FAST_BLUE")
    form_data.add_field("samples", '1')
    form_data.add_field("steps", '50')
    form_data.add_field("style_preset", f'{style_preset}')
# !!!!!!!!!!!!! проверить этот код с открытием файла
    form_data.add_field('init_image',
            await aiofiles.open(f"img/init_{telegram_id}_image.png", "rb"),
            content_type='multipart/form-data'
            )
    # print(form_data())
    async with aiohttp.ClientSession() as session:
        session.headers.update(headers)
        response = await session.post(url, data=form_data)
        if response.status != 200:
            data = await response.read()
            return False, json.loads(data)['message']
        else:
            data = await response.read()
            for i, image in enumerate(json.loads(data)["artifacts"]):
                f = await aiofiles.open(f"img/2img_{telegram_id}.png", "wb")
                await f.write(base64.b64decode(image["base64"]))
                await f.close()
                print('Готово!')
            return True, ''
