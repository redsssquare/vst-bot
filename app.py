"""Точка входа: aiohttp-приложение с webhook для aiogram 3.x."""

from pathlib import Path

from dotenv import load_dotenv

# Явный путь к .env (важно для systemd, где cwd может отличаться)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import Update

import config


class MessageLogMiddleware:
    async def __call__(self, handler, event, data):
        if event.message:
            print("CHAT_ID:", event.message.chat.id)
            print("USER_ID:", event.message.from_user.id if event.message.from_user else None)
        return await handler(event, data)
from handlers import crm_router, inbox_router, registration_router, start_router

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
dp.update.middleware(MessageLogMiddleware())
dp.include_router(start_router)
dp.include_router(crm_router)
dp.include_router(registration_router)
dp.include_router(inbox_router)


async def on_startup(_: web.Application) -> None:
    await bot.set_webhook(config.WEBHOOK_URL)


async def on_shutdown(_: web.Application) -> None:
    await bot.delete_webhook()
    await bot.session.close()


async def handle_webhook(request: web.Request) -> web.Response:
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response()


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post(config.WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="127.0.0.1", port=8000)
