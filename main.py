import asyncio
import json
import logging
import os
import plistlib
from hurry.filesize import size

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


async def load_ipa_file(ipa_link: str, message=None) -> str:
    link = furl(ipa_link)
    file_name = link.path.segments[-1]

    async with ClientSession() as session:
        async with session.get(ipa_link) as response:
            filesize = response.headers['Content-Length']

            if message:
                await message.reply(f'Начата загрузка .ipa-файла на сервер ({filesize})')

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
        await message.reply('Получаем .plist-файл...')

        plist_file_content = await get_plist_file(link.args['id'])
        plist_file_name = 'application.plist'
        with open(plist_file_name, 'w', encoding='utf-8') as file:
            file.write(plist_file_content)

        await message.reply('.plist-файл загружен, начинаем передачу')

        with open(plist_file_name, 'rb') as file:
            data = plistlib.load(file)
            ipa_link = data['items'][0]['assets'][0]['url']

        with open(plist_file_name, 'rb') as file:
            await message.reply_document(file)
        os.remove(plist_file_name)

        try:
            await message.reply(f'Ссылка на .ipa-файл: \n\n {ipa_link}')

            await message.reply('Начинаем загрузку .ipa-файла на сервер')
            ipa_file_name = await load_ipa_file(ipa_link)
            try:
                with open(ipa_file_name, 'rb') as file:
                    await message.reply_document(file)
            except Exception:
                await message.reply('Не удалось отправить загруженный .ipa-файл через Telegram')
            os.remove(ipa_file_name)

        except Exception as e:
            await message.reply(f'Что-то пошло не так \n\n {e}')


if __name__ == "__main__":
    logger = logging.getLogger('logger')
    logger.setLevel('INFO')
    executor.start_polling(dp)
