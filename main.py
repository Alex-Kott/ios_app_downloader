import asyncio
import logging

from aiohttp import ClientSession


async def main():
    logger.info("Script started")
    async with ClientSession() as session:
        async with session.get(f"https://appscloud.me/free_apps/install.php?id=32", headers={'action': 'download-manifest'}) as response:

            print(await response.text())


if __name__ == "__main__":
    logger = logging.getLogger('logger')
    logger.setLevel('INFO')
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(main())
    event_loop.close()
