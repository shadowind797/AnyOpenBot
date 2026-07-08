import logging
import os
from functools import partial

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, PUBLIC_URL
from handlers import router

logging.basicConfig(level=logging.INFO)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{PUBLIC_URL.rstrip('/')}{WEBHOOK_PATH}"


async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


async def health_check(request):
    return web.Response(text="OK")


def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    app.router.add_get("/", health_check)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", "8000"))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
