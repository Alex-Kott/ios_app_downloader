import asyncio
import json
import logging
import os
import plistlib

from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiohttp import ClientSession
from furl import furl

from config import BOT_TOKEN

# bot = Bot(token=BOT_TOKEN, proxy="socks5://163.172.152.192:1080")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.reply('Для начала работы пришлите боту ссылку вида https://appscloud.me/free_apps/app.php?id=<application_id>')


async def get_plist_file(app_id: int) -> str:
    logger.info("Script started")
    async with ClientSession() as session:
        async with session.get(f"https://appscloud.me/free_apps/install.php?id={app_id}",
                               headers={'action': 'download-manifest'}) as response:

            return await response.text()


async def load_ipa_file(ipa_link: str) -> str:
    link = furl(ipa_link)
    file_name = link.path.segments[-1]

    async with ClientSession() as session:
        async with session.get(ipa_link) as response:
            with open(file_name, 'wb') as file:
                file.write(await response.read())

                return file_name


@dp.message_handler(content_types=['text'])
async def text_handler(message: Message):
    link = furl(message.text)
    if link.host is None:
        await message.reply(f'Не похоже, что это ссылка. '
                            f'Для работы боту нужна ссылка вида https://appscloud.me/free_apps/app.php?id=<application_id>')
    elif link.host != 'appscloud.me':
        await message.reply('Бот не работает с этим сайтом')
    else:
        await message.reply('Начинаю загрузку...')
        plist_file_content = await get_plist_file(link.args['id'])
        plist_file_name = 'application.plist'
        with open(plist_file_name, 'w', encoding='utf-8') as file:
            file.write(plist_file_content)

        with open(plist_file_name, 'rb') as file:
            data = plistlib.load(file)
            ipa_link = data['items'][0]['assets'][0]['url']

        ipa_file_name = await load_ipa_file(ipa_link)

        # with open(plist_file_name, 'rb') as file:
        #     try:
        #         await message.reply_document(file)
        #     except:
        #         print(plist_file_name)

        with open(ipa_file_name, 'rb') as file:
            # await message.reply_document(file)
            await message.reply_document(file)

        # os.remove(plist_file_name)
        # os.remove(ipa_file_name)

        # print(plist_file_content)
        # plistlib.loads(plist_file_content)
    # print(link.__dict__)



if __name__ == "__main__":
    logger = logging.getLogger('logger')
    logger.setLevel('INFO')
    # event_loop = asyncio.get_event_loop()
    # event_loop.run_until_complete(main())
    # event_loop.close()
    executor.start_polling(dp)
