import os
from modules import dbdata as db
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import default_state
from aiogram.utils.executor import start_webhook

IS_WEBHOOK = os.environ.get('IS_WEBHOOK')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
NGINX_HOST = os.environ.get('NGINX_HOST') 

# webhook settings
WEBHOOK_HOST = f'https://{NGINX_HOST}'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0' 
WEBAPP_PORT = 3001

# Инициализация Telegram Bot
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# функции для webhook stratup и shutdown
async def on_startup(dp) -> None:
    await bot.set_webhook(WEBHOOK_URL)
    print(f'Передали серверам Telegram что слушаем {WEBHOOK_URL}. Бот запущен!')
    enabled_chats, admin = db.get_all_users()
    await bot.send_message(admin, text=f'Бот запущен!')

async def on_shutdown(dp) -> None:
    await bot.delete_webhook()

# Запуск бота
if __name__ == '__main__':
    from handlers import handlers as hl, pexels_handlers as px, stabilityai_handlers as sd, chatgpt_handlers as hgpt, payments_handlers as pay
    dp.register_message_handler(pay.buy, commands=['buy'], state='*')
    dp.register_pre_checkout_query_handler(pay.pre_checkout_query, lambda query: True)
    dp.register_message_handler(pay.successful_payment, content_types=types.ContentType.SUCCESSFUL_PAYMENT)
    dp.register_message_handler(px.send_pictures, commands=['picsearch'], state='*')
    dp.register_message_handler(hgpt.flush_cache, commands=['flush'], state='*')
    dp.register_message_handler(hl.start_command_handler, commands=['start'], state='*')
    dp.register_message_handler(hl.help_command_handler, commands=['help'], state='*')
    dp.register_message_handler(hl.admin_panel, commands=['settings'], state='*')
    dp.register_message_handler(hgpt.assistant_role_menu, commands=['gpt_role_settings'], state='*')
    dp.register_message_handler(hgpt.gpt_model_menu, commands=['gpt_model_settings'], state='*')
    dp.register_callback_query_handler(hgpt.assistant_role_change, text_contains='gpt_system_role_', state='*')
    dp.register_callback_query_handler(hgpt.gpt_model_setting, text_contains='gpt_model_', state='*')
    dp.register_message_handler(sd.stable_diffusion, commands=['stablediffusion'], state='*')
    dp.register_message_handler(sd.sd_img2img, content_types=types.ContentTypes.PHOTO, state=sd.StableDiffPrompt.prompt)
    dp.register_callback_query_handler(sd.sd_style_settings, text='sd_style_settings', state='*')
    dp.register_callback_query_handler(sd.sd_style_settings_apply, text_contains='sdstyle_', state='*')
    dp.register_message_handler(hl.get_new_user_contact, content_types=types.ContentTypes.CONTACT, state=hl.UserControl.new_user)
    dp.register_message_handler(sd.save_sd_api_key, state=sd.StableDiffAPI.api_set)
    dp.register_message_handler(px.send_pictures_promt, state=px.PictureSearch.search_promt)
    dp.register_message_handler(sd.text2img_prompt, state=sd.StableDiffPrompt.prompt)
    dp.register_callback_query_handler(px.page_switcher, text_contains='switch_page_pic', state='*')
    dp.register_callback_query_handler(hl.page_switcher_adm, text_contains='switch_page_adm', state=hl.AdminPanel.per_page)
    dp.register_callback_query_handler(hl.remove_user_menu, text='remove_user', state=hl.AdminPanel.per_page)
    dp.register_callback_query_handler(hl.remove_user_from_db, text_contains='remove_user_', state=hl.AdminPanel.remove_user)
    dp.register_callback_query_handler(hl.register_user, text_contains='approve_', state='*')
    dp.register_callback_query_handler(hl.deny_user, text_contains='deny_', state='*')
    dp.register_callback_query_handler(hl.exit_fsm, text='exit', state='*')
    dp.register_callback_query_handler(px.new_pic_search, text='new_search', state='*')
    dp.register_message_handler(hgpt.handle_message, content_types=['text'], state='*')
    if IS_WEBHOOK == 'True':
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,)
    else:
        executor.start_polling(dp, skip_updates=True)