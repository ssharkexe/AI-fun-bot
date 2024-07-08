import os, json, aiohttp, asyncio
from aiohttp import ClientSession
from modules import buttons as bt
from aiofiles import os as aios
from aiofiles import open
from aiogram.types import MediaGroup, InputFile

PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY')
proxy_host = os.environ.get("PROXY_HOST")
proxy_port = os.environ.get("PROXY_PORT")
proxy_user = os.environ.get("PROXY_USER")
proxy_pass = os.environ.get("PROXY_PASS")
proxy = ''
if '' not in [proxy_host, proxy_port, proxy_user, proxy_pass]:
    proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"


# Основная функция, которая ищет картинки и размещает их вместе с кнопками в сообщении
async def main_pex_func(query: str, page: int, telegram_id: int) -> tuple:
    # tasks = []
    main_task = asyncio.create_task(get_img_url_list(query, 'portrait', telegram_id, page))
    task = await asyncio.gather(main_task)
    print(task[0])
    if task[0][1] == 'success':
        total_results = task[0][2]
        current_page = task[0][3]
        media = MediaGroup()
        [media.attach_photo(InputFile(f'{i}')) for i in task[0][0]]
        if total_results < 11:
            PAGE_BUTTONS = await bt.page_switcher(current_page, total_results)
            text=f'Найдено изображений: {total_results}'
            return media, text, PAGE_BUTTONS
        else:
            PAGE_BUTTONS = await bt.page_switcher(current_page, total_results)
            text=f'Найдено изображений: {total_results}\nСтраница: {current_page}\nПереключиться между страницами:'
            return media, text, PAGE_BUTTONS  
    else:
        text=task[0][0]
        media = 0
        BUTTONS = await bt.exit_button()
        return media, text, BUTTONS

async def get_img_url_list(query: str, img_type: str, telegram_id: int, page: int = 1) -> list:
    await aios.makedirs(f'img/pexels/{telegram_id}', exist_ok=True)
    headers = {'Authorization': f'{PEXELS_API_KEY}'}
    full_url = f'https://api.pexels.com/v1/search?query={query}&per_page=10&page={page}'
    async with aiohttp.ClientSession() as session:
        session.headers.update(headers)
        if proxy:
            get_request = await session.get(full_url, proxy=proxy)
        else:
            get_request = await session.get(full_url)
        if get_request.status == 522:
            await session.close()
            return ['Ошибка доступа к API. Возможно, геоограничения. Необходимо добавить proxy', 'error', 0, 1]
        data = await get_request.read()
        photo_data = json.loads(data)
        if photo_data['total_results'] == 0:
            return ['Изображения не нейдены, попробуйте изменить запрос', 'error', 0, 1]
        else:
            limits = [
                'X-Ratelimit-Limit',
                'X-Ratelimit-Remaining',
                'X-Ratelimit-Reset'
            ]
            print(f'Общий лимит запросов: {get_request.headers[limits[0]]}, оставшийся лимит {get_request.headers[limits[1]]}, reset {get_request.headers[limits[2]]}')
            if img_type == 'original':
                img_list = [i['src']['original'] for i in photo_data['photos']]
            elif img_type == 'portrait':
                img_list = [i['src']['portrait'] for i in photo_data['photos']]
            else:
                img_list = []
                print('Не удалось сформировать список картинок')
            total_results = photo_data['total_results']
            current_page = photo_data['page']
            pic_num = min([10, total_results])
            tasks = []
            for i in range(0, pic_num):
                task = asyncio.create_task(save_images(img_list[i], session, i, telegram_id)) #создаем корутину
                tasks.append(task) #добавляем корутину в стек
            fetched_img = await asyncio.gather(*tasks)
            # print(fetched_img)
            return [fetched_img, 'success', total_results, current_page]

async def save_images(img_url: str, session: ClientSession, num: int, telegram_id: int) -> str:
    response = await session.get(img_url, proxy=proxy)
    if response.status == 200:
        f = await open(f'img/pexels/{telegram_id}/{num}.jpeg', 'wb')
        await f.write(await response.read())
        await f.close()
        return f'img/pexels/{telegram_id}/{num}.jpeg'
    else:
        print('Image Couldn\'t be retrieved')
        return 'None'
